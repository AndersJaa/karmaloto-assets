"""VSI — Voog–Surve indeks.

Kaheteljeline liitindikaator, mis koondab AINULT mehaaniliselt mõõdetavad
näitajad turu seaduspärasuste koondtabelist (plokid D, E, F, G).

Elliott, Gann, Wyckoff ja mustrituvastus on siit teadlikult VÄLJA jäetud:
need on tõlgendus, mitte mõõt, ning neid ei saa arvuks taandada ilma, et
number teeskleks täpsust, mida tal ei ole. Struktuur jääb eraldi kihiks.

    Telg V (voog)   -100…+100   mida raha PRAEGU teeb
    Telg S (surve)  -100…+100   kui ühel pool rahvahulk on

    S > 0 = rahvahulk on longis (üleval surve alla)
    S < 0 = rahvahulk on shortis (all surve üles)

Kaks telge EI liideta üheks numbriks. Liitmine kaotaks just selle info,
mis siin loeb: tõus madala survega ja tõus kõrge survega on vastandid,
kuigi mõlemal on V positiivne.

Kasutus:
    python3 vsi.py --demo
    python3 vsi.py --test
"""

from __future__ import annotations

import math
import statistics
import sys
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Normaliseerimine
# --------------------------------------------------------------------------

def robust_z(value: float, ajalugu: list[float]) -> float:
    """z-skoor mediaani ja MAD-i baasil.

    Tavaline keskmine/stdev on paksude sabade tõttu kasutuskõlbmatu (plokk D):
    üks likvideerimiskaskaad nihutab keskmise ära ja kõik järgnevad z-skoorid
    on valed. Mediaan/MAD ei liigu üksikute ekstreemide peale.
    """
    if len(ajalugu) < 8:
        raise ValueError(f"z-skoor vajab >= 8 vaatlust, sai {len(ajalugu)}")
    med = statistics.median(ajalugu)
    mad = statistics.median([abs(x - med) for x in ajalugu])
    if mad == 0:
        return 0.0
    return (value - med) / (1.4826 * mad)


def squash(z: float, k: float = 1.5) -> float:
    """z-skoor -> [-1, 1]. k = mitme z juures loetakse ekstreemiks."""
    return math.tanh(z / k)


def clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


# --------------------------------------------------------------------------
# Komponent
# --------------------------------------------------------------------------

@dataclass
class Komponent:
    nimi: str
    skoor: float          # [-1, 1]
    kaal: float           # suhteline kaal teljel
    selgitus: str         # mida see arv tähendab, inimkeeles
    allikas: str          # mis kutse selle andis — jälgitavuse nõue
    kehtiv: bool = True   # False = värav sulges selle, kaal jaotatakse ümber

    def panus(self, kaalude_summa: float) -> float:
        return 100.0 * self.skoor * self.kaal / kaalude_summa if kaalude_summa else 0.0


def _telg(komponendid: list[Komponent]) -> tuple[float, float]:
    """Tagastab (telje väärtus -100..100, kaetud kaalu osakaal 0..1)."""
    kehtivad = [k for k in komponendid if k.kehtiv]
    kaalud = sum(k.kaal for k in kehtivad)
    kogukaal = sum(k.kaal for k in komponendid)
    if kaalud == 0:
        return 0.0, 0.0
    vaartus = sum(k.skoor * k.kaal for k in kehtivad) / kaalud * 100.0
    return vaartus, kaalud / kogukaal


# --------------------------------------------------------------------------
# V-telg — voog. Mida raha praegu teeb.
# --------------------------------------------------------------------------

def oi_hinna_kvadrant(hinna_muutus: float, oi_muutus: float,
                      hinna_ref: float = 0.03, oi_ref: float = 0.05) -> Komponent:
    """Plokk E. Neli kombinatsiooni, mille tõlgendused on vastandlikud.

    Ainult USD-s ja mitme börsi peale agregeeritud OI-ga. Coin-ühikutes OI
    annab hinnaliikumisel vale vastuse.
    """
    mag = clip(math.hypot(hinna_muutus / hinna_ref, oi_muutus / oi_ref) / math.sqrt(2), 0, 1)
    if hinna_muutus >= 0 and oi_muutus >= 0:
        base, silt = 1.0, "uus raha longi — kõige puhtam tõus"
    elif hinna_muutus >= 0 and oi_muutus < 0:
        base, silt = 0.3, "shortide kattmine, mitte ostmine"
    elif hinna_muutus < 0 and oi_muutus >= 0:
        base, silt = -1.0, "uued shordid tulevad peale"
    else:
        base, silt = -0.3, "longide sundmüük, positsioonid kaovad"
    return Komponent(
        "OI + hind", base * mag, 35,
        f"{silt} (hind {hinna_muutus:+.1%}, OI {oi_muutus:+.1%})",
        "oi_history action=aggregated + price_history",
    )


