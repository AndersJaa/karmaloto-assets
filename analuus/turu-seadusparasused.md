# Turu seaduspärasuste koondtabel

Üks koondnimekiri kõigest, mis turgudel korduvalt kordub — Elliott ja Fibonacci on siin
lihtsalt kaks rida paljudest, mitte eraldi süsteem. Kõik on viidud ühele kujule:
**mis see on → mis ajaraamis → kuidas mõõta → kui usaldusväärne → kuidas see läbi kukub.**

Usaldusväärsus on hinnatud skaalal 1–5, kus:

- **5** = mehaaniline, mõõdetav, ei sõltu tõlgendusest (nt funding, OI muutus, likvideerimised)
- **4** = statistiliselt tugev, aga vajab konteksti
- **3** = töötab režiimis, kukub režiimivahetusel läbi
- **2** = subjektiivne, tagantjärele alati "õige", ette harva
- **1** = narratiiv, mitte signaal

Reegel läbivalt: **iga rida allpool on kontekst, mitte kauplemissignaal.** Signaal tekib alles
siis, kui mitu sõltumatut kategooriat (struktuur + tase + positsioneerimine + likviidsus)
osutavad samasse kohta.

---

## A. Struktuur ja laineloogika

| Seaduspärasus | Mis see on | Ajaraam | Kuidas mõõta | Usald. | Kuidas läbi kukub |
|---|---|---|---|---|---|
| **Elliotti lained** | 5 impulsi + 3 korrektsiooni, fraktaalne igal ajaraamil | Kõik, kõige stabiilsem D/W | Käsitsi märgistus; reeglid: laine 2 ei lähe alla laine 1 algust, laine 3 pole lühim, laine 4 ei kattu laine 1 tipuga | 2 | Märgistus on tagantjärele alati sobitatav; sama graafik lubab 3+ kehtivat lugemist. Kasuta ainult kolme kõva reegli **invalideerimiseks**, mitte prognoosiks |
| **Dow' teooria** | Trend = kõrgemad tipud + kõrgemad põhjad, kuni struktuur murdub | D/W | Viimane struktuurne HH/HL vs LH/LL | 4 | Külgsuunalises turus annab pidevaid valemurdeid |
| **Wyckoffi faasid** | Akumulatsioon → markup → distributsioon → markdown; spring/upthrust | H4–W | Mahu ja hinnaulatuse suhe faasides; spring = valemurd alla range'i, kiire tagasitulek | 3 | Faasi nimetatakse alles siis, kui see on läbi. Spring ja päris murd näevad reaalajas identsed välja |
| **Range / equal highs–lows** | Turg ehitab tasakaalutsooni, servad koguvad stopid | H1–D | Range serv ± ATR; equal highs = klastrunud stopid | 4 | Range murdub mõlemale poole enne päris suunda (nn double fakeout) |
| **Market / volume profile** | Hind naaseb kõrge mahu tsooni (POC), liigub kiiresti läbi madala mahu (LVN) | H4–W | POC, VAH/VAL, HVN/LVN | 4 | Uue info (uudis, likvideerimiskaskaad) korral profiil nullitakse |
| **Gann' nurgad / ruudud** | Hinna ja aja geomeetriline suhe | D–W | 1x1 nurgad, ruudu tasemed | 1 | Parameetrid on vabalt valitavad → sobitub alati tagantjärele. Ei kasuta |

## B. Proportsioonid ja tasemed

