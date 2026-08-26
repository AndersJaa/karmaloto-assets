# Turuanalüüsi süsteem

Kolm osa, mis vastavad kolmele eri küsimusele. Iga osa on kasutu teise küsimuse peal.

## Avaldatud lehed

Need kolm linki on **püsivad** — uuendamine ei muuda URL-i. Telefonis saab need
avaekraanile lisada.

| Leht | Mille jaoks | Link |
|---|---|---|
| **Turu seaduspärasuste koond** | 40+ turumustrit ühel kujul, usaldusväärsuse hindega 1–5 | https://claude.ai/code/artifact/35beddc7-d71d-455c-9b65-51b1bd87eb50 |
| **Voog–Surve kaart** | Interaktiivne VSI tööriist — numbrid sisse, lugemine välja | https://claude.ai/code/artifact/8b28be4a-259d-4ae0-8a4b-83df8492a52e |
| **Masinaruum** | Kogu süsteemi seletuskiri: väravad, ahel, leitud vead | https://claude.ai/code/artifact/d76cbc64-e3c9-42e2-acc8-6cae25678d89 |

Kõik avaldatud lehed on ka galeriis: `claude.ai/code/artifacts`

## Failid

| Fail | Mis ta on |
|---|---|
| `turu-seadusparasused.md` | Alustabel — millest VSI komponendid valiti |
| `masinaruum.html` | Seletuskirja lähtefail |
| `vsi/vsi.py` | Arvutusmoodul: kaks telge, väravad, `adx()`, `choppiness()` |
| `vsi/skanner.py` | Coini otsimine — äärmused ja jätk |
| `vsi/vsi-kaart.html` | Interaktiivse tööriista lähtefail |
| `vsi/README.md` | VSI ja skänneri tehniline kirjeldus |
| `../.claude/skills/vsi/` | Pakendatud skill koos `run_vsi.py`-ga |

## Testid

```bash
python3 vsi/vsi.py --test        # 17 testiplokki
python3 vsi/skanner.py --test    # 9 testiplokki
```

## Mis jookseb väljaspool seda repot

| Tükk | Kus | Millal |
|---|---|---|
| `vsi_fetch.py` | Andersi Mac, `~/Documents/Claude/Projects/Trade/` | iga tund, launchd |
| `market_data.py` | sama koht | iga tund, launchd |
| Positsiooni päevaraport | Claude Routine, pilves | iga päev 13:00 |
| `vsi` skill | Andersi konto | iga kord, kui küsib |

CoinGlass on **lokaalne** MCP-server Andersi Macis. Pilv teda ei näe — sellepärast
käib ahel läbi Google Drive'i (`TradeData/vsi_input.json`). Kataloogis hostitud
CoinGlassi ühendust ei ole olemas, kontrollitud.