def taker_cvd(neto_taker_usd: float, maht_usd: float, ref: float = 0.05) -> Komponent:
    """Plokk E. Agressiivsete ostjate netovoog, normaliseeritud kogumahuga.

    ALATI coin_history, mitte pair_history. Paaritasandi feed on olnud 50-100x
    vale — kutsuja peab olema selle price_history mahuga ristkontrollinud.
    """
    if maht_usd <= 0:
        return Komponent("Taker CVD", 0.0, 30, "mahtu ei ole — komponent maas",
                         "taker action=coin_history", kehtiv=False)
    suhe = neto_taker_usd / maht_usd
    return Komponent(
        "Taker CVD", clip(suhe / ref), 30,
        f"neto {suhe:+.1%} kogumahust ({neto_taker_usd/1e6:+.1f}M / {maht_usd/1e6:.0f}M)",
        "taker action=coin_history",
    )


def likvideerimised(long_liq_usd: float, short_liq_usd: float, oi_usd: float,
                    mura_lavi: float = 0.005) -> Komponent:
    """Plokk E+F. Long-likvideerimine = sundmüük (alla), short = sundost (üles).

    Värav: alla ~0.5% OI-st on see müra, ükskõik kui kaldu on long/short jaotus.
    90/10 jaotus 0.1% OI pealt ei ole kaskaad — see on kolm inimest.
    """
    kokku = long_liq_usd + short_liq_usd
    osa = kokku / oi_usd if oi_usd > 0 else 0.0
    if osa < mura_lavi:
        return Komponent(
            "Likvideerimised", 0.0, 20,
            f"{osa:.2%} OI-st — alla {mura_lavi:.1%} läve, MÜRA, komponent maas",
            "liq_history action=aggregated", kehtiv=False,
        )
    kalle = (short_liq_usd - long_liq_usd) / kokku
    intensiivsus = clip(osa / 0.02, 0, 1)
    return Komponent(
        "Likvideerimised", kalle * intensiivsus, 20,
        f"{osa:.2%} OI-st, kalle {'shortide' if kalle > 0 else 'longide'} suunas ({abs(kalle):.0%})",
        "liq_history action=aggregated",
    )


def spot_voog(neto_voog_usd: float, oi_usd: float, ref: float = 0.02) -> Komponent:
    """Plokk G. ETF- ja spot-netovoog. Ainult BTC/ETH — altidele ei kandu."""
    if oi_usd <= 0:
        return Komponent("Spot/ETF voog", 0.0, 15, "OI puudub", "päevased netovood", kehtiv=False)
    suhe = neto_voog_usd / oi_usd
    return Komponent(
        "Spot/ETF voog", clip(suhe / ref), 15,
        f"neto {neto_voog_usd/1e6:+.0f}M = {suhe:+.2%} OI-st",
        "päevased netovood",
    )


# --------------------------------------------------------------------------
# S-telg — surve. Kui ühel pool rahvahulk on.
# --------------------------------------------------------------------------

def funding_surve(funding_nyyd: float, funding_ajalugu: list[float]) -> Komponent:
    """Plokk E. Kõrge positiivne funding = longid maksavad = rahvas on longis.

    Ekstreem EI anna ajastust — võib püsida nädalaid. See on surve mõõt,
    mitte päästik.
    """
    z = robust_z(funding_nyyd, funding_ajalugu)
    return Komponent(
        "Funding", squash(z), 45,
        f"{funding_nyyd:+.4%} vs ajalugu, z = {z:+.1f}",
        "funding_history action=oi_weighted",
    )


