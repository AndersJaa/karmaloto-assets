# VSI — Voog–Surve indeks

Liitindikaator, mis koondab **ainult mehaaniliselt mõõdetavad** näitajad
[turu seaduspärasuste koondtabelist](../turu-seadusparasused.md) — plokid D, E, F, G.

```
python3 vsi.py --demo     # näidislugemine väljamõeldud arvudega
python3 vsi.py --test     # 14 testiplokki
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

## Režiim — ainus koht, kus kontekst numbrit liigutab

Kaks üksteisest sõltumatut režiimi, kumbki eraldi teljest:

**Trend vs külgsuunaline** — reegel on üle võetud only_fibonacci `Multicator Table`'ist:

```
ADX < 20  VÕI  Chop > 61.8   →   külgsuunaline
```

VÕI, mitte JA, sest kumbki tingimus üksi jätab augu: ADX jääb madalaks ka aeglases
trendis, Choppiness läheb kõrgeks ka laias trendivas vahemikus. Kaks sõltumatut mõõtu
sama asja kohta eksivad erinevatel juhtudel. `adx()` ja `choppiness()` on moodulis
olemas, nii et neid ei pea graafikult maha lugema.

See režiim **tõstab voo läve**, ei anna suunda:

| Režiim | Voo lävi |
|---|---|
| trend üles / trend alla | 25 |
| külgsuunaline | 40 |

Põhjus on koondtabeli Dow' rida: külgsuunalises turus on valemurd reegel, mitte erand.
Sama V = +27 annab trendis lugemise ja külgsuunas mitte. Test kontrollib täpselt seda.

**Volatiliteet (ATR pertsentiil)** on sellest sõltumatu: kokkusurutud ATR ütleb, et
liikumine **tuleb**, mitte kuhu. Külgsuunaline turg võib olla nii kokku surutud kui
laienenud, ja need kaks tähendavad täiesti eri asja — sellepärast neid ei liideta.


## Skänner — coini otsimine

```bash
python3 skanner.py --demo
python3 skanner.py --test
```

`skanner.py` vastab teisele küsimusele kui VSI. VSI ütleb, mis toimub **selle**
mündiga; skänner ütleb, **millist vaadata**.

### Universum on reeglid, mitte nimekiri

Käsitsi valitud watchlist töötab äärmuste otsija vastu: sa vaatad neid münte, mis
sulle meelde tulid, mitte neid, kus midagi toimub. Universum defineeritakse
reeglitega ja uueneb ise:

| Reegel | Miks |
|---|---|
| OI ≥ 50M USD | allpool ei saa mõistliku slippage'iga sisse ega välja |
| Maht ≥ 25M USD | sama |
| Vähemalt 3 börsil | „mitte shitcoin" — üheainsa börsi münt ei ole kaubeldav |
| BTC välja | võrdlusalus, mitte kandidaat — tema ülejääk iseenda vastu on null |

Väljajäänud **loetletakse põhjendusega**. Vaikne kadumine nimekirjast loeks nagu
„ei olnud huvitav", mitte „ei mahtunud reeglitest läbi".

### Kaks nimekirja, kaks eri küsimust

**ÄÄRMUSED** — `|S| ≥ 60` **ja** voog liigub surve vastu **ja** `|V| ≥ 15`

Rahvahulk on maksimaalselt ühel pool ja raha on hakanud teistpidi liikuma.
Skoor on **korrutis**, mitte summa: äärmus ilma pöördeta on null ja pööre ilma
äärmuseta on null. Kumbki üksi ei ole see, mida otsitakse.

| Seis | Suund |
|---|---|
| S tugevalt +, V pöördub − | alla — longide väljasurumine algab |
| S tugevalt −, V pöördub + | üles — squeeze algab |

**JÄTK** — `|V| ≥ 30`, `R` sama märgiga, `|S| < 60`

Liikumine käib ja rahvahulk pole veel peal. **V ja R peavad olema sama märgiga:**
münt, mis liigub oma suhtelise tugevuse vastu, on müra, mitte trend. Surve annab
karistuse, kui ta on vooga samas suunas — siis on hea osa liikumisest juba tehtud.

Mõlemas nimekirjas maksimaalselt 4 rida. Pikem nimekiri on sama hea kui puuduv.

### Kolmas telg: suhteline tugevus (R)

Rotatsioon müntide vahel on suhtelise tugevuse mäng. Münt, mille V on +60
sellepärast, et kogu turg tõuseb, ei ole leid — ta on beeta. R on z-skoor
**kandidaatide lõikes**, mitte mündi oma ajaloo vastu: küsimus pole „kas ta on
tugevam kui eelmisel nädalal", vaid „kas ta on tugevam kui teised praegu".

Lipp **„tugevus tuleb BTC nõrkusest"**: langevas turus on iga vähem langenud münt
positiivse ülejäägiga. Ilma selle liputa loeks skänner iga vastupidaja leiuks.

### Nädalased parameetrid

`HINNA_REF` 12% ja `OI_REF` 15% VSI 3% / 5% asemel. Päevase akna refidega annaks
nädalane müra igale mündile täisskoori.

### Mida see EI ole

Kumbki nimekiri ei ole soovitus ega sisenemispunkt. **Äärmus ei ole ajastus** —
funding võib ekstreemne püsida nädalaid — ja enamik äärmusi ei pöördu üldse.
Nimekiri annab kandidaadid, mille peale VSI täies mahus jooksutada.
