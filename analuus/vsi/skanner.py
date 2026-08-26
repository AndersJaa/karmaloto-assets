"""Coini skänner — VSI kolmanda teljega, nädalase hoiu jaoks.

VSI vastab küsimusele "mis toimub SELLE mündiga". Skänner vastab teisele
küsimusele: "millisesse minna". Need ei ole sama küsimus ja sellepärast on
siin kaks asja teisiti.

**Kolmas telg: suhteline tugevus.** Rotatsioon müntide vahel on suhtelise
tugevuse mäng. Münt, mille V on +60 sellepärast, et kogu turg tõuseb, ei ole
leid — ta on beeta. Münt, mille V on +40 sel ajal, kui BTC seisab, on. VSI-s on
BTC korrelatsioon ainult hoiatuslipp; siin on ta omaette telg.

**Nädalased parameetrid.** VSI vaikeväärtused (hinna_ref 3%, oi_ref 5%) on
4h/päevase akna peale. Nädalase hoiu juures annaks see igale mürale täisskoori.
Siin on aken 7 päeva ja refid vastavalt laiemad.

Pingerida EI ole soovitus. Ta ütleb, mida vaadata esimesena — lugemise teeb
ikka VSI, kolm telge eraldi, ja otsuse teeb inimene.

    python3 skanner.py --demo
    python3 skanner.py --test
"""

from __future__ import annotations

import math
import statistics
import sys
from dataclasses import dataclass, field

import vsi

# Nädalane aken: mis päevases graafikus on liikumine, on nädalases müra.
HINNA_REF = 0.12
OI_REF = 0.15

# Likviidsuse põrand. Alla selle ei tule münt nimekirja üldse — mitte madala
# skooriga, vaid üldse mitte. Suurus, mida ei saa mõistliku slippage'iga sisse
# ega välja, ei ole kauplemiskandidaat, ükskõik kui hea ta number on.
MIN_OI_USD = 50e6
MIN_MAHT_USD = 25e6


@dataclass
class Kandidaat:
    """Üks münt skännis. Kõik väljad tulevad päris kutsetest."""
    coin: str
    hinna_muutus: float      # 7 päeva, murruna
    oi_muutus: float
    neto_taker_usd: float
    maht_usd: float
    long_liq_usd: float
    short_liq_usd: float
    oi_usd: float
    funding_nyyd: float
    funding_ajalugu: list[float]
    long_short_ratio: float
    borsi_oi_osakaal: float
    basis_nyyd: float | None = None
    basis_ajalugu: list[float] | None = None


@dataclass
class Rida:
    coin: str
    voog: float
    surve: float
    suhteline: float          # z-skoor kandidaatide LÕIKES, mitte oma ajaloo vastu
    ylejaak: float            # coini tootlus miinus BTC tootlus
    oi_usd: float
    skoor: float
    lipud: list[str] = field(default_factory=list)

    def rida(self) -> str:
        lipud = ("  " + " · ".join(self.lipud)) if self.lipud else ""
        return (f"{self.coin:<8} V {self.voog:+6.1f}  S {self.surve:+6.1f}  "
                f"R {self.suhteline:+5.2f}  ülejääk {self.ylejaak:+6.1%}  "
                f"skoor {self.skoor:+6.1f}{lipud}")


def _telg_vsi(k: Kandidaat) -> tuple[float, float]:
    """V ja S sama loogikaga mis VSI, aga nädalaste refidega."""
    v = [
        vsi.oi_hinna_kvadrant(k.hinna_muutus, k.oi_muutus, HINNA_REF, OI_REF),
        vsi.taker_cvd(k.neto_taker_usd, k.maht_usd),
        vsi.likvideerimised(k.long_liq_usd, k.short_liq_usd, k.oi_usd),
    ]
    s = [
        vsi.funding_surve(k.funding_nyyd, k.funding_ajalugu),
        vsi.long_short_kalle(k.long_short_ratio, k.borsi_oi_osakaal),
    ]
    if k.basis_nyyd is not None and k.basis_ajalugu:
        s.append(vsi.basis_surve(k.basis_nyyd, k.basis_ajalugu))
    voog, _ = vsi._telg(v)
    surve, _ = vsi._telg(s)
    return voog, surve


def _ristloike_z(vaartused: list[float]) -> list[float]:
    """z-skoor kandidaatide lõikes, mediaani ja MAD-i baasil.

    Ristlõikes, mitte oma ajaloo vastu: küsimus ei ole "kas see münt on
    tugevam kui eelmisel nädalal", vaid "kas ta on tugevam kui teised praegu".
    """
    if len(vaartused) < 3:
        return [0.0] * len(vaartused)
    med = statistics.median(vaartused)
    mad = statistics.median([abs(x - med) for x in vaartused])
    if mad == 0:
        return [0.0] * len(vaartused)
    return [(x - med) / (1.4826 * mad) for x in vaartused]