def long_short_kalle(ratio: float, borsi_oi_osakaal: float) -> Komponent:
    """Plokk E. Retaili kalle, ALATI börsi OI-osakaaluga skaleeritud.

    Alla ~25% OI-st hoidva börsi ratio ei ole rahvahulk. Kontode arv ei ole
    raha — sellepärast on kaal madal ja skaleerimine kohustuslik.
    """
    if ratio <= 0:
        return Komponent("Long/short", 0.0, 25, "vigane ratio", "long_short action=global", kehtiv=False)
    toores = squash(math.log(ratio) / 0.35)
    if borsi_oi_osakaal < 0.25:
        return Komponent(
            "Long/short", toores * borsi_oi_osakaal, 25,
            f"ratio {ratio:.2f}, aga börs katab vaid {borsi_oi_osakaal:.0%} OI-st — EI ole rahvahulk, kaal alla surutud",
            "long_short action=global + oi_distribution",
        )
    return Komponent(
        "Long/short", toores * borsi_oi_osakaal, 25,
        f"ratio {ratio:.2f} börsil, mis katab {borsi_oi_osakaal:.0%} OI-st",
        "long_short action=global + oi_distribution",
    )


def basis_surve(basis_nyyd: float, basis_ajalugu: list[float]) -> Komponent:
    """Plokk E. Contango ekstreem = ülekuumenemine, backwardation = kapitulatsioon."""
    z = robust_z(basis_nyyd, basis_ajalugu)
    return Komponent(
        "Basis", squash(z), 30,
        f"annualiseeritud {basis_nyyd:+.1%}, z = {z:+.1f}",
        "kvartalifutuur vs spot",
    )


# --------------------------------------------------------------------------
# Väravad — usaldusväärsuse kordaja, mitte suund
# --------------------------------------------------------------------------

def volatiliteedi_reziim(atr_pertsentiil: float) -> tuple[str, str]:
    """Plokk D. Ei anna suunda — annab ajastuse akna.

    Kokkusurutud ATR ütleb, et liikumine TULEB, mitte kuhu.
    """
    if atr_pertsentiil <= 0.20:
        return "kokku surutud", "laienemine ees — suunda see ei ütle, ainult et liikumine tuleb"
    if atr_pertsentiil >= 0.80:
        return "laienenud", "tagasitõmme tõenäoline, positsiooni suurus peab seda arvestama"
    return "normaalne", "ajastuse eelist ei ole"


@dataclass
class Varavad:
    """Kõik väärtused 0..1. Korrutuvad usaldusväärsuseks."""
    andmete_vanus_h: float = 0.0
    max_vanus_h: float = 3.0
    kaetud_oi_osakaal: float = 1.0     # kui suurt osa OI-st andmed katavad
    btc_korrelatsioon: float = 0.0     # |corr| coini ja BTC vahel samas aknas

    def varskus(self) -> float:
        if self.andmete_vanus_h <= self.max_vanus_h:
            return 1.0
        return clip(self.max_vanus_h / self.andmete_vanus_h, 0.0, 1.0)

    def juhtiv_muutuja(self) -> str:
        return "BTC" if abs(self.btc_korrelatsioon) >= 0.80 else "coin ise"

    def hoiatused(self) -> list[str]:
        h = []
        if self.andmete_vanus_h > self.max_vanus_h:
            h.append(f"andmed on {self.andmete_vanus_h:.1f}h vanad (lubatud {self.max_vanus_h:.0f}h)")
        if self.kaetud_oi_osakaal < 0.60:
            h.append(f"andmed katavad ainult {self.kaetud_oi_osakaal:.0%} OI-st")
        if abs(self.btc_korrelatsioon) >= 0.80:
            h.append(f"BTC korrelatsioon {self.btc_korrelatsioon:+.2f} — coin ei liigu oma andmete peale")
        return h


# --------------------------------------------------------------------------
# Lugemine
# --------------------------------------------------------------------------

KVADRANDID = {
    ("+", "-"): ("PUHAS TÕUS", "raha voolab sisse ja rahvahulk pole veel longis — kõige tervem tõusukonfiguratsioon"),
    ("+", "+"): ("ÜLEKUUMENENUD TÕUS", "voog on üles, aga rahvahulk on juba longis — tõus kestab kütusega, mis on ise risk"),
    ("-", "+"): ("LONGIDE VÄLJASURUMINE", "voog on alla ja rahvahulk on longis — kõige valusam kombinatsioon longidele"),
    ("-", "-"): ("SHORTIDE KÜTUS", "voog on alla, aga shordid on ülerahvastatud — iga tõuge üles leiab kütust"),
}


