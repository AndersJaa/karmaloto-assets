"""Coini skänner — kaks nimekirja, mis vastavad kahele eri küsimusele.

VSI ütleb, mis toimub ÜHE mündiga. Skänner ütleb, MILLIST vaadata.

Universum defineeritakse REEGLITEGA, mitte nimedega. Käsitsi valitud watchlist
töötab äärmuste otsija vastu: sa vaatad neid münte, mis sulle meelde tulid,
mitte neid, kus midagi toimub. Reeglid uuenevad ise.

    ÄÄRMUSED   |S| ≥ 60 ja V liigub S vastu   →  pöördekandidaadid
    JÄTK       V tugev, R sama märgiga, S mõõdukas  →  juba liikumises

Miks kaks. Äärmus üksi ei ole ajastus — funding võib olla ekstreemne nädalaid.
Sellepärast nõuab äärmuse nimekiri lisaks tõendust, et voog on hakanud surve
vastu liikuma. Ja enamik äärmusi ei pöördu üldse: see nimekiri annab
KANDIDAADID, mille peale VSI täies mahus jooksutada, mitte sisenemispunktid.

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

# --- universumi reeglid: null hooldust, nimekiri uueneb ise ---
MIN_OI_USD = 50e6       # allpool ei saa mõistliku slippage'iga sisse ega välja
MIN_MAHT_USD = 25e6
MIN_BORSE = 3           # "mitte shitcoin" — peab olema mitmel suurel börsil

# --- läved ---
LAVI_AARMUS = 60.0      # |S|, millest alates rahvahulk on tõesti ühel pool
MIN_POORDE_TOEND = 15.0 # |V|, millest alates saab öelda, et voog liigub vastu
LAVI_JATK = 30.0        # |V| jätku-nimekirja jaoks
MAX_RIDU = 4            # nimekirja kohta — pikem nimekiri on sama hea kui puuduv


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
    borside_arv: int = 5
    basis_nyyd: float | None = None
    basis_ajalugu: list[float] | None = None


@dataclass
class Rida:
    coin: str
    voog: float
    surve: float
    suhteline: float
    ylejaak: float
    oi_usd: float
    skoor: float
    suund: str
    pohjus: str
    lipud: list[str] = field(default_factory=list)

    def rida(self) -> str:
        lipud = ("  " + " · ".join(self.lipud)) if self.lipud else ""
        return (f"{self.coin:<8} {self.suund:<5} V {self.voog:+6.1f}  S {self.surve:+6.1f}  "
                f"R {self.suhteline:+5.2f}  skoor {self.skoor:5.1f}  {self.pohjus}{lipud}")


def _telg_vsi(k: Kandidaat) -> tuple[float, float, float, float]:
    """V ja S nädalaste refidega. Tagastab (V, V-kaetus, S, S-kaetus)."""
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
    voog, v_kate = vsi._telg(v)
    surve, s_kate = vsi._telg(s)
    return voog, v_kate, surve, s_kate


def _ristloike_z(vaartused: list[float]) -> list[float]:
    """z-skoor kandidaatide LÕIKES, mitte oma ajaloo vastu.

    Küsimus ei ole "kas ta on tugevam kui eelmisel nädalal", vaid "kas ta on
    tugevam kui teised praegu". Rotatsioon on suhteline mäng.
    """
    if len(vaartused) < 3:
        return [0.0] * len(vaartused)
    med = statistics.median(vaartused)
    mad = statistics.median([abs(x - med) for x in vaartused])
    if mad == 0:
        return [0.0] * len(vaartused)
    return [(x - med) / (1.4826 * mad) for x in vaartused]


def _universum(kandidaadid: list[Kandidaat], min_oi_usd: float, min_maht_usd: float,
               min_borse: int) -> tuple[list[Kandidaat], list[str]]:
    sobivad, valja = [], []
    for k in kandidaadid:
        if k.coin.strip().upper() in vsi.BTC_NIMED:
            valja.append(f"{k.coin}: võrdlusalus, mitte kandidaat")
        elif k.oi_usd < min_oi_usd:
            valja.append(f"{k.coin}: OI {k.oi_usd/1e6:.0f}M alla {min_oi_usd/1e6:.0f}M põranda")
        elif k.maht_usd < min_maht_usd:
            valja.append(f"{k.coin}: maht {k.maht_usd/1e6:.0f}M alla {min_maht_usd/1e6:.0f}M põranda")
        elif k.borside_arv < min_borse:
            valja.append(f"{k.coin}: ainult {k.borside_arv} börsil (vaja ≥ {min_borse})")
        else:
            sobivad.append(k)
    return sobivad, valja


def skanni(kandidaadid: list[Kandidaat], btc_tootlus: float,
           min_oi_usd: float = MIN_OI_USD, min_maht_usd: float = MIN_MAHT_USD,
           min_borse: int = MIN_BORSE
           ) -> tuple[list[Rida], list[Rida], list[str]]:
    """Tagastab (äärmused, jätk, väljajäänud)."""
    sobivad, valja = _universum(kandidaadid, min_oi_usd, min_maht_usd, min_borse)
    if not sobivad:
        return [], [], valja

    ylejaagid = [k.hinna_muutus - btc_tootlus for k in sobivad]
    z = _ristloike_z(ylejaagid)

    aarmused, jatk = [], []
    for k, yle, zz in zip(sobivad, ylejaagid, z):
        voog, v_kate, surve, s_kate = _telg_vsi(k)

        lipud = []
        # Suhteline tugevus, mis tuleb BTC langusest, ei ole coini tugevus.
        # Ilma selleta loeks skänner iga languses vastupidava mündi leiuks.
        if yle > 0 and k.hinna_muutus <= 0:
            lipud.append("tugevus tuleb BTC nõrkusest")
        if v_kate < 0.5 or s_kate < 0.5:
            lipud.append(f"kaetus V {v_kate:.0%} / S {s_kate:.0%}")

        def tee(skoor, suund, pohjus, kuhu):
            kuhu.append(Rida(k.coin, voog, surve, zz, yle, k.oi_usd,
                             skoor, suund, pohjus, list(lipud)))

        # --- ÄÄRMUS: rahvahulk maksimaalselt ühel pool JA voog liigub vastu ---
        # Korrutis, mitte summa: äärmus ilma pöördeta on null ja pööre ilma
        # äärmuseta on null. Kumbki üksi ei ole see, mida otsime.
        vastassuunas = (voog > 0) != (surve > 0)
        if (abs(surve) >= LAVI_AARMUS and vastassuunas
                and abs(voog) >= MIN_POORDE_TOEND):
            skoor = min(abs(surve), 100.0) * min(abs(voog) / 40.0, 1.0)
            if surve > 0:
                tee(skoor, "alla", "rahvas longis, voog pöördub välja", aarmused)
            else:
                tee(skoor, "üles", "rahvas shortis, voog pöördub sisse", aarmused)

        # --- JÄTK: liikumine käib, rahvahulk pole veel peal ---
        # V ja R peavad olema sama märgiga: münt, mis liigub oma suhtelise
        # tugevuse vastu, on müra, mitte trend.
        elif (abs(voog) >= LAVI_JATK and abs(surve) < LAVI_AARMUS
              and zz != 0 and (voog > 0) == (zz > 0)):
            karistus = 0.35 * abs(surve) if (voog > 0) == (surve > 0) else 0.0
            skoor = 0.6 * abs(voog) + 25 * abs(zz) - karistus
            if skoor > 0:
                tee(skoor, "üles" if voog > 0 else "alla",
                    "voog kannab, rahvas pole veel peal", jatk)

    aarmused.sort(key=lambda r: r.skoor, reverse=True)
    jatk.sort(key=lambda r: r.skoor, reverse=True)
    return aarmused[:MAX_RIDU], jatk[:MAX_RIDU], valja


def render(aarmused: list[Rida], jatk: list[Rida], valja: list[str],
           btc_tootlus: float, universumi_suurus: int) -> str:
    r = [
        "SKÄNN · nädalane aken",
        "=" * 88,
        f"  BTC samas aknas: {btc_tootlus:+.1%} · universumis {universumi_suurus} münti",
        f"  R = suhteline tugevus BTC vastu, z-skoor kandidaatide lõikes",
        "",
        f"  ÄÄRMUSED — |S| ≥ {LAVI_AARMUS:.0f} ja voog liigub surve vastu",
    ]
    if aarmused:
        r += [f"{i:>3}.  {x.rida()}" for i, x in enumerate(aarmused, 1)]
    else:
        r.append("       ükski münt ei ole korraga äärmuses ja pöördumas")
    r += ["", f"  JÄTK — |V| ≥ {LAVI_JATK:.0f}, R sama märgiga, |S| < {LAVI_AARMUS:.0f}"]
    if jatk:
        r += [f"{i:>3}.  {x.rida()}" for i, x in enumerate(jatk, 1)]
    else:
        r.append("       ükski münt ei liigu koos oma suhtelise tugevusega")
    if valja:
        r += ["", "  Universumist väljas:"]
        r += [f"    {x}" for x in valja]
    r += [
        "",
        "  Mõlemad nimekirjad on VAATAMISE JÄRJEKORD, mitte soovitus.",
        "  Äärmus ei ole ajastus — funding võib ekstreemne püsida nädalaid, ja",
        "  enamik äärmusi ei pöördu üldse. Iga rea kohta tuleb enne otsust",
        "  jooksutada täis-VSI koos invalideerimisega.",
    ]
    return "\n".join(r)


# --------------------------------------------------------------------------

def _demo() -> None:
    fh = [0.0001, 0.00008, 0.00012, 0.00005, 0.00015, 0.0001,
          0.00009, 0.00011, 0.00013, 0.00007, 0.0001, 0.00012]
    k = [
        # rahvas longis kaelani, hind hakkab alla tulema
        Kandidaat("AAA", -0.06, 0.14, -55e6, 700e6, 22e6, 2e6, 800e6, 0.0016, fh, 4.8, 0.62),
        # rahvas shortis, raha hakkab sisse tulema
        Kandidaat("BBB", 0.03, 0.16, 48e6, 600e6, 2e6, 19e6, 520e6, -0.0009, fh, 0.28, 0.58),
        # lihtsalt tugev liikumine, rahvas pole peal
        Kandidaat("CCC", 0.21, 0.24, 70e6, 900e6, 3e6, 12e6, 700e6, 0.00013, fh, 1.3, 0.55),
        # nõrk, ei sobi kummalegi
        Kandidaat("DDD", 0.01, 0.01, 2e6, 300e6, 1e6, 1e6, 400e6, 0.0001, fh, 1.05, 0.51),
        # liiga väike
        Kandidaat("EEE", 0.31, 0.40, 12e6, 18e6, 1e6, 2e6, 30e6, 0.0002, fh, 1.8, 0.30),
        # kahel börsil ainult
        Kandidaat("FFF", 0.18, 0.20, 30e6, 200e6, 2e6, 3e6, 300e6, 0.0002, fh, 1.5, 0.60, borside_arv=2),
    ]
    a, j, v = skanni(k, btc_tootlus=0.02)
    print(render(a, j, v, 0.02, len(k)))


def _test() -> None:
    ok = 0
    fh = [0.0001] * 6 + [0.00012, 0.00008, 0.00011, 0.00009]

    def teeb(coin, dh, doi, taker=30e6, oi=500e6, maht=300e6, ll=3e6, sl=6e6,
             funding=0.0001, ls=1.2, share=0.6, borse=5):
        return Kandidaat(coin, dh, doi, taker, maht, ll, sl, oi, funding, fh, ls, share, borse)

    # universumi reeglid viskavad välja, ei anna madalat skoori
    a, j, valja = skanni([teeb("SMALL", 0.4, 0.5, oi=10e6), teeb("THIN", 0.2, 0.2, borse=2),
                          teeb("BTC", 0.1, 0.1), teeb("OK", 0.2, 0.2)], 0.02)
    assert any("SMALL" in x for x in valja) and any("THIN" in x for x in valja)
    assert any("BTC" in x and "võrdlusalus" in x for x in valja)
    ok += 1

    # äärmus: rahvas longis (kõrge funding + ratio), voog alla
    aa = teeb("FLUSH", -0.06, 0.14, taker=-55e6, funding=0.002, ls=5.0)
    a, j, _ = skanni([aa, teeb("X", 0.01, 0.01), teeb("Y", 0.0, 0.0)], 0.0)
    assert [r.coin for r in a] == ["FLUSH"], f"äärmus jäi leidmata, sai {[r.coin for r in a]}"
    assert a[0].suund == "alla" and a[0].surve > LAVI_AARMUS and a[0].voog < 0
    ok += 1

    # äärmus teistpidi: rahvas shortis, voog üles
    bb = teeb("SQUEEZE", 0.03, 0.16, taker=48e6, sl=19e6, ll=2e6, funding=-0.0012, ls=0.25)
    a, j, _ = skanni([bb, teeb("X", 0.01, 0.01), teeb("Y", 0.0, 0.0)], 0.0)
    assert [r.coin for r in a] == ["SQUEEZE"]
    assert a[0].suund == "üles" and a[0].surve < -LAVI_AARMUS and a[0].voog > 0
    ok += 1

    # äärmus ILMA pöördeta ei kvalifitseeru — see on korrutise mõte
    paigal = teeb("PAIGAL", 0.005, 0.005, taker=1e6, funding=0.002, ls=5.0)
    a, j, _ = skanni([paigal, teeb("X", 0.01, 0.01), teeb("Y", 0.0, 0.0)], 0.0)
    assert not a, "äärmus ilma voo pöördeta ei ole kandidaat"
    ok += 1

    # jätk nõuab, et V ja R oleks sama märgiga
    a, j, _ = skanni([teeb("TUGEV", 0.25, 0.25), teeb("N1", -0.05, 0.0), teeb("N2", -0.06, 0.0)], 0.0)
    assert [r.coin for r in j] == ["TUGEV"], f"sai {[r.coin for r in j]}"
    assert j[0].suund == "üles"
    ok += 1

    # münt, mis liigub oma suhtelise tugevuse VASTU, ei kvalifitseeru:
    # hind tõuseb ja voog on üles, aga BTC vastu jääb ta kaugele maha
    a, j, _ = skanni([teeb("VASTU", 0.05, 0.20, taker=60e6),
                      teeb("P1", 0.50, 0.0), teeb("P2", 0.52, 0.0)], btc_tootlus=0.40)
    vastu = [r for r in j if r.coin == "VASTU"]
    assert not vastu, "V üles + R alla on müra, mitte trend"
    ok += 1

    # tugevus BTC nõrkusest saab lipu
    a, j, _ = skanni([teeb("FLAT", -0.01, 0.20, taker=40e6), teeb("X", -0.15, 0.1),
                      teeb("Y", -0.20, 0.1)], btc_tootlus=-0.18)
    koik = a + j
    flat = [r for r in koik if r.coin == "FLAT"]
    if flat:
        assert any("BTC nõrkusest" in f for f in flat[0].lipud)
    ok += 1

    # nimekirjad on piiratud
    palju = [teeb(f"C{i}", 0.20 + i*0.01, 0.25, taker=60e6) for i in range(10)]
    a, j, _ = skanni(palju, 0.0)
    assert len(a) <= MAX_RIDU and len(j) <= MAX_RIDU
    ok += 1

    # tühi sisend ei kuku kokku
    assert skanni([], 0.0) == ([], [], [])
    ok += 1

    print(f"{ok}/9 testiplokki OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    else:
        _demo()
