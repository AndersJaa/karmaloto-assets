# VSI — Voog–Surve indeks

Liitindikaator, mis koondab **ainult mehaaniliselt mõõdetavad** näitajad
[turu seaduspärasuste koondtabelist](../turu-seadusparasused.md) — plokid D, E, F, G.

```
python3 vsi.py --demo     # näidislugemine väljamõeldud arvudega
python3 vsi.py --test     # 8 testiplokki
```

## Miks Elliott siin ei ole

Elliott, Gann, Wyckoff ja mustrituvastus said koondtabelis hinde 1–3 just sellepärast,
et nad on tõlgendus, mitte mõõt. Kui panna Elliotti laine number liitindeksisse, siis
indeks **teeskleb täpsust, mida tal ei ole** — ja halvem: subjektiivne sisend hakkab
liigutama numbrit, mis näeb välja objektiivne. Struktuur jääb eraldi kihiks, mida
vaadatakse enne indeksit (koondloogika sammud 2–3), mitte selle sees.

Sisse pääsesid ainult need, mille väärtuse saab ühest endpointist arvuna kätte ja
mille tõlgendus ei muutu sõltuvalt sellest, kes vaatab.

## Kaks telge, mitte üks number

```
              S surve (rahvahulk longis) +100
                            |
   LONGIDE VÄLJASURUMINE    |    ÜLEKUUMENENUD TÕUS
   voog alla, rahvas longis |    voog üles, rahvas longis
                            |
  -100 ────────────────────-+-──────────────────── +100  V voog
                            |
   SHORTIDE KÜTUS           |    PUHAS TÕUS
   voog alla, shordid täis  |    voog üles, rahvas pole longis
                            |
              S surve (rahvahulk shortis) -100
```

**Telgi ei liideta.** Liitmine kaotaks täpselt selle info, mis siin loeb: tõus madala
survega ja tõus kõrge survega on vastandid, kuigi mõlemal on V positiivne. Üks number
näitaks mõlemal juhul "+70" ja kaotaks vahe ära.

Kui **|V| < 25**, siis lugemist ei ole. Indeks ütleb seda otse, ei tooda stsenaariume.

## Komponendid ja kaalud

### V-telg — mida raha praegu teeb

| Komponent | Kaal | Allikas | Värav |
|---|---|---|---|
| OI + hinna kvadrant | 35 | `oi_history action=aggregated` + `price_history` | Peab olema USD-s ja agregeeritud |
| Taker CVD | 30 | `taker action=coin_history` | Mitte `pair_history` — see feed on olnud 50–100× vale |
| Likvideerimised | 20 | `liq_history action=aggregated` | **Alla 0.5% OI-st → komponent lülitub välja** |
| Spot / ETF voog | 15 | Päevased netovood | Ainult BTC / ETH |

### S-telg — kui ühel pool rahvahulk on

| Komponent | Kaal | Allikas | Värav |
|---|---|---|---|
| Funding | 45 | `funding_history action=oi_weighted` | — |
| Basis / term structure | 30 | Kvartalifutuur vs spot | — |
| Long/short ratio | 25 | `long_short action=global` + `oi_distribution` | **Skaleeritakse börsi OI-osakaaluga** |

Long/short saab teadlikult madalaima kaalu ja ainsana kohustusliku skaleerimise:
kontode arv ei ole raha, ja alla ~25% OI-st hoidva börsi ratio ei ole rahvahulk.

## Kolm asja, mis on koodi sisse ehitatud, mitte kommentaaris

1. **Müravärav likvideerimistel.** Alla 0.5% OI-st komponent *lülitub välja* ja tema
   kaal jaotub teiste vahel ümber. 90/10 jaotus 0.1% OI pealt ei ole kaskaad.
2. **Invalideerimine on kohustuslik.** `render()` viskab `ValueError`-i, kui
   invalideerimist pole antud. Lugemist ilma selleta füüsiliselt ei tule.
3. **Iga arv kannab oma allikat.** Iga komponendi juures on kirjas, mis kutse ta andis.
   Väljundis on see näha rea kaupa — arvu, mille allikat ei ole, siit ei tule.

## Robustne z-skoor

Normaliseerimine käib mediaani ja MAD-i baasil, mitte keskmise ja standardhälbe baasil.
Põhjus on koondtabeli plokk D: tootluste jaotusel on paksud sabad, üks
likvideerimiskaskaad nihutab keskmise ära ja kõik järgnevad z-skoorid on valed.
Test `robust_z` juures kontrollib täpselt seda.

## Usaldusväärsuse kordaja

```
usaldusväärsus = värskus × kaetud_OI_osakaal × keskmine_komponentide_kate
```

- **värskus** langeb, kui andmed on üle 3h vanad
- **kaetud OI osakaal** — kui suurt osa turust andmed üldse katavad
- **komponentide kate** — kui palju kaalust jäi väravate taha

Eraldi lipp: kui |korrelatsioon BTC-ga| ≥ 0.80, kirjutatakse välja, et **juhtiv muutuja
on BTC**, mitte coin ise. See ei nulli lugemist — see ütleb, mille peale coin liigub.

Volatiliteedi režiim (ATR pertsentiil) on samuti eraldi, mitte telje sees: kokkusurutud
ATR ütleb, et liikumine **tuleb**, mitte kuhu. Suunda temast ei tehta.