@dataclass
class Lugemine:
    coin: str
    voog: float
    surve: float
    voo_kate: float
    surve_kate: float
    varavad: Varavad
    reziim: tuple[str, str]
    v_komponendid: list[Komponent] = field(default_factory=list)
    s_komponendid: list[Komponent] = field(default_factory=list)
    invalideerimine: str | None = None

    LAVI = 25.0  # alla selle ei ole lugemist

    def usaldusvaarsus(self) -> float:
        return (self.varavad.varskus()
                * self.varavad.kaetud_oi_osakaal
                * (self.voo_kate + self.surve_kate) / 2)

    def kvadrant(self) -> tuple[str, str]:
        if abs(self.voog) < self.LAVI:
            return ("LUGEMIST EI OLE", f"voog {self.voog:+.0f} on alla {self.LAVI:.0f} läve — "
                                       "ütle seda otse, ära tooda stsenaariume")
        return KVADRANDID[("+" if self.voog >= 0 else "-", "+" if self.surve >= 0 else "-")]

    def render(self) -> str:
        if self.invalideerimine is None:
            raise ValueError(
                "Invalideerimine on kohustuslik. Ilma täpse hinna või tingimuseta, "
                "mis lugemise valeks tunnistab, lugemist ei anta."
            )
        pealkiri, seletus = self.kvadrant()
        u = self.usaldusvaarsus()
        r = [
            f"VSI · {self.coin}",
            "=" * 58,
            f"  Voog  V = {self.voog:+6.1f}   (kaetud {self.voo_kate:.0%} kaalust)",
            f"  Surve S = {self.surve:+6.1f}   (kaetud {self.surve_kate:.0%} kaalust)",
            "",
            f"  {pealkiri}",
            f"  {seletus}",
            "",
            f"  Usaldusväärsus {u:.0%} · juhtiv muutuja: {self.varavad.juhtiv_muutuja()}",
            f"  Volatiliteet: {self.reziim[0]} — {self.reziim[1]}",
        ]
        for h in self.varavad.hoiatused():
            r.append(f"  ! {h}")
        r += ["", "  V-telje panus:"]
        vk = sum(k.kaal for k in self.v_komponendid if k.kehtiv)
        for k in self.v_komponendid:
            m = "  " if k.kehtiv else " x"
            r.append(f"   {m} {k.nimi:<18} {k.panus(vk):+6.1f}  {k.selgitus}")
            r.append(f"        {'':<18}         allikas: {k.allikas}")
        r += ["", "  S-telje panus:"]
        sk = sum(k.kaal for k in self.s_komponendid if k.kehtiv)
        for k in self.s_komponendid:
            m = "  " if k.kehtiv else " x"
            r.append(f"   {m} {k.nimi:<18} {k.panus(sk):+6.1f}  {k.selgitus}")
            r.append(f"        {'':<18}         allikas: {k.allikas}")
        r += ["", f"  Invalideerimine: {self.invalideerimine}",
              "", "  Kontekst, mitte kauplemissignaal. Suunda ega positsiooni suurust siin ei ole."]
        return "\n".join(r)


def arvuta(coin: str, v_komponendid: list[Komponent], s_komponendid: list[Komponent],
           varavad: Varavad, atr_pertsentiil: float,
           invalideerimine: str | None = None) -> Lugemine:
    voog, v_kate = _telg(v_komponendid)
    surve, s_kate = _telg(s_komponendid)
    return Lugemine(coin, voog, surve, v_kate, s_kate, varavad,
                    volatiliteedi_reziim(atr_pertsentiil),
                    v_komponendid, s_komponendid, invalideerimine)


# --------------------------------------------------------------------------
# Demo ja testid
# --------------------------------------------------------------------------