def skanni(kandidaadid: list[Kandidaat], btc_tootlus: float,
           min_oi_usd: float = MIN_OI_USD,
           min_maht_usd: float = MIN_MAHT_USD) -> tuple[list[Rida], list[str]]:
    """Tagastab (pingerida, valja_jaanud_pohjendustega)."""
    valja = []
    sobivad = []
    for k in kandidaadid:
        if k.coin.strip().upper() in vsi.BTC_NIMED:
            # BTC ülejääk iseenda vastu on alati null — ta ei saa kunagi
            # pingereas tõusta ega langeda, ainult teisi lahjendada
            valja.append(f"{k.coin}: võrdlusalus, mitte kandidaat")
        elif k.oi_usd < min_oi_usd:
            valja.append(f"{k.coin}: OI {k.oi_usd/1e6:.0f}M alla {min_oi_usd/1e6:.0f}M põranda")
        elif k.maht_usd < min_maht_usd:
            valja.append(f"{k.coin}: maht {k.maht_usd/1e6:.0f}M alla {min_maht_usd/1e6:.0f}M põranda")
        else:
            sobivad.append(k)

    if not sobivad:
        return [], valja

    ylejaagid = [k.hinna_muutus - btc_tootlus for k in sobivad]
    z = _ristloike_z(ylejaagid)

    read = []
    for k, yle, zz in zip(sobivad, ylejaagid, z):
        voog, surve = _telg_vsi(k)
        lipud = []

        # Suhteline tugevus, mis tuleb BTC langusest, ei ole coini tugevus.
        # Ilma selleta hindaks skänner iga languses vähem langenud mündi leiuks.
        if yle > 0 and k.hinna_muutus <= 0:
            lipud.append("tugevus tuleb BTC nõrkusest, mitte coini tõusust")
        if abs(surve) > 60:
            lipud.append("rahvahulk juba ühel pool — hiline sisenemine")
        if k.borsi_oi_osakaal < 0.25:
            lipud.append(f"positsioneerimise andmed katavad vaid {k.borsi_oi_osakaal:.0%} OI-st")

        # Pingerida on vaatamise järjekord, mitte lugemine. Lugemine on kolm
        # telge eraldi — need on all real näha ja neid ei asendata skooriga.
        # Surve on karistus mõlemas suunas: vooga samas suunas ülerahvastatud
        # rahvahulk tähendab, et hea osa liikumisest on juba tehtud.
        karistus = 0.35 * abs(surve) if (voog > 0) == (surve > 0) else 0.0
        skoor = 0.6 * voog + 25 * zz - karistus

        read.append(Rida(k.coin, voog, surve, zz, yle, k.oi_usd, skoor, lipud))

    read.sort(key=lambda r: r.skoor, reverse=True)
    return read, valja


def render(read: list[Rida], valja: list[str], btc_tootlus: float) -> str:
    r = [
        "SKÄNN · nädalane aken",
        "=" * 78,
        f"  BTC samas aknas: {btc_tootlus:+.1%}",
        f"  R = suhteline tugevus BTC vastu, z-skoor kandidaatide lõikes",
        "",
    ]
    if not read:
        r.append("  Ükski münt ei läbinud likviidsuse põrandat.")
    for i, rida in enumerate(read, 1):
        r.append(f"{i:>3}.  {rida.rida()}")
    if valja:
        r += ["", "  Nimekirjast väljas:"]
        r += [f"    {x}" for x in valja]
    r += [
        "",
        "  See on VAATAMISE JÄRJEKORD, mitte soovitus. Iga rea kohta tuleb enne",
        "  otsust jooksutada täis-VSI koos invalideerimisega — skoor ei asenda lugemist.",
    ]
    return "\n".join(r)


# --------------------------------------------------------------------------

def _demo() -> None:
    fh = [0.0001, 0.00008, 0.00012, 0.00005, 0.00015, 0.0001,
          0.00009, 0.00011, 0.00013, 0.00007, 0.0001, 0.00012]
    k = [
        Kandidaat("AAA", 0.18, 0.22, 60e6, 900e6, 3e6, 14e6, 800e6, 0.00012, fh, 1.4, 0.55),
        Kandidaat("BBB", 0.04, -0.08, -20e6, 400e6, 18e6, 2e6, 300e6, 0.0005, fh, 3.1, 0.60),
        Kandidaat("CCC", -0.02, 0.11, 15e6, 250e6, 4e6, 5e6, 210e6, 0.00011, fh, 1.1, 0.48),
        Kandidaat("DDD", 0.25, 0.30, 90e6, 1200e6, 2e6, 30e6, 1000e6, 0.0009, fh, 4.2, 0.71),
        Kandidaat("EEE", 0.31, 0.40, 12e6, 18e6, 1e6, 2e6, 30e6, 0.0002, fh, 1.8, 0.30),
    ]
    read, valja = skanni(k, btc_tootlus=0.03)
    print(render(read, valja, 0.03))


