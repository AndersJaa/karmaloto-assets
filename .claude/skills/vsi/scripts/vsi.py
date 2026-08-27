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

    MAD-il on aga oma lõks, mis puudutab just fundingut: kui üle poole ajaloost
    on identne — ja börsid hoiavad fundingut tihti mitu perioodi täpselt samal
    väärtusel — siis MAD on null ja iga hälve, ka kahekümnekordne, loeks z = 0.
    See oleks vaikne vale vastus, mitte ettevaatlik vastus. Sellepärast on
    kaks tagavara: keskmine absoluuthälve, mis nii kergesti ei kollapseeru, ja
    täiesti lameda ajaloo puhul küllastunud hälve, mis ütleb "ekstreem, aga
    ulatust ei saa mõõta".
    """
    if len(ajalugu) < 8:
        raise ValueError(f"z-skoor vajab >= 8 vaatlust, sai {len(ajalugu)}")
    med = statistics.median(ajalugu)
    hajuvus = 1.4826 * statistics.median([abs(x - med) for x in ajalugu])
    if hajuvus == 0:
        hajuvus = 1.2533 * (sum(abs(x - med) for x in ajalugu) / len(ajalugu))
    if hajuvus == 0:
        return 0.0 if value == med else math.copysign(6.0, value - med)
    return (value - med) / hajuvus


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


# Telje täiskaal. Kaetust mõõdetakse SELLE, mitte kaasa antud komponentide
# summa vastu. Vahe on oluline: kui nimetaja on kaasa antute summa, siis
# komponendi ärajätmine PARANDAB kaetuse numbrit — mida vähem andmeid, seda
# terveni telg paistab. HYPE-l juhtus täpselt see: basis puudub (kvartalifutuuri
# pole) ja long/short lülitub välja (Hyperliquid ei anna ratiot), S seisab
# ainult fundingu peal, aga näitas 64% kaetust.
V_TAISKAAL = 100.0
S_TAISKAAL = 100.0


def _telg(komponendid: list[Komponent], taiskaal: float | None = None) -> tuple[float, float]:
    """Tagastab (telje väärtus -100..100, kaetud osa täiskaalust 0..1).

    `taiskaal=None` mõõdab kaasa antute summa vastu — seda kasutab skänner,
    mis teadlikult jätab osa komponente välja ega taotle täiskatvust.
    """
    kehtivad = [k for k in komponendid if k.kehtiv]
    kaalud = sum(k.kaal for k in kehtivad)
    nimetaja = taiskaal if taiskaal is not None else sum(k.kaal for k in komponendid)
    if kaalud == 0 or nimetaja == 0:
        return 0.0, 0.0
    vaartus = sum(k.skoor * k.kaal for k in kehtivad) / kaalud * 100.0
    return vaartus, min(kaalud / nimetaja, 1.0)


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
        # Varem skaleeriti siin skoor peaaegu nulli, aga kaal luges kaetuse
        # arvestuses edasi täiega — 25 kaaluühikut, mis annab 0.5 signaali.
        # Nii näitas telg "70% kaetud" ka siis, kui ta seisis ühe komponendi
        # peal. Vale venue ei ole nõrk andmepunkt, ta ei ole andmepunkt.
        return Komponent(
            "Long/short", 0.0, 25,
            f"ratio {ratio:.2f}, aga börs katab vaid {borsi_oi_osakaal:.0%} OI-st — "
            "EI ole rahvahulk, komponent maas. Võta ratio domineerivalt börsilt",
            "long_short action=global + oi_distribution", kehtiv=False,
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
        f"{basis_nyyd:+.2%} (toores, mitte annualiseeritud), z = {z:+.1f}",
        "kvartalifutuur vs spot",
    )


# --------------------------------------------------------------------------
# Väravad — usaldusväärsuse kordaja, mitte suund
# --------------------------------------------------------------------------

def _rma(vaartused: list[float], n: int) -> list[float]:
    """Wilderi silumine. Esimene vaartus on SMA, edasi rekursiivne."""
    if len(vaartused) < n:
        return []
    out = [sum(vaartused[:n]) / n]
    for x in vaartused[n:]:
        out.append((out[-1] * (n - 1) + x) / n)
    return out


def adx(high: list[float], low: list[float], close: list[float],
        di_pikkus: int = 14, silumine: int = 14) -> float:
    """Wilderi ADX. Trendi TUGEVUS, mitte suund.

    Vajab vahemalt di_pikkus + silumine + 1 kuunalt.
    """
    n = len(close)
    if n < di_pikkus + silumine + 1:
        raise ValueError(f"ADX vajab >= {di_pikkus + silumine + 1} kuunalt, sai {n}")
    tr, plus_dm, minus_dm = [], [], []
    for i in range(1, n):
        ules = high[i] - high[i - 1]
        alla = low[i - 1] - low[i]
        plus_dm.append(ules if (ules > alla and ules > 0) else 0.0)
        minus_dm.append(alla if (alla > ules and alla > 0) else 0.0)
        tr.append(max(high[i] - low[i],
                      abs(high[i] - close[i - 1]),
                      abs(low[i] - close[i - 1])))
    tr_s, p_s, m_s = _rma(tr, di_pikkus), _rma(plus_dm, di_pikkus), _rma(minus_dm, di_pikkus)
    dx = []
    for t, pp, mm in zip(tr_s, p_s, m_s):
        if t == 0:
            dx.append(0.0)
            continue
        di_p, di_m = 100 * pp / t, 100 * mm / t
        summa = di_p + di_m
        dx.append(100 * abs(di_p - di_m) / summa if summa else 0.0)
    silutud = _rma(dx, silumine)
    if not silutud:
        raise ValueError("ADX-i ei saanud arvutada — liiga vahe andmeid")
    return silutud[-1]


def choppiness(high: list[float], low: list[float], close: list[float],
               pikkus: int = 14) -> float:
    """Choppiness Index. > 61.8 = kulgsuunaline, < 38.2 = trendiv.

    Motleb sama asja kust teisest otsast kui ADX: kui palju teed kaib hind
    ara vorreldes sellega, kui kaugele ta joudis. Kaks sold korraga on tugevam
    kui kumbki eraldi, sest nad eksivad erinevatel juhtudel.
    """
    n = len(close)
    if n < pikkus + 1:
        raise ValueError(f"Choppiness vajab >= {pikkus + 1} kuunalt, sai {n}")
    tr = [max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
          for i in range(n - pikkus, n)]
    ulatus = max(high[-pikkus:]) - min(low[-pikkus:])
    if ulatus <= 0 or sum(tr) <= 0:
        return 100.0
    return 100.0 * math.log10(sum(tr) / ulatus) / math.log10(pikkus)


def treni_reziim(adx_vaartus: float, chop_vaartus: float, hind_ule_ema200: bool
                 ) -> tuple[str, str, bool]:
    """Kas turg trendib voi kaib kulgsuunas. Tagastab (nimi, selgitus, on_range).

    Reegel parineb only_fibonacci Multicator Table'ist: ADX < 20 VOI Chop > 61.8
    tahendab kulgsuunalist. Kaks tingimust VOI-ga, sest kumbki uksi jatab augu:
    ADX jaab madalaks ka aeglases trendis, Chop laheb korgeks ka lai vahemik.
    """
    if adx_vaartus < 20 or chop_vaartus > 61.8:
        return ("külgsuunaline",
                f"ADX {adx_vaartus:.0f}, Chop {chop_vaartus:.0f} — servad hoiavad, "
                "murrud kukuvad tagasi, voo lävi on tõstetud",
                True)
    suund = "üles" if hind_ule_ema200 else "alla"
    return (f"trend {suund}",
            f"ADX {adx_vaartus:.0f}, Chop {chop_vaartus:.0f} — voog kannab, "
            "tagasitõmbed on ostu-/müügikohad, mitte pöörded",
            False)


def volatiliteedi_reziim(atr_pertsentiil: float) -> tuple[str, str]:
    """Plokk D. Ei anna suunda — annab ajastuse akna.

    Kokkusurutud ATR ütleb, et liikumine TULEB, mitte kuhu. See on trendi
    režiimist SÕLTUMATU: külgsuunaline turg võib olla nii kokku surutud kui
    laienenud, ja need kaks tähendavad täiesti eri asja.
    """
    if atr_pertsentiil <= 0.20:
        return "kokku surutud", "laienemine ees — suunda see ei ütle, ainult et liikumine tuleb"
    if atr_pertsentiil >= 0.80:
        return "laienenud", "tagasitõmme tõenäoline, positsiooni suurus peab seda arvestama"
    return "normaalne", "ajastuse eelist ei ole"


BTC_NIMED = {"BTC", "XBT", "BTCUSD", "BTCUSDT"}


@dataclass
class Varavad:
    """Kõik väärtused 0..1. Korrutuvad usaldusväärsuseks."""
    andmete_vanus_h: float = 0.0
    max_vanus_h: float = 3.0
    kaetud_oi_osakaal: float = 1.0     # kui suurt osa OI-st andmed katavad
    btc_korrelatsioon: float = 0.0     # |corr| coini ja BTC vahel samas aknas
    on_btc: bool = False               # lugemine käib BTC enda kohta

    def varskus(self) -> float:
        if self.andmete_vanus_h <= self.max_vanus_h:
            return 1.0
        return clip(self.max_vanus_h / self.andmete_vanus_h, 0.0, 1.0)

    def juhtiv_muutuja(self) -> str:
        """BTC enda peal on korrelatsioon iseendaga 1.0 ja ei tähenda midagi.

        Ilma selle erandita ütleks lugemine BTC kohta "juhtiv muutuja on BTC,
        coin ei liigu oma andmete peale" — tautoloogia, mis näeb välja nagu
        hoiatus ja paneb kahtlema lugemises, millel viga pole.
        """
        if self.on_btc:
            return "BTC ise — ta ongi turu juht"
        return "BTC" if abs(self.btc_korrelatsioon) >= 0.80 else "coin ise"

    def hoiatused(self) -> list[str]:
        h = []
        if self.andmete_vanus_h > self.max_vanus_h:
            h.append(f"andmed on {self.andmete_vanus_h:.1f}h vanad (lubatud {self.max_vanus_h:.0f}h)")
        if self.kaetud_oi_osakaal < 0.60:
            h.append(f"andmed katavad ainult {self.kaetud_oi_osakaal:.0%} OI-st")
        if not self.on_btc and abs(self.btc_korrelatsioon) >= 0.80:
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
    trend: tuple[str, str, bool]
    v_komponendid: list[Komponent] = field(default_factory=list)
    s_komponendid: list[Komponent] = field(default_factory=list)
    invalideerimine: str | None = None

    LAVI_TREND = 25.0   # trendis piisab nõrgemast voost
    LAVI_RANGE = 40.0   # külgsuunas peab voog olema selgelt tugevam
    MIN_KATE = 0.50     # alla poole telje kaalust ei ole telg, vaid üks komponent

    def lavi(self) -> float:
        """Külgsuunalises turus on valemurd reegel, mitte erand — lävi tõuseb.

        See on ainus koht, kus trendi režiim numbrit liigutab. Suunda ta ei anna.
        """
        return self.LAVI_RANGE if self.trend[2] else self.LAVI_TREND

    def usaldusvaarsus(self) -> float:
        return (self.varavad.varskus()
                * self.varavad.kaetud_oi_osakaal
                * (self.voo_kate + self.surve_kate) / 2)

    def vastuolu(self, komponendid: list[Komponent], telje_nimi: str) -> str | None:
        """Kas telje väärtus on väike sellepärast, et komponendid tühistavad teineteist?

        Telg −2 võib tähendada kahte täiesti eri asja: kõik komponendid on
        vaiksed, või kaks tugevat komponenti näitavad vastassuunda ja summa
        juhtub nulli lähedale kukkuma. Esimene on „ei ole survet", teine on
        „andmed ei ole ühel meelel". Numbrina on nad identsed, tähenduselt
        vastandid — ja vaikimisi esitatakse teine esimesena.
        """
        kehtivad = [k for k in komponendid if k.kehtiv]
        kaalud = sum(k.kaal for k in kehtivad)
        if not kaalud:
            return None
        panused = [(k.nimi, 100.0 * k.skoor * k.kaal / kaalud) for k in kehtivad]
        plussid = [p for p in panused if p[1] > 20]
        miinused = [p for p in panused if p[1] < -20]
        if not (plussid and miinused):
            return None
        summa = sum(p[1] for p in panused)
        if abs(summa) > 20:
            return None  # üks pool võitis selgelt, see ei ole tühistus
        nimed = ", ".join(f"{n} {v:+.0f}" for n, v in sorted(panused, key=lambda x: -abs(x[1])))
        return (f'{telje_nimi} on {summa:+.0f} sellepärast, et komponendid tühistavad '
                f'teineteist ({nimed}) — see EI ole „neutraalne", vaid „andmed ei ole '
                f'ühel meelel". Vaata komponente eraldi.')

    def vastuolud(self) -> list[str]:
        return [x for x in (self.vastuolu(self.v_komponendid, "Voog"),
                            self.vastuolu(self.s_komponendid, "Surve")) if x]

    def kvadrant(self) -> tuple[str, str]:
        # Kaetuse põrand. Kaal jaotub puuduvate komponentide pealt ümber, mis on
        # õige — aga kui alles on vähem kui pool, siis ei mõõda telg enam seda,
        # mida ta lubab: üks ellujäänud komponent saab terve telje endale ja
        # annab uhke +100. Madal usaldusväärsuse protsent on kõrvalmärkus, mida
        # keegi verdikti kõrval ei loe. Nii et sellisel juhul lugemist ei tule.
        puudulik = []
        if self.voo_kate < self.MIN_KATE:
            puudulik.append(f"V-teljel on kaetud {self.voo_kate:.0%} kaalust")
        if self.surve_kate < self.MIN_KATE:
            puudulik.append(f"S-teljel on kaetud {self.surve_kate:.0%} kaalust")
        if puudulik:
            return ("LUGEMIST EI OLE",
                    " ja ".join(puudulik) + f" (vaja vähemalt {self.MIN_KATE:.0%}) — "
                    "puuduvad komponendid tuleb tõmmata, mitte ümber kaaluda")

        lavi = self.lavi()
        if abs(self.voog) < lavi:
            lisa = " (tõstetud, sest turg on külgsuunaline)" if self.trend[2] else ""
            return ("LUGEMIST EI OLE", f"voog {self.voog:+.0f} on alla {lavi:.0f} läve{lisa} — "
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
            f"  Režiim: {self.trend[0]} — {self.trend[1]}",
            f"  Volatiliteet: {self.reziim[0]} — {self.reziim[1]}",
            f"  Voo lävi: {self.lavi():.0f}",
        ]
        for h in self.varavad.hoiatused():
            r.append(f"  ! {h}")
        for x in self.vastuolud():
            r.append(f"  !! {x}")
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
           adx_vaartus: float = 25.0, chop_vaartus: float = 50.0,
           hind_ule_ema200: bool = True,
           invalideerimine: str | None = None) -> Lugemine:
    voog, v_kate = _telg(v_komponendid, V_TAISKAAL)
    surve, s_kate = _telg(s_komponendid, S_TAISKAAL)
    varavad.on_btc = coin.strip().upper() in BTC_NIMED
    return Lugemine(coin, voog, surve, v_kate, s_kate, varavad,
                    volatiliteedi_reziim(atr_pertsentiil),
                    treni_reziim(adx_vaartus, chop_vaartus, hind_ule_ema200),
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
    # trendiv OHLC seeria — päris kasutuses tulevad need price_history'st
    hi, lo, cl = [], [], []
    hind = 100.0
    for i in range(60):
        hind *= 1.012 if i % 5 else 0.996
        hi.append(hind * 1.008); lo.append(hind * 0.992); cl.append(hind)

    g = Varavad(andmete_vanus_h=1.2, kaetud_oi_osakaal=0.88, btc_korrelatsioon=0.61)
    lug = arvuta("HYPE", v, s, g, atr_pertsentiil=0.83,
                 adx_vaartus=adx(hi, lo, cl), chop_vaartus=choppiness(hi, lo, cl),
                 hind_ule_ema200=True,
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

    # väikese OI-osakaaluga börsi ratio lülitub välja, mitte ei skaleeru nulli lähedale
    suur = long_short_kalle(2.5, 0.90)
    vaike = long_short_kalle(2.5, 0.10)
    assert suur.kehtiv and abs(suur.skoor) > 0.5
    assert not vaike.kehtiv and vaike.skoor == 0.0, "vale venue ei ole nõrk andmepunkt, ta ei ole andmepunkt"

    # ja see peab kaetuse arvestuses näha olema: S ühe komponendi peal ei anna lugemist
    s_telg = [funding_surve(0.0004, [0.0001] * 6 + [0.00012, 0.00008, 0.00011, 0.00009]),
              long_short_kalle(1.07, 0.112),
              Komponent("Basis", 0.0, 30, "ajalugu puudub", "", kehtiv=False)]
    lug = arvuta("X", [Komponent("v", 0.9, 100, "", "")], s_telg,
                 Varavad(), 0.5, invalideerimine="t")
    assert lug.surve_kate < 0.50, f"S peab näitama alla poole kaetust, sai {lug.surve_kate:.0%}"
    assert lug.kvadrant()[0] == "LUGEMIST EI OLE", "ühe komponendi peal seisev telg ei anna lugemist"
    ok += 1

    # MAD-z ei lähe üksikust ekstreemist katki
    aj = [1.0] * 11 + [50.0]
    assert abs(robust_z(1.0, aj)) < 1.0, "üks ekstreem ei tohi baastaset nihutada"
    ok += 1

    # kollapseerunud MAD: üle poole ajaloost identne, aga hälve on päris
    kordub = [0.0001] * 6 + [0.00012, 0.00008, 0.00011, 0.00009]
    z = robust_z(0.002, kordub)
    assert z > 5, f"20x funding-spike ei tohi lugeda z = 0, sai {z:.2f}"
    assert abs(robust_z(0.0001, kordub)) < 0.5, "mediaanil istuv väärtus jääb nulli lähedale"
    ok += 1

    # täiesti lame ajalugu: ulatust ei saa mõõta, aga suund on teada
    lame = [0.0002] * 10
    assert robust_z(0.0002, lame) == 0.0, "sama väärtus lameda ajaloo peal on 0"
    assert robust_z(0.01, lame) == 6.0, "kõrgem väärtus lameda ajaloo peal on küllastunud +"
    assert robust_z(0.0, lame) == -6.0, "madalam väärtus on küllastunud −"
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

    # puuduv komponent EI tohi kaetuse numbrit parandada
    ainult_funding = [Komponent("Funding", -1.0, 45, "", "")]  # basis ja L/S puuduvad hoopis
    val, kate = _telg(ainult_funding, S_TAISKAAL)
    assert abs(kate - 0.45) < 1e-9, f"kaetus peab olema 45%, sai {kate:.0%}"
    vana_moodi, vana_kate = _telg(ainult_funding)
    assert vana_kate == 1.0, "kaasa antute summa vastu mõõtes paistaks see 100% kaetud"
    lug = arvuta("HYPE", [Komponent("v", 0.9, 100, "", "")], ainult_funding,
                 Varavad(), 0.5, invalideerimine="t")
    assert lug.kvadrant()[0] == "LUGEMIST EI OLE", "ainult funding ei ole S-telg"
    ok += 1

    # kaetuse põrand: pool telge puudu = lugemist ei ole, ükskõik kui kõrge number
    poolik = arvuta("X",
                    [Komponent("on", 1.0, 35, "", ""),
                     Komponent("maas1", 0.0, 30, "", "", kehtiv=False),
                     Komponent("maas2", 0.0, 20, "", "", kehtiv=False),
                     Komponent("maas3", 0.0, 15, "", "", kehtiv=False)],
                    [Komponent("s", 0.8, 100, "", "")],
                    Varavad(), 0.5, invalideerimine="t")
    assert poolik.voog == 100.0, "üks komponent haarab telje — see osa ongi probleem"
    assert poolik.kvadrant()[0] == "LUGEMIST EI OLE", \
        "35% kaetusega ei tohi verdikti tulla, ükskõik kui kõrge V on"
    assert "V-teljel" in poolik.kvadrant()[1], "peab ütlema, KUMB telg on puudulik"

    # 65% kaetust on üle põranda ja lugemine tuleb
    piisav = arvuta("X",
                    [Komponent("a", 1.0, 35, "", ""), Komponent("b", 1.0, 30, "", ""),
                     Komponent("c", 0.0, 20, "", "", kehtiv=False),
                     Komponent("d", 0.0, 15, "", "", kehtiv=False)],
                    [Komponent("s", 0.8, 100, "", "")],
                    Varavad(), 0.5, invalideerimine="t")
    assert piisav.kvadrant()[0] != "LUGEMIST EI OLE", "65% kaetust peab lugemise andma"
    ok += 1

    # tühistuv telg ei ole neutraalne telg
    tyhistav = arvuta("X", [Komponent("a", 0.9, 100, "", "")],
                      [Komponent("Funding", -0.66, 45, "", ""),
                       Komponent("Basis", 0.93, 30, "", ""),
                       Komponent("L/S", 0.0, 25, "", "", kehtiv=False)],
                      Varavad(), 0.5, invalideerimine="t")
    v = tyhistav.vastuolud()
    assert v, f"funding −30 ja basis +28 peavad andma vastuolu, sai S={tyhistav.surve:.1f}"
    assert "ei ole ühel meelel" in v[0] and "Funding" in v[0] and "Basis" in v[0]

    # päriselt vaikne telg EI tohi vastuolu lippu saada
    vaikne = arvuta("X", [Komponent("a", 0.9, 100, "", "")],
                    [Komponent("Funding", 0.02, 45, "", ""),
                     Komponent("Basis", -0.03, 30, "", "")],
                    Varavad(), 0.5, invalideerimine="t")
    assert not vaikne.vastuolud(), "väikesed komponendid ei ole tühistus"

    # selge võitja EI ole tühistus
    selge = arvuta("X", [Komponent("a", 0.9, 100, "", "")],
                   [Komponent("Funding", 0.9, 45, "", ""),
                    Komponent("Basis", -0.4, 30, "", "")],
                   Varavad(), 0.5, invalideerimine="t")
    assert not selge.vastuolud(), "kui üks pool võidab selgelt, ei ole see tühistus"
    ok += 1

    # BTC enda peal ei ole korrelatsioon iseendaga näitaja
    v_btc = [Komponent("a", 0.9, 100, "", "")]
    s_btc = [Komponent("b", 0.5, 100, "", "")]
    btc = arvuta("BTC", v_btc, s_btc, Varavad(btc_korrelatsioon=1.0), 0.5,
                 invalideerimine="t")
    alt = arvuta("SOL", v_btc, s_btc, Varavad(btc_korrelatsioon=1.0), 0.5,
                 invalideerimine="t")
    assert "BTC ise" in btc.varavad.juhtiv_muutuja()
    assert not any("korrelatsioon" in x for x in btc.varavad.hoiatused()), \
        "BTC ei tohi saada hoiatust, et ta liigub BTC peale"
    assert alt.varavad.juhtiv_muutuja() == "BTC"
    assert any("korrelatsioon" in x for x in alt.varavad.hoiatused()), \
        "alt PEAB selle hoiatuse saama"
    ok += 1

    # vananenud andmed langetavad usaldusväärsust
    varske = Varavad(andmete_vanus_h=1.0)
    vana = Varavad(andmete_vanus_h=12.0)
    assert vana.varskus() < varske.varskus() == 1.0
    ok += 1

    # --- trendi režiim ---
    # puhas trend: iga küünal kõrgemal, kattuvust peaaegu pole
    thi, tlo, tcl = [], [], []
    x = 100.0
    for _ in range(60):
        x *= 1.02
        thi.append(x*1.003); tlo.append(x*0.997); tcl.append(x)
    # külgsuunaline: hind võngub sama vahemiku sees
    rhi, rlo, rcl = [], [], []
    for i in range(60):
        y = 100 + (2.0 if i % 2 else -2.0)
        rhi.append(y+1.5); rlo.append(y-1.5); rcl.append(y)

    a_trend, a_range = adx(thi, tlo, tcl), adx(rhi, rlo, rcl)
    c_trend, c_range = choppiness(thi, tlo, tcl), choppiness(rhi, rlo, rcl)
    assert a_trend > 25, f"puhas trend peab andma ADX > 25, sai {a_trend:.1f}"
    assert a_range < 20, f"võnkumine peab andma ADX < 20, sai {a_range:.1f}"
    assert c_trend < 38.2, f"puhas trend peab andma Chop < 38.2, sai {c_trend:.1f}"
    assert c_range > 61.8, f"võnkumine peab andma Chop > 61.8, sai {c_range:.1f}"
    ok += 1

    # VÕI-loogika: kumbki tingimus üksi viib külgsuunalisse
    assert treni_reziim(15, 40, True)[2], "madal ADX üksi peab andma külgsuunalise"
    assert treni_reziim(30, 70, True)[2], "kõrge Chop üksi peab andma külgsuunalise"
    assert not treni_reziim(30, 40, True)[2], "tugev ADX + madal Chop on trend"
    assert "üles" in treni_reziim(30, 40, True)[0]
    assert "alla" in treni_reziim(30, 40, False)[0]
    ok += 1

    # sama voog: trendis on lugemine, külgsuunas mitte
    v1 = [Komponent("a", 0.30, 100, "", "")]
    s1 = [Komponent("b", 0.50, 100, "", "")]
    trendis = arvuta("X", v1, s1, Varavad(), 0.5, 30, 40, True, invalideerimine="t")
    kulgs  = arvuta("X", v1, s1, Varavad(), 0.5, 15, 70, True, invalideerimine="t")
    assert trendis.lavi() == 25.0 and kulgs.lavi() == 40.0
    assert trendis.kvadrant()[0] != "LUGEMIST EI OLE", "voog 30 trendis peab andma lugemise"
    assert kulgs.kvadrant()[0] == "LUGEMIST EI OLE", "voog 30 külgsuunas jääb alla läve"
    ok += 1

    # režiim ja volatiliteet on eraldi teljed — sama režiim, eri volatiliteet
    kokku = arvuta("X", v1, s1, Varavad(), 0.10, 15, 70, True, invalideerimine="t")
    lai   = arvuta("X", v1, s1, Varavad(), 0.95, 15, 70, True, invalideerimine="t")
    assert kokku.trend[0] == lai.trend[0] == "külgsuunaline"
    assert kokku.reziim[0] == "kokku surutud" and lai.reziim[0] == "laienenud"
    ok += 1

    print(f"{ok}/18 testiplokki OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    else:
        _demo()