| Seaduspärasus | Mis see on | Ajaraam | Kuidas mõõta | Usald. | Kuidas läbi kukub |
|---|---|---|---|---|---|
| **Fibonacci retracement** | Korrektsioon peatub 0.382 / 0.5 / 0.618 / 0.786 juures | Kõik | Impulsi algus→tipp | 3 | Töötab, sest paljud vaatavad sama — st **enesetäituv**, mitte loodusseadus. Ilma mahu/positsioneerimise kinnituseta on 0.618 lihtsalt joon |
| **Fibonacci extension** | Sihtmärgid 1.272 / 1.618 / 2.618 | Kõik | Impulsi projektsioon | 2 | Trendis lendab hind neist läbi, range'is ei jõua kohale |
| **Konflueents** | Fib + MA + eelmine struktuurne tase + POC ühes kohas | Kõik | Loenda kokkulangevusi | 4 | Konflueentsi otsides leiab neid alati — piira max 2 punktile graafikul |
| **Measured move** | Muster projitseerib enda kõrguse murdepunktist edasi | H1–D | Range/kujundi kõrgus | 3 | Eeldab, et volatiliteet püsib sama; ATR-i kokkutõmbumisel ei tööta |
| **Ümmargused numbrid** | 100/1000/0.10 jne koguvad ordereid ja stoppe | Kõik | Otse hinnalt | 4 | Väga likviidsetes paarides efekt nõrgeneb |
| **ATR-normeeritud liikumine** | Päevane liikumine kipub jääma 1–1.5× ATR piiresse | D | ATR(14) | 4 | Uudis-/likvideerimispäevadel 3–5× ATR |
| **VWAP ± standardhälve** | Institutsionaalne keskmine; ±1σ / ±2σ ribad | Intraday–W | Ankrud: nädal, kuu, sündmus | 4 | Nõrgas mahus (nädalavahetus) VWAP triivib |

## C. Tsüklid ja aeg

| Seaduspärasus | Mis see on | Ajaraam | Kuidas mõõta | Usald. | Kuidas läbi kukub |
|---|---|---|---|---|---|
| **Halving-tsükkel (krüpto)** | ~4-aastane laine, tipp ~12–18 kuud pärast halvingut | Aastad | Päevade arv halvingust | 3 | Valim on n=4. ETF-voogude ajastul on tsükkel juba venitatud/lamedaks tõmmatud |
| **Nädalapäeva efekt** | Esmaspäeva gäpid, reede sulgemised, nädalavahetuse õhuke raamat | Päev | Tootluse jaotus nädalapäeva kaupa | 3 | Krüptos on 24/7, aga tuletisinstrumentide voog järgib ikka TradFi kalendrit |
| **Sessioonid** | Aasia range → Londoni murd → NY jätk/pööre | Intraday | UTC ajaaknad | 4 | Suurte makrouudiste päevadel sessiooniloogika kaob |
| **Kuu-/kvartalilõpp** | Rebalanss, aegumised, raamatute korrastamine | Päevad | Kalender | 4 | Suund pole ette teada, ainult volatiliteet on |
| **Optsioonide aegumine** | Hind tõmbub max pain / suurima OI striki poole | Nädal | Deribit OI strikkide kaupa | 3 | Toimib peamiselt viimasel 1–2 päeval enne aegumist |
| **Volatiliteedi ööpäevane muster** | Volatiliteet kobardub sessioonide avamiste ümber | Intraday | Realiseeritud vol tunni kaupa | 4 | Stabiilne, aga ei ütle suunda |

## D. Statistilised seaduspärasused

| Seaduspärasus | Mis see on | Ajaraam | Kuidas mõõta | Usald. | Kuidas läbi kukub |
|---|---|---|---|---|---|
| **Volatiliteedi kobardumine** | Suur liikumine järgneb suurele, vaikus vaiksele | Kõik | ATR / realiseeritud vol, GARCH | 5 | Praktiliselt ei kuku läbi — see on turgude kõige tugevam empiiriline fakt |
| **Vol. kokkusurumine → laienemine** | Ahenev ATR/Bollinger lõpeb impulsiga | H1–D | Bollinger bandwidth, ATR percentiil | 5 | Suund pole ennustatav — ainult liikumise **tulek** on |
| **Paksud sabad** | Ekstreemsed liikumised on palju sagedasemad kui normaaljaotus lubab | Kõik | Kurtoos, tootluste jaotus | 5 | Riskimudel, mis eeldab normaaljaotust, lammutab konto |
| **Lühiajaline mean reversion** | 1–5 päeva ülemäärane liikumine kipub osaliselt tagasi tulema | H4–D | z-skoor MA suhtes, RSI ekstreemid | 3 | Tugevas trendis "ülemüüdud" jääb ülemüüduks nädalateks |
| **Keskmise pikkusega momentum** | 1–12 kuu tootlus kaldub jätkuma | Nädalad–kuud | Tootlus vs turg | 4 | Pöördepunktides annab kõige valusama väljalöögi |
| **Hurst / trendilisus** | H > 0.5 = trendiv, H < 0.5 = tagasipöörduv režiim | D | Rescaled range | 3 | Režiim vahetub ilma hoiatuseta |
| **Autokorrelatsioon ~0 hinnas** | Suunda ei saa hinnast endast ette lugeda | Kõik | ACF tootlustel | 5 | See ongi põhjus, miks puhas indikaatorimäng ei tööta |

