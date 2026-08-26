---
name: vsi
description: Arvutab VSI (Voog-Surve indeks) — kaheteljelise positsioneerimislugemise CoinGlassi andmetest — ja avaldab selle artifact-lehena, mida saab telefonis avada. Kasuta ALATI, kui Anders küsib mõne mündi kohta "mis seis on", "jooksuta VSI", "voog-surve", "kas rahvahulk on longis/shortis", "kas see on ülekuumenenud", küsib positsioneerimise, fundingu, OI või likvideerimiste lugemist, saadab CoinGlassi ekraanipildi ja tahab tõlgendust, või tahab lugemist telefonis näha. Kasuta ka siis, kui ta ei ütle sõna "VSI" — iga suunapäring ühe mündi kohta käib läbi selle.
---

# VSI — Voog-Surve indeks

Kaheteljeline lugemine, mis koondab ainult mehaaniliselt mõõdetavad näitajad.
Struktuur, Elliott ja mustrid siia sisse ei tule — need on tõlgendus ja rikuksid
numbri, mis peab olema objektiivne.

| Telg | Mida ütleb | Komponendid ja kaalud |
|---|---|---|
| **V — voog** | mida raha PRAEGU teeb | OI+hind 35 · taker CVD 30 · likvideerimised 20 · spot/ETF 15 |
| **S — surve** | kui ühel pool rahvahulk on | funding 45 · basis 30 · long/short 25 |

Telgi ei liideta. Tõus madala survega ja tõus kõrge survega on vastandid, kuigi
mõlemal on V positiivne — üks number kaotaks selle vahe ära.

Kvadrandid: **puhas tõus** (V+ S−) · **ülekuumenenud tõus** (V+ S+) ·
**longide väljasurumine** (V− S+) · **shortide kütus** (V− S−).
Kui |V| jääb alla läve, siis lugemist ei ole ja seda öeldakse otse.

## Töövoog

### 1. Tõmba andmed — enne ühtki väidet

Andmete tõmbamist juhib **market-data-check** skill. Järgi seda: börsi kaal
(`oi_distribution by_exchange`) käib alati esimesena, sest see otsustab, kelle
andmed on üldse tähenduslikud, ja `taker coin_history` tuleb ristkontrollida
`price_history` mahuga.

Kui mõni kutse annab vea — **tsiteeri viga sõna-sõnalt** ja küsi ekraanipilti.
Ära asenda mudeliga, ära asenda naaberbörsiga.

### 2. Pane numbrid JSON-i

Loo fail (nt `/tmp/vsi-HYPE.json`). Iga väli tuleb päris kutsest — kui mõnd ei
saanud, **jäta väli välja**, ära pane nulli. Skript ütleb siis, mis puudu on.
Null näeb välja nagu andmed ja annab lugemise, mis on vaikselt vale.

| JSON-väli | Kust | Ühik |
|---|---|---|
| `coin`, `ajatempel` | — | tekst |
| `hinna_muutus_pct` | `price_history`, sama aken mis OI-l | % |
| `oi_muutus_pct` | `oi_history action=aggregated` | % |
| `neto_taker_usd` | `taker action=coin_history`, ost − müük | USD |
| `maht_usd` | `price_history` sama akna maht | USD |
| `long_liq_usd`, `short_liq_usd` | `liq_history action=aggregated` | USD |
| `oi_usd` | `oi_history action=aggregated`, viimane | USD |
| `spot_voog_usd` | päevased netovood — **ainult BTC/ETH, mujal jäta välja** | USD |
| `funding_nyyd_pct`, `funding_ajalugu_pct` | `funding_history action=oi_weighted`, ≥ 8 punkti | % |
| `basis_nyyd_pct`, `basis_ajalugu_pct` | kvartalifutuur vs spot, ≥ 8 punkti | % |
| `long_short_ratio` | `long_short action=global` | suhtarv |
| `borsi_oi_osakaal` | `oi_distribution by_exchange`, selle börsi osa | 0…1 |
| `andmete_vanus_h` | vanim kasutatud andmepunkt | tundi |
| `kaetud_oi_osakaal` | kui suurt osa OI-st andmed katavad | 0…1 |
| `btc_korrelatsioon` | coin vs BTC samas aknas | −1…1 |
| `atr_pertsentiil` | ATR praegu vs oma ajalugu | 0…1 |
| `adx`, `chop` | `price_history` OHLC-st; `vsi.adx()` ja `vsi.choppiness()` arvutavad | arv |
| `hind_ule_ema200` | hind vs EMA200 | true/false |
| `invalideerimine` | **sinu sõnastatud** — täpne hind või tingimus | tekst |

Protsendid protsentidena: `4.2` tähendab 4.2%, mitte 0.042. Skript teisendab ise.

**Ükski münt pole eelistatud — `coin` ütleb, mida hinnatakse.** Kaks erisust:
BTC ja ETH puhul lisa `spot_voog_usd` (ETF- ja spot-vood on ainult neil kahel);
mujal jäta see väli välja ja kaal jaotub teiste komponentide vahel ümber.
BTC enda peal ei ole `btc_korrelatsioon` nõutud — korrelatsioon iseendaga on 1.0
ja ütleks lugemises tautoloogia, et BTC liigub BTC peale.

