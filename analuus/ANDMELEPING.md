# Andmeleping — `turg.json`

Üks fail. Üks ajatempel. Üks aken. Iga väli kannab allikat.

## Miks see olemas on

27.08.2026 andsid kolm süsteemi sama mündi kohta sama ajaga kolm eri vastust:

| Näitaja | Päevaraport 13:18 | Hype Positsioon 17:00 | CoinGlass 20:15 |
|---|---|---|---|
| Funding | positiivne | **−0,1466%/päev** | — |
| Vaalad | **7/7 short** | **6 positsiooni, 5/1** | long 4,57B / short 5,22B |
| Long/short | 1,21 (Binance) | — | **1,89** (Hyperliquid) |

Ükski neist ei olnud vale. Nad olid **eri asjad sama nime all** — eri aken, eri
börs, eri ühik. Selle lepingu ainus ülesanne on see võimatuks teha.

## Kolm reeglit, millest kõik muu tuleneb

**1. Ükski tükk ei arvuta numbrit, mis on juba failis olemas.**
Kui vaalade arvu on vaja, tuleb see failist. Mitte uuest kutsest, mis annab
teise vastuse. Uus kutse tähendab uut arvu ja uus arv tähendab vastuolu.

**2. Igal väljal on täpselt üks ühik ja üks aken, mis on siin kirjas.**
Funding ei ole kord %/h ja kord %/päev. Kui kuskil on vaja teist esitust,
teisendatakse **kuvamisel**, mitte salvestamisel.

**3. Puuduv väli jäetakse välja, mitte ei nullita.**
Null näeb välja nagu mõõtmine. Puuduv väli ütleb ausalt, et mõõtmist ei olnud.

## Struktuur

```
turg.json
├── meta          millal, mille kohta, mis versioon
├── hind          mark price ja liikumine
├── voog          mida raha teeb   → VSI V-telg
├── surve         kus rahvahulk on → VSI S-telg
├── reziim        trend vs külgsuunaline, volatiliteet
├── kontekst      vaalad, likvideerimiskaart, BTC — ei lähe VSI-sse
└── kate          kui suurt osa turust iga plokk katab
```

### meta

| Väli | Ühik | Reegel |
|---|---|---|
| `ajatempel` | ISO 8601, UTC | Kogu faili kirjutamise hetk. **Üks kõigile.** |
| `coin` | tekst | Sümbol, nt `HYPE` |
| `aken` | tekst | `h4×6` — kõik voo väljad sellest aknast |
| `versioon` | arv | Selle lepingu versioon; muutub, kui väli lisandub või tähendus muutub |

Kui mõni allikas on vanem kui `ajatempel`, on selle välja kõrval oma
`_vanus_h`. Ilma selleta eeldatakse, et väli on failiga sama vana.

### hind

| Väli | Ühik | Allikas |
|---|---|---|
| `mark` | USD | **Hyperliquid** — Andersi venue. Mitte asendus |
| `muutus_24h_pct` | % | sama venue |
| `muutus_aknas_pct` | % | sama venue, `meta.aken` |

### voog → V-telg

| Väli | Ühik | Allikas |
|---|---|---|
| `oi_usd` | USD | `oi_history aggregated`, viimane |
| `oi_muutus_pct` | % | sama, `meta.aken` |
| `neto_taker_usd` | USD | `taker coin_history`, ost − müük |
| `maht_usd` | USD | **samad börsid mis taker** — muidu jagatakse kolme börsi neto kümne börsi mahuga |
| `long_liq_usd`, `short_liq_usd` | USD | `liq_history aggregated` |
| `spot_voog_usd` | USD | ainult BTC ja ETH; mujal **väli puudub** |

### surve → S-telg

| Väli | Ühik | Allikas |
|---|---|---|
| `funding_pct` | **% / 8h**, oi_weighted | Üks ühik. Kuvamisel võib teisendada |
| `funding_ajalugu_pct` | sama ühik, ≥ 8 punkti | Vajalik mediaan/MAD jaoks |
| `basis_pct` | % annualiseeritud | Puudub, kui kvartalifutuuri pole |
| `basis_ajalugu_pct` | sama, ≥ 8 punkti | |
| `long_short_ratio` | suhtarv | **Domineerivalt börsilt.** Kui see börs ei anna, väli **puudub** — Binance'i 11% ei esitata rahvahulgana |
| `long_short_bors` | tekst | Mis börsilt ratio tuli |
| `long_short_bors_kate` | 0…1 | Selle börsi OI osakaal |

### reziim

| Väli | Ühik | Allikas |
|---|---|---|
| `adx` | arv | Wilder(14,14), `meta.aken` küünlad |
| `chop` | arv | Choppiness(14) |
| `atr_pertsentiil` | 0…1 | ATR14 vs oma ajalugu |
| `hind_ule_ema200` | tõeväärtus | |
| `btc_korrelatsioon` | −1…1 | Sama aken. BTC enda puhul **väli puudub** |

### kontekst — EI lähe VSI-sse

Need on lugemiseks ja kuvamiseks, mitte indeksi sisendiks.

| Väli | Reegel |
|---|---|
| `vaalad.positsioone` | Üks definitsioon: Hyperliquidi leaderboard skann |
| `vaalad.short`, `vaalad.long` | Arvud, mille summa = `positsioone` |
| `vaalad.neto_usd` | Netonotionaal |
| `vaalad.skanni_aeg` | Oma ajatempel — skann ei käi iga tund |
| `likvideerimiskaart.tasemed` | Nimekiri: hind, USD, kontosid |
| `likvideerimiskaart.baashind` | Mis hinnaga kaart arvutati |
| `likvideerimiskaart.nihe_pct` | Praegune hind vs baashind. Üle 2% → märgi |
| `btc.hind`, `btc.muutus_24h_pct` | |

**Vaalade arv tuleb ainult siit.** Kui leht näitab „6 positsiooni" ja raport
„7/7", siis üks neist ei lugenud failist.

### kate

| Väli | Ühik | Mida tähendab |
|---|---|---|
| `agregeeritud_kate` | 0…1 | Kui suurt osa OI-st katavad agregeeritud allikad (OI, funding, liq). Tavaliselt ~1.0 |
| `taker_kate` | 0…1 | Kui suurt osa OI-st katavad taker-börsid. HYPE-l ~0,24 |
| `borside_arv` | arv | Mitmel börsil OI > 0 |

Need **kaks katet on eraldi meelega**. Varem läks taker-börside osakaal
üldiseks kordajaks ja surus HYPE usaldusväärsuse struktuurselt 17% juurde —
kuigi funding, basis ja likvideerimised olid täies katvuses. Taker-kate
puudutab taker-komponenti, mitte tervet lugemist.

## Mis loeb faili, mis mitte

| Tükk | Roll |
|---|---|
| Maci tõmbeskript | **kirjutab** — ainus, kes kirjutab |
| `vsi.py` / `run_vsi.py` | loeb, arvutab V ja S |
| Positsioonileht | loeb, kuvab |
| Päevaraport | loeb, kirjutab teksti |

Ainult üks kirjutaja. Kõik teised loevad. See on kogu lepingu mõte.