def _test() -> None:
    ok = 0
    fh = [0.0001] * 6 + [0.00012, 0.00008, 0.00011, 0.00009]

    def teeb(coin, dh, doi, taker=30e6, oi=500e6, maht=300e6,
             ll=3e6, sl=6e6, funding=0.0001, ls=1.2, share=0.6):
        return Kandidaat(coin, dh, doi, taker, maht, ll, sl, oi, funding, fh, ls, share)

    # likviidsuse põrand viskab välja, ei anna lihtsalt madalat skoori
    read, valja = skanni([teeb("SMALL", 0.4, 0.5, oi=10e6), teeb("BIG", 0.1, 0.1)], 0.02)
    assert [r.coin for r in read] == ["BIG"], "väike OI peab nimekirjast välja jääma"
    assert any("SMALL" in x for x in valja), "väljajäämine peab olema põhjendatud"
    ok += 1

    # sama voog, eri suhteline tugevus -> tugevam ülejääk võidab
    read, _ = skanni([teeb("A", 0.20, 0.20), teeb("B", 0.05, 0.20), teeb("C", 0.02, 0.20)], 0.05)
    assert read[0].coin == "A", f"suurima ülejäägiga peab olema esimene, sai {read[0].coin}"
    ok += 1

    # tugevus BTC nõrkusest saab lipu
    read, _ = skanni([teeb("FLAT", -0.01, 0.10), teeb("X", -0.15, 0.10), teeb("Y", -0.20, 0.10)],
                     btc_tootlus=-0.18)
    flat = next(r for r in read if r.coin == "FLAT")
    assert flat.ylejaak > 0, "langevas turus on vähem langenu ülejääk positiivne"
    assert any("BTC nõrkusest" in f for f in flat.lipud), "see peab lipu saama"
    ok += 1

    # ülerahvastatud rahvahulk karistab, kui ta on vooga samas suunas
    puhas = teeb("PUHAS", 0.20, 0.20, funding=0.00005, ls=1.0)
    rahvas = teeb("RAHVAS", 0.20, 0.20, funding=0.002, ls=5.0)
    read, _ = skanni([puhas, rahvas, teeb("C", 0.0, 0.0)], 0.02)
    p = next(r for r in read if r.coin == "PUHAS")
    h = next(r for r in read if r.coin == "RAHVAS")
    assert h.surve > p.surve, "kõrge funding + ratio peab andma suurema surve"
    assert p.skoor > h.skoor, "sama voo juures peab väiksema survega münt ette jääma"
    assert any("hiline" in f for f in h.lipud)
    ok += 1

    # nädalased refid: päevane liikumine ei tohi anda täisskoori
    n = vsi.oi_hinna_kvadrant(0.04, 0.05, HINNA_REF, OI_REF)
    p = vsi.oi_hinna_kvadrant(0.04, 0.05)
    assert n.skoor < p.skoor * 0.6, "nädalases aknas peab 4% olema tagasihoidlik"
    ok += 1

    # ristlõike z on kandidaatide, mitte ajaloo suhtes
    z = _ristloike_z([0.01, 0.02, 0.03, 0.30])
    assert z[-1] > 2 and abs(z[1]) < 1, "väljapaistev peab eristuma, keskmine mitte"
    ok += 1

    # BTC ei osale kandidaadina
    read, valja = skanni([teeb("BTC", 0.10, 0.10), teeb("A", 0.20, 0.20),
                          teeb("B", 0.05, 0.05), teeb("C", 0.02, 0.02)], 0.10)
    assert "BTC" not in [r.coin for r in read], "BTC ei tohi pingereas olla"
    assert any("võrdlusalus" in x for x in valja), "ja väljajäämine peab olema põhjendatud"
    ok += 1

    # tühi ja liiga lühike nimekiri ei kuku kokku
    assert skanni([], 0.0) == ([], [])
    read, _ = skanni([teeb("ONE", 0.1, 0.1)], 0.02)
    assert len(read) == 1 and read[0].suhteline == 0.0, "alla 3 kandidaadi z = 0"
    ok += 1

    print(f"{ok}/8 testiplokki OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    else:
        _demo()