### 3. Jooksuta

```bash
python3 scripts/run_vsi.py /tmp/vsi-HYPE.json --valja /tmp/vsi-HYPE.html
```

See prindib tekstilugemise ja kirjutab lehe, mille väljad on ette täidetud, aga
jäävad muudetavaks.

### 4. Avalda

Avalda `/tmp/vsi-HYPE.html` Artifact-tööriistaga ja anna link. Nii saab Anders
lugemise telefonis lahti teha ja seal kohapeal numbreid muuta, kui tahab "aga
mis siis kui" läbi mängida.

Kui sama mündi lugemine on juba varem avaldatud, **avalda sama URL-i peale**
(`url` parameeter), et link jääks samaks — muidu tekib iga korraga uus leht ja
telefonis olev järjehoidja jääb vana peale.

### 5. Vasta vestluses

Anna tekstilugemine ja link. Ütle **üks selge seisukoht**, mitte stsenaariumide
nimekiri. Kui ei tea, ütle see otse.

## Kui CoinGlassi ühendust ei ole

See juhtub — mõnes aknas või ajastatud ülesandes pole CoinGlassi ühendust kaasas.
**Siis VSI lugemist ei tule.** Ütle see otse ja ütle ka, mis puudu on.

Anders'i `market_snapshot.json` (Macis, peegeldub Google Drive'i kausta `TradeData`)
**ei asenda seda**. Ta annab positsiooni mündi kohta `markPx`, `funding`, `oi_trend`,
`whales` ja `crowding` — see katab VSI seitsmest komponendist heal juhul kaks, ja
kolme lõksuga:

- `openInterest_units` on **COIN-ÜHIKUTES, mitte USD-s**. Likvideerimiste müravärav
  ja OI-hinna komponent eeldavad USD-d. Ühikute segamini ajamine annab vaikselt
  jama, mis näeb välja nagu arv.
- `funding` on **TUNNINE**, mitte 8-tunnine, ja ainult Hyperliquidist — mitte
  `oi_weighted` mitme börsi peale.
- Üks snapshot on **üks ajapunkt**. Funding ja basis vajavad z-skoori jaoks ≥ 8
  vaatlust. Ühest failist neid ei tule.

Mida snapshot **hästi** annab: õige mark price tema enda venue'ilt (mitte asendus-
börsilt), OI trendi suuna ja valaskannu. Kasuta seda hinna ja konteksti jaoks —
ja ütle välja, et see on kontekst, mitte lugemine.

Kaetuse põrand on koodis: kui telje kaalust on kaetud alla poole, keeldub
`kvadrant()` verdiktist ja ütleb, kumb telg on puudulik. Ühest ellujäänud
komponendist saaks muidu uhke V = 100, mille kõrval madal usaldusväärsuse
protsent on kõrvalmärkus, mida keegi ei loe.

## Reeglid, mis ei ole soovitused

**Invalideerimine on kohustuslik.** Skript keeldub ilma selleta töötamast, sest
lugemine ilma invalideerimiseta ei ole lugemine. Sõnasta see ise andmete põhjal —
täpne hind või tingimus, mis lugemise valeks tunnistab.

**Iga arv kannab oma allikat.** Väljundis on iga komponendi juures kirjas, mis
kutse ta andis. Kui mõne arvu kohta ei oska öelda, kust ta tuli, siis ta sinna ei
kuulu.

**„Mul pole andmeid" ilma endpointi kutsumata on vale väide, mitte ettevaatlikkus.**
Kutsu enne, kui ütled, et midagi pole.

**Ostu- ja müügisoovitusi ei anta.** Andmed, tasemed, stsenaariumid — otsus on tema.
Positsiooni suurust ei puuduta.

**Tema positsioon ei tohi lugemist kallutada.** Kui ta on mündis sees, hinnatakse
graafikut täpselt sama moodi, nagu ta ei oleks.

## Mida väravad ise ära teevad

Neid ei pea käsitsi jälgima — skript teeb ja kirjutab välja:

- **Likvideerimised alla 0.5% OI-st** lülituvad välja kui müra ja nende kaal
  jaotub teiste komponentide vahel ümber. 90/10 jaotus 0.1% pealt ei ole kaskaad.
- **Long/short skaleeritakse börsi OI-osakaaluga.** Alla ~25% katvusega börsi
  ratio ei ole rahvahulk.
- **Külgsuunaline režiim** (ADX < 20 VÕI Chop > 61.8) tõstab voo läve 25-lt 40-le,
  sest seal on valemurd reegel, mitte erand.
- **BTC korrelatsioon ≥ 0.80** paneb lipu, et juhtiv muutuja on BTC, mitte münt ise.
- **Vananenud andmed ja puudulik katvus** langetavad usaldusväärsuse kordajat.

## Failid

- `scripts/vsi.py` — arvutusmoodul, sisaldab ka `adx()` ja `choppiness()`
- `scripts/run_vsi.py` — JSON sisse, lugemine ja leht välja
- `assets/vsi-kaart.html` — lehe mall

Mooduli enda testid: `python3 scripts/vsi.py --test` (16 testiplokki).