def _demo() -> None:
    """Väljamõeldud arvud. Päris lugemiseks tulevad need CoinGlassi kutsetest."""
    funding_ajalugu = [0.0001, 0.00008, 0.00012, 0.00005, 0.00015, 0.0001,
                       0.00009, 0.00011, 0.00013, 0.00007, 0.0001, 0.00012]
    basis_ajalugu = [0.05, 0.06, 0.045, 0.055, 0.07, 0.05, 0.048, 0.062, 0.058, 0.05]

    v = [
        oi_hinna_kvadrant(hinna_muutus=0.042, oi_muutus=0.068),
        taker_cvd(neto_taker_usd=41e6, maht_usd=980e6),
        likvideerimised(long_liq_usd=2.1e6, short_liq_usd=9.4e6, oi_usd=1_235e6),
        spot_voog(neto_voog_usd=18e6, oi_usd=1_235e6),
    ]
    s = [
        funding_surve(0.00042, funding_ajalugu),
        long_short_kalle(ratio=2.35, borsi_oi_osakaal=0.53),
        basis_surve(0.118, basis_ajalugu),
    ]
    g = Varavad(andmete_vanus_h=1.2, kaetud_oi_osakaal=0.88, btc_korrelatsioon=0.61)
    lug = arvuta("HYPE", v, s, g, atr_pertsentiil=0.83,
                 invalideerimine="4h sulgemine alla 38.40 tühistab voo lugemise; "
                                 "funding alla mediaani tühistab surve lugemise")
    print(lug.render())


def _test() -> None:
    ok = 0

    # kvadrandid annavad vastandliku märgi
    a, _ = oi_hinna_kvadrant(0.05, 0.05), None
    assert a.skoor > 0, "hind üles + OI üles peab olema positiivne"
    b = oi_hinna_kvadrant(-0.05, 0.05)
    assert b.skoor < 0, "hind alla + OI üles peab olema negatiivne"
    c = oi_hinna_kvadrant(0.05, -0.05)
    assert 0 < c.skoor < a.skoor, "shortide kattmine peab olema nõrgem kui uus raha"
    ok += 1

    # likvideerimiste müravärav
    mura = likvideerimised(long_liq_usd=0.9e6, short_liq_usd=0.1e6, oi_usd=1_000e6)
    assert not mura.kehtiv and mura.skoor == 0.0, "0.1% OI-st peab olema müra"
    paris = likvideerimised(long_liq_usd=30e6, short_liq_usd=2e6, oi_usd=1_000e6)
    assert paris.kehtiv and paris.skoor < 0, "long-likvideerimine on müügisurve"
    ok += 1

    # kehtetu komponent ei lahjenda telge, vaid kaal jaotub ümber
    komp = [Komponent("a", 1.0, 50, "", ""), Komponent("b", 0.0, 50, "", "", kehtiv=False)]
    val, kate = _telg(komp)
    assert abs(val - 100.0) < 1e-9, f"kehtiv komponent peab andma 100, sai {val}"
    assert abs(kate - 0.5) < 1e-9, "kate peab näitama, et pool kaalust on maas"
    ok += 1

    # väikese OI-osakaaluga börsi ratio surutakse alla
    suur = long_short_kalle(2.5, 0.90)
    vaike = long_short_kalle(2.5, 0.10)
    assert abs(vaike.skoor) < abs(suur.skoor) / 5, "vähese katvusega börs ei tohi telge liigutada"
    ok += 1

    # MAD-z ei lähe üksikust ekstreemist katki
    aj = [1.0] * 11 + [50.0]
    assert abs(robust_z(1.0, aj)) < 1.0, "üks ekstreem ei tohi baastaset nihutada"
    ok += 1

    # nõrk voog = lugemist ei ole
    lug = arvuta("X", [Komponent("a", 0.1, 100, "", "")], [Komponent("b", 0.9, 100, "", "")],
                 Varavad(), 0.5, invalideerimine="test")
    assert lug.kvadrant()[0] == "LUGEMIST EI OLE", "alla läve ei anta suunda"
    ok += 1

    # invalideerimiseta ei renderdata
    lug2 = arvuta("X", [Komponent("a", 0.9, 100, "", "")], [Komponent("b", 0.9, 100, "", "")],
                  Varavad(), 0.5)
    try:
        lug2.render()
        raise AssertionError("invalideerimiseta pidi render() vea andma")
    except ValueError:
        pass
    ok += 1

    # vananenud andmed langetavad usaldusväärsust
    varske = Varavad(andmete_vanus_h=1.0)
    vana = Varavad(andmete_vanus_h=12.0)
    assert vana.varskus() < varske.varskus() == 1.0
    ok += 1

    print(f"{ok}/8 testiplokki OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    else:
        _demo()