## E. Positsioneerimine ja tuletisinstrumendid — kõige mõõdetavam kiht

| Seaduspärasus | Mis see on | Ajaraam | Kuidas mõõta (CoinGlass) | Usald. | Kuidas läbi kukub |
|---|---|---|---|---|---|
| **Funding ekstreem** | Püsivalt kõrge positiivne funding = longid maksavad, rahvas ühel pool | H8–D | `funding_history` action=`oi_weighted` | 5 | Ekstreem võib püsida nädalaid; ajastus puudub |
| **OI + hinna neli kombinatsiooni** | ↑hind ↑OI = uus raha; ↑hind ↓OI = shortide kattmine; ↓hind ↑OI = uued shortid; ↓hind ↓OI = longide sundmüük | H1–D | `oi_history` action=`aggregated` | 5 | Ainult siis, kui OI on USD-s ja mitme börsi peale agregeeritud |
| **Likvideerimiskaskaad** | Klastri läbimine käivitab ahelreaktsiooni | Minutid–tunnid | `liq_history` action=`aggregated` | 5 | **Alla ~0.5% OI-st = müra**, mitte kaskaad. Kirjuta protsent alati välja |
| **Taker CVD** | Agressiivsete ostjate/müüjate netovoog | H1–D | `taker` action=`coin_history` (mitte `pair_history`) | 4 | Paaritasandi feed on katki olnud 50–100× — ristkontrolli alati `price_history` mahuga |
| **Börsi kaal (OI jaotus)** | Kelle andmed üldse loevad | — | `oi_distribution` action=`by_exchange` — **JOOKSUTA ESIMESENA** | 5 | Alla ~25% OI-st hoidev börs **ei ole** "rahvahulk" |
| **Long/short ratio** | Retaili kalle | H4–D | `long_short` action=`global` | 3 | Kontode arv ≠ raha. Suur raha ja retail lähevad tihti lahku |
| **Basis / term structure** | Futuuri preemia spoti suhtes | D–W | Kvartalifutuur vs spot | 4 | Backwardation = kapitulatsioon, contango ekstreem = ülekuumenemine |
| **Optsioonide gamma / OI seinad** | Suur OI strike toimib magneti või tõkkena | Päevad | Deribit strike OI | 3 | Kehtib ainult likviidsetel strikkidel |

## F. Likviidsus ja orderivoog

| Seaduspärasus | Mis see on | Ajaraam | Kuidas mõõta | Usald. | Kuidas läbi kukub |
|---|---|---|---|---|---|
| **Likviidsuse jaht** | Hind liigub sinna, kus on stoppide klaster (eelmiste tippude/põhjade taha) | H1–D | Equal highs/lows + likvideerimiskaart | 4 | Forward-looking heatmap on tasulise plaani taga → küsi ekraanipilti |
| **Absorptsioon** | Suur maht ilma hinnaliikumiseta = keegi täidab vastassuunas | Minutid–H1 | Maht vs hinnaulatuse suhe | 4 | Ilma orderiraamatuta on see tõlgendus, mitte mõõt |
| **Imbalance / FVG** | Kiire liikumise jäetud "auk", mille juurde tullakse tagasi | H1–D | 3 küünla lõhe | 3 | Tugevas trendis jäävad täitmata kuudeks |
| **Orderiraamatu sügavus** | Õhuke raamat = suurem slippage ja ülelöögid | Reaalaeg | `ob_history` action=`pair_depth` | 4 | Spoof-orderid moonutavad pilti |

## G. Korrelatsioon ja makro

