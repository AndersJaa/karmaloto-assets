#!/usr/bin/env python3
"""Arvutab VSI lugemise ühest JSON-failist ja kirjutab telefonis avatava lehe.

    python3 run_vsi.py sisend.json --valja lugemine.html

Sisend on TOORNUMBRID nii, nagu need CoinGlassist tulevad — protsendid
protsentidena (4.2 tähendab 4.2%), USD-summad dollarites. Teisendused teeb
skript ise, et kutsuja ei peaks meeles pidama, kus on murd ja kus protsent.

Väljund on kaks asja korraga:
  1. tekstilugemine stdout'i — see läheb vestlusesse
  2. HTML-leht, mille väljad on ette täidetud, aga jäävad muudetavaks

Puuduv väli peatab töö ja ütleb, MIS puudub — vaikne nulliga asendamine
annaks lugemise, mis näeb terve välja, aga on vale.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import vsi  # noqa: E402


# Basis ja spot/ETF voog EI ole siin. Kummalgi on mündid, kus neid lihtsalt ei
# eksisteeri — HYPE-l pole kvartalifutuuri, ETF-vood on ainult BTC-l ja ETH-il.
# Nende nõudmine tähendaks, et selliste müntide kohta ei tule lugemist kunagi.
# Nende puudumine on juba kaetud: kaal jaotub ümber ja kaetuse põrand otsustab,
# kas telge saab veel lugeda.
# Väljad, milleta lugemist ei tule. Basis, spot/ETF voog ja long/short EI ole
# siin: kummalgi on mündid, kus neid lihtsalt ei eksisteeri (HYPE-l pole
# Hyperliquidi ratiot ega ETF-voogu). Nende puudumine on juba kaetud — kaal
# jaotub ümber ja kaetuse põrand otsustab, kas telge saab veel lugeda.
KOHUSTUSLIK = [
    "coin", "hinna_muutus_pct", "oi_muutus_pct", "neto_taker_usd", "maht_usd",
    "long_liq_usd", "short_liq_usd", "oi_usd",
    "funding_nyyd_pct", "funding_ajalugu_pct",
    "andmete_vanus_h", "kaetud_oi_osakaal",
    "atr_pertsentiil", "adx", "chop", "hind_ule_ema200",
    "invalideerimine",
]

# turg.json plokk.väli  ->  siseselt kasutatav lame nimi.
# Andmeleping hoiab välju plokkides; see moodul on kirjutatud lamedale kujule.
# Tõlge käib ühes kohas, et kummalgi poolel ei peaks teist meeles pidama.
LEPINGU_TEED = {
    "meta.coin": "coin",
    "meta.ajatempel": "ajatempel",
    "hind.muutus_aknas_pct": "hinna_muutus_pct",
    "voog.oi_muutus_pct": "oi_muutus_pct",
    "voog.neto_taker_usd": "neto_taker_usd",
    "voog.maht_usd": "maht_usd",
    "voog.long_liq_usd": "long_liq_usd",
    "voog.short_liq_usd": "short_liq_usd",
    "voog.oi_usd": "oi_usd",
    "voog.spot_voog_usd": "spot_voog_usd",
    "surve.funding_pct": "funding_nyyd_pct",
    "surve.funding_ajalugu_pct": "funding_ajalugu_pct",
    "surve.basis_pct": "basis_nyyd_pct",
    "surve.basis_ajalugu_pct": "basis_ajalugu_pct",
    "surve.long_short_ratio": "long_short_ratio",
    "surve.long_short_bors_kate": "borsi_oi_osakaal",
    "reziim.btc_korrelatsioon": "btc_korrelatsioon",
    "reziim.atr_pertsentiil": "atr_pertsentiil",
    "reziim.adx": "adx",
    "reziim.chop": "chop",
    "reziim.hind_ule_ema200": "hind_ule_ema200",
    # kaetus tuleb AGREGEERITUD katvusest, mitte taker-börside omast:
    # taker-piirang puudutab taker-komponenti, mitte tervet lugemist
    "kate.agregeeritud_kate": "kaetud_oi_osakaal",
}


def _vota(d: dict, tee: str):
    """Loeb 'plokk.väli' tee. Tagastab None, kui teed ei ole."""
    osa = d
    for samm in tee.split("."):
        if not isinstance(osa, dict) or samm not in osa:
            return None
        osa = osa[samm]
    return osa


def lepingust(d: dict) -> dict:
    """turg.json (plokkidega) -> lame kuju. Juba lame sisend läheb läbi muutmata.

    Vanuse arvutab ajatemplist ise: andmete_vanus_h ei ole lepingus väli, vaid
    tuletis, ja tuletist ei salvestata kaks korda.
    """
    if "meta" not in d:
        return d  # vana lame kuju, nt käsitsi kokku pandud JSON

    lame = {}
    for tee, nimi in LEPINGU_TEED.items():
        v = _vota(d, tee)
        if v is not None:
            lame[nimi] = v

    stamp = lame.pop("ajatempel", None)
    if stamp:
        try:
            t = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            vanus = (datetime.now(timezone.utc) - t).total_seconds() / 3600
            if vanus < -0.05:
                # Ajatempel on tulevikus — kella silt on vale, tõenäoliselt on
                # kirjutatud kohalik aeg UTC-na. Andmed ise ei ole sellest katki,
                # aga VANUST ei saa arvutada. Lugemist ei blokeerita: label-viga
                # ei ole andmeviga. Küll aga öeldakse see valjult välja, sest
                # vaikselt nulliga edasi minek tähendaks, et vanusevärav on
                # välja lülitatud ja keegi ei tea seda.
                lame["_ajatempli_viga"] = (
                    f"meta.ajatempel on {abs(vanus):.1f}h TULEVIKUS ({stamp}). "
                    "Tõenäoliselt kirjutatud kohalik aeg UTC sildiga. "
                    "VANUS ON TEADMATA — vanusevärav ei tööta, kuni allikas on parandatud."
                )
                lame["andmete_vanus_h"] = 0.0
            else:
                lame["andmete_vanus_h"] = round(vanus, 2)
        except ValueError:
            raise SystemExit(f"meta.ajatempel ei ole loetav kuupäev: {stamp}")

    lame["kontekst"] = d.get("kontekst", {})
    lame["kate"] = d.get("kate", {})
    lame["hind"] = d.get("hind", {})
    return lame


def kontrolli(d: dict) -> None:
    noutud = list(KOHUSTUSLIK)
    if str(d.get("coin", "")).strip().upper() in vsi.BTC_NIMED:
        # BTC korrelatsioon iseendaga on 1.0 ega ütle midagi — ei nõua seda
        noutud = [x for x in noutud if x != "btc_korrelatsioon"]
    puudu = [k for k in noutud if k not in d]
    if puudu:
        raise SystemExit(
            "Puuduvad väljad: " + ", ".join(puudu) +
            "\n\nIga väli peab tulema päris kutsest. Kui mõnd andmerida ei saanud, "
            "ära pane nulli — jäta väli välja ja see viga ütleb, mis puudu on."
        )
    if not str(d["invalideerimine"]).strip():
        raise SystemExit(
            "Invalideerimine on tühi. Ilma täpse hinna või tingimuseta, mis lugemise "
            "valeks tunnistab, lugemist ei anta."
        )
    if len(d["funding_ajalugu_pct"]) < 8:
        raise SystemExit(
            "Funding vajab vähemalt 8 ajaloopunkti, et mediaan/MAD oleks "
            "tähenduslik. Tõmba pikem aken."
        )
    if "basis_nyyd_pct" in d and len(d.get("basis_ajalugu_pct", [])) < 8:
        raise SystemExit(
            "Basis on antud, aga ajalugu on lühem kui 8 punkti. Kas tõmba pikem "
            "aken või jäta basis üldse välja — poolik ajalugu annab vale z-skoori."
        )


def ehita(d: dict) -> vsi.Lugemine:
    v = [
        vsi.oi_hinna_kvadrant(d["hinna_muutus_pct"] / 100, d["oi_muutus_pct"] / 100),
        vsi.taker_cvd(d["neto_taker_usd"], d["maht_usd"]),
        vsi.likvideerimised(d["long_liq_usd"], d["short_liq_usd"], d["oi_usd"]),
    ]
    # spot/ETF voog puudutab ainult BTC-d ja ETH-i — mujal jääks see valekindluseks
    if "spot_voog_usd" in d:
        v.append(vsi.spot_voog(d["spot_voog_usd"], d["oi_usd"]))

    s = [
        vsi.funding_surve(d["funding_nyyd_pct"] / 100,
                          [x / 100 for x in d["funding_ajalugu_pct"]]),
    ]
    # long/short puudub, kui domineeriv börs ratiot ei anna — alumisele ei astuta
    if "long_short_ratio" in d and "borsi_oi_osakaal" in d:
        s.append(vsi.long_short_kalle(d["long_short_ratio"], d["borsi_oi_osakaal"]))
    # basis puudub mündil, millel kvartalifutuuri ei ole
    if "basis_nyyd_pct" in d and d.get("basis_ajalugu_pct"):
        s.append(vsi.basis_surve(d["basis_nyyd_pct"] / 100,
                                 [x / 100 for x in d["basis_ajalugu_pct"]]))

    varavad = vsi.Varavad(
        andmete_vanus_h=d["andmete_vanus_h"],
        kaetud_oi_osakaal=d["kaetud_oi_osakaal"],
        btc_korrelatsioon=d.get("btc_korrelatsioon", 0.0),
    )
    return vsi.arvuta(d["coin"], v, s, varavad,
                      atr_pertsentiil=d["atr_pertsentiil"],
                      adx_vaartus=d["adx"], chop_vaartus=d["chop"],
                      hind_ule_ema200=bool(d["hind_ule_ema200"]),
                      invalideerimine=d["invalideerimine"])


def preset(d: dict) -> dict:
    """Lehe väljad protsentides — täpselt nii, nagu inimene neid CoinGlassil näeb."""
    return {
        "silt": f"VSI · {d['coin']} · {d.get('ajatempel', 'ajatempel puudu')}",
        "vaartused": {
            "dp": d["hinna_muutus_pct"], "doi": d["oi_muutus_pct"],
            "cvd": round(d["neto_taker_usd"] / 1e6, 2),
            "vol": round(d["maht_usd"] / 1e6, 1),
            "ll": round(d["long_liq_usd"] / 1e6, 2),
            "sl": round(d["short_liq_usd"] / 1e6, 2),
            "oi": round(d["oi_usd"] / 1e6, 1),
            "flow": round(d["spot_voog_usd"] / 1e6, 2) if "spot_voog_usd" in d else "",
            "fnow": d["funding_nyyd_pct"],
            "fhist": " ".join(str(x) for x in d["funding_ajalugu_pct"]),
            "bnow": d.get("basis_nyyd_pct", ""),
            "bhist": " ".join(str(x) for x in d.get("basis_ajalugu_pct", [])),
            # tühjaks jäetud väli tähendab lehel "ei kohaldu", mitte nulli
            "ls": d.get("long_short_ratio", ""),
            "share": round(d["borsi_oi_osakaal"] * 100, 1) if "borsi_oi_osakaal" in d else "",
            "age": d["andmete_vanus_h"],
            "cov": round(d["kaetud_oi_osakaal"] * 100, 1),
            "btc": d.get("btc_korrelatsioon", 0.0),
            "atr": d["atr_pertsentiil"],
            "adx": d["adx"], "chop": d["chop"],
            "ema": "1" if d["hind_ule_ema200"] else "0",
            "inval": d["invalideerimine"],
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="VSI lugemine JSON-sisendist")
    ap.add_argument("sisend", help="JSON toornumbritega")
    ap.add_argument("--valja", default="vsi-lugemine.html", help="väljundleht")
    ap.add_argument("--invalideerimine", default=None,
                    help="täpne hind või tingimus, mis lugemise valeks tunnistab. "
                         "Andmefailis seda välja EI OLE ja see on meelega: "
                         "invalideerimine on otsus, mitte mõõtmine.")
    args = ap.parse_args()

    d = lepingust(json.loads(Path(args.sisend).read_text(encoding="utf-8")))
    if args.invalideerimine:
        d["invalideerimine"] = args.invalideerimine
    kontrolli(d)
    lugemine = ehita(d)
    if d.get("_ajatempli_viga"):
        print("\n  !! " + d["_ajatempli_viga"] + "\n")
    print(lugemine.render())
    if d.get("_ajatempli_viga"):
        print("\n  !! " + d["_ajatempli_viga"])

    mall = Path(__file__).parent.parent / "assets" / "vsi-kaart.html"
    leht = mall.read_text(encoding="utf-8")
    süst = ("<script>window.VSI_PRESET = "
            + json.dumps(preset(d), ensure_ascii=False) + ";</script>\n")
    # preset peab jõudma lehele enne peaskripti, muidu update() jookseb tühjadega
    leht = leht.replace("<style>", süst + "<style>", 1)
    Path(args.valja).write_text(leht, encoding="utf-8")
    print(f"\n  Leht kirjutatud: {args.valja}")


if __name__ == "__main__":
    main()
