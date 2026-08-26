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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import vsi  # noqa: E402


# Basis ja spot/ETF voog EI ole siin. Kummalgi on mündid, kus neid lihtsalt ei
# eksisteeri — HYPE-l pole kvartalifutuuri, ETF-vood on ainult BTC-l ja ETH-il.
# Nende nõudmine tähendaks, et selliste müntide kohta ei tule lugemist kunagi.
# Nende puudumine on juba kaetud: kaal jaotub ümber ja kaetuse põrand otsustab,
# kas telge saab veel lugeda.
KOHUSTUSLIK = [
    "coin", "hinna_muutus_pct", "oi_muutus_pct", "neto_taker_usd", "maht_usd",
    "long_liq_usd", "short_liq_usd", "oi_usd",
    "funding_nyyd_pct", "funding_ajalugu_pct",
    "long_short_ratio", "borsi_oi_osakaal",
    "andmete_vanus_h", "kaetud_oi_osakaal", "btc_korrelatsioon",
    "atr_pertsentiil", "adx", "chop", "hind_ule_ema200",
    "invalideerimine",
]


def kontrolli(d: dict) -> None:
    noutud = list(KOHUSTUSLIK)
    if str(d.get("coin", "")).strip().upper() in vsi.BTC_NIMED:
        # BTC korrelatsioon iseendaga on 1.0 ega ütle midagi — ei nõua seda
        noutud.remove("btc_korrelatsioon")
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
        vsi.long_short_kalle(d["long_short_ratio"], d["borsi_oi_osakaal"]),
    ]
    # basis puudub mündil, millel kvartalifutuuri ei ole — kaal jaotub ümber ja
    # kaetuse põrand ütleb, kas S-telge saab veel lugeda
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
            "ls": d["long_short_ratio"],
            "share": round(d["borsi_oi_osakaal"] * 100, 1),
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
    args = ap.parse_args()

    d = json.loads(Path(args.sisend).read_text(encoding="utf-8"))
    kontrolli(d)
    lugemine = ehita(d)
    print(lugemine.render())

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