| Seaduspärasus | Mis see on | Ajaraam | Kuidas mõõta | Usald. | Kuidas läbi kukub |
|---|---|---|---|---|---|
| **BTC domineerib altcoine** | Enamik altcoine liigub BTC beetana, mitte oma andmete peale | Kõik | Korrelatsioon BTC-ga samas aknas | 5 | **Iga altcoini puhul tõmba BTC sama akna peale ja ütle välja, kumb muutuja juhib** |
| **Riskiisu (DXY, tootlused, aktsiad)** | Krüpto käitub pika kestusega riskivarana | D–W | DXY, US10Y, NDX korrelatsioon | 4 | Korrelatsioonid katkevad krüptospetsiifiliste sündmuste ajal |
| **Stablecoin'i pakkumine** | Kasvav USDT/USDC pakkumine = sisenev ostujõud | Nädalad | Emissioon | 3 | Aeglane, ei ajasta midagi |
| **ETF / spot-vood** | Institutsionaalne netovoog surub trendi | Päevad | Päevased netovood | 4 | Ainult BTC/ETH; altidele ei kandu |

## H. Klassikalised indikaatorid — aus hinnang

| Indikaator | Mida ta tegelikult teeb | Usald. | Ainus mõistlik kasutus |
|---|---|---|---|
| **RSI** | Normeeritud momentum | 2 | Divergents struktuursel tasemel; mitte "üle 70 = müü" |
| **MACD** | Kahe libiseva keskmise vahe | 2 | Režiimi kinnitus, hilineb alati |
| **Libisevad keskmised (50/100/200)** | Enesetäituv tugi/vastupanu, sest kõik vaatavad | 3 | Trendifilter, mitte sisenemine |
| **Bollinger** | Volatiliteedi ümbris | 4 | Bandwidth kokkusurumise tuvastus (vt D) |
| **ADX** | Trendi tugevus | 3 | Otsustada, kas kasutada trendi- või range-loogikat |

**Kõik selle tabeli indikaatorid on hinna tuletised.** Nad ei lisa infot, mida hinnas juba pole.
Uut infot lisavad ainult E, F ja G plokid.

---

## Koondloogika — kuidas kõik üheks lugemiseks kokku panna

Järjekord on oluline. Ära hüppa vahele.

1. **Börsi kaal** — `oi_distribution by_exchange`. Ilma selleta ei tea, kelle andmed loevad.
2. **Struktuur** (A) — kus on viimane kehtiv HH/HL või LH/LL, kus on range' servad.
3. **Tase** (B) — kas hind on konflueentsis (fib + POC + struktuur + MA)? Kui ei ole, oota.
4. **Aeg** (C) — kas ees on aegumine, kvartalilõpp, sessioonivahetus?
5. **Režiim** (D) — kas ATR on kokku surutud (oota laienemist) või laienenud (oota tagasitõmmet)?
6. **Positsioneerimine** (E) — funding, OI-hinna kombinatsioon, likvideerimised % OI-st, taker CVD.
7. **Likviidsus** (F) — kus on stoppide klaster, kummal pool on kütus.
8. **Juhtiv muutuja** (G) — kas coin liigub omal jõul või BTC/makro peale?
9. **Invalideerimine** — täpne hind või tingimus, mis lugemise valeks tunnistab. **Ilma selleta lugemist ei anta.**

### Skoorileht

Iga kategooria annab +1 (poolt), 0 (neutraalne), −1 (vastu). Liida A–G kokku:

| Skoor | Tähendus |
|---|---|
| ≥ +4 | Tugev kalle, kategooriad ei ole vastuolus |
| +2…+3 | Kalle olemas, vajab käivitajat |
| −1…+1 | Ei ole lugemist. Ütle seda otse, ära tooda stsenaariume |
| ≤ −2 | Kalle vastassuunas |

**Vastuolulisi kategooriaid ei siluta üheks narratiiviks — vastuolu näidatakse välja.**

---

## Mis selles nimekirjas EI tööta üksi

- Elliott ja Gann ilma mehaanilise invalideerimiseta — tagantjärele sobitatavad mõlemad.
- Fibonacci ilma mahu või positsioneerimise kinnituseta — see on lihtsalt joon.
- Üksik retaili long/short ratio ühelt börsilt — kontode arv ei ole raha.
- RSI/MACD ekstreemid trendis.
- Likvideerimised alla ~0.5% OI-st.
- Halving-tsükkel n=4 valimiga esitatuna prognoosina.

## Andmete kontroll enne iga lugemist

Iga arv peab olema jälgitav: **mis tool, mis börs, mis intervall, mis ajatempel.**
Kui vastust ei ole — väide kustutatakse või märgitakse kontrollimatuks.
"Mul pole andmeid" ilma endpointi kutsumata on vale väide, mitte ettevaatlikkus.
