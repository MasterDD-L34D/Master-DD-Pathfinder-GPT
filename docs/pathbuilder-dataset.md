# Dataset Pathbuilder 1e (raw dall'APK) — inventario e formato

Ricognizione del **2026-08-01** (task PB-1) sui 253 XML estratti da
`res/raw/` dell'APK Pathbuilder 1e (BlueStacks 5 dell'utente, permesso d'uso
concesso 2026-08-02). Dataset rilocato in
`data/reference/pi_local_only/pathbuilder/` (**PI local-only, mai committato,
mai redistribuito** — vedi `_provenance.json` nella stessa directory).

Formato generale di ogni file: XML con radice `<Root>` e una `<Row>` per voce;
i campi sono sotto-elementi della riga e variano per tipo di dataset. I campi
`Description` contengono testo Paizo (Product Identity): restano solo nel
dataset locale e NON vengono mai esportati nei JSON committati (disciplina OGL
del progetto, come per l'import PCGen A1).

Totali: **253 file XML, 23.105 righe** (più 2 file non-dataset di billing
Android, ignorati).

## Gruppi di dataset

| Gruppo | File | Righe | Contenuto |
|---|---|---|---|
| `data_specials_*` | 188 | 4.253 | Feature di classe selezionabili (rage powers, scoperte, exploit, domini, bloodline, ordini, deed, hex, talenti da ladro…) |
| `data_archetypes_*` | 42 | 5.069 | Archetipi di classe (uno per classe, incluse ninja/samurai/unchained) |
| compagni (`data_animals`, `data_familiars*`, `data_eidolons_*`, `data_unchained_eidolons_*`) | 8 | 658 | Compagni animali, famigli, eidolon (forme base, evoluzioni, sottotipi) |
| altri dataset principali | 15 | 13.125 | feats, classi, razze, equipaggiamento, armi/armature, incantesimi, tratti, ecc. |

## Dataset principali (file singoli)

| File | Righe | Campi reali | Uso previsto |
|---|---|---|---|
| `data_feats.xml` | 3.320 | FeatName, Category, EffectMethod, RequirementMethod, MaxTakable, Prerequisites, Description, URL, Source + requisiti strutturati `r*` (vedi sotto) | (b) `pathbuilder-feats.json` (senza Description) + confronto con pcgen-feats |
| `data_classes.xml` | 163 | Classname, Category, Method, Requirements, RequiredBAB/Level/Feats/Specials/…SpellLevel, PackPrestige, Description, Source, Ref | Arricchimento `classes.json` (report, niente merge cieco) |
| `data_races.xml` | 669 | Race, Trait, Description, ShowInSpecials, HasEffect, Src | **Importato (D1)**: `pathbuilder-races.json` — 74 razze (name/size/abilityAdjustments dal dato/flexible/playable/source) |
| `data_races_alternative_traits.xml` | 702 | Race, Trait, ChangedTraits, ReplacedTraits, Description, ShowInSpecials, HasEffect, Source | **Importato (D1)**: `pathbuilder-race-traits.json` — 702 tratti alternativi su 59 razze (race/trait/replaces/changes/source) |
| `race_builder_traits.xml` | 229 | RacialTrait, Category, Type, RP, PowerLevel, MaxTakable, AddMethod, Description | Race builder (RP = race points) |
| `data_background_traits.xml` | 1.569 | Name, Type, Description, ClassSkill(Choice), Skill(Bonus), Fort/Reflex/Will, Initiative, rAlign/rClass/rFaction/rRace/rReligion, Source, Ref | Tratti (background) con bonus meccanici strutturati |
| `data_armor.xml` | 58 | Armor, Category, Bonus, MaxDex, CheckPenalty, Arcane_Spell, Speed_30ft, Weight1 | Confronto con pcgen-equipment |
| `data_armor_magic.xml` | 68 | Categories, Effect | Qualità magiche per armature |
| `data_weapons.xml` | 313 | Weapon, Category, Proficiency, Damage, DamageType, CritRange, CritMultiplier, RangeIncrement, Hands, Finessable, WeaponGroup, UsesAmmo, DefaultDamage, naturalWeapon | Confronto con pcgen-equipment |
| `data_weapon_effects.xml` | 97 | Name, Categories, Damage | Qualità magiche per armi |
| `data_equipment_slotted.xml` | 2.855 | Name, Item, Slot, Cost, Weight, BonusType, EffectType, Amount, DefaultAmount, Description, Finished, Source, Ref | Oggetti magici a slot |
| `data_spells.xml` | 2.922 | name, school, subschool, descriptor, castingTime, components, range, area, effect, targets, duration, savingThrow, sr, description, source, spellLevelsDisplay + una colonna per classe (Alchemist…Wizard) + domain/bloodline/patron/mythic | Confronto con pcgen-spells (livelli per classe già in colonna) |
| `data_feat_metadata.xml` | 100 | name, count | Statistiche d'uso cloud Pathbuilder (talenti più presi: Weapon Focus 3123, Power Attack 2646, Dodge 2143…) |

## `data_specials_*` — feature di classe (input di `pathbuilder-class-features.json`)

Campi reali (subset variabile per file):

- `Special` — nome della feature (chiave);
- `Requirements` — requisiti testuali (es. `"Barbarian 6, intimidating glare"`);
- `RequiredSpecial1` / `RequiredSpecial2` — altra feature richiesta (per nome);
- `LevelAP` — livello minimo "approx" Pathbuilder (intero);
- `RequirementMethod` / `EffectMethod` — hook interni dell'app (camelCase);
- `Description` — testo Paizo (PI, mai esportato);
- `Source` — sigla libro (CRB, ACG, APG…);
- `Ref` — URL di riferimento (paizo.com PRD o aonprd.com).

Esempio reale (`data_specials_barbarian_rage_powers.xml`):

```xml
<Row>
  <Special>Battle Roar</Special>
  <LevelAP>5</LevelAP>
  <RequiredSpecial1>Intimidating Glare</RequiredSpecial1>
  <Requirements>Barbarian 6, intimidating glare</Requirements>
  <Description>...</Description>
  <Source>ACG</Source>
  <Ref>http://paizo.com/pathfinderRPG/prd/advancedClassGuide/classOptions/barbarian.html#rage-powers</Ref>
</Row>
```

File più grandi: `barbarian_rage_powers` 228, `cleric_domains` 206,
`alchemist_discoveries` 190, `rogue_talents` 165, `kineticist_wild_talents`
143, `monk_qinggong_powers` 126, `vigilante_talents` 117,
`unchained_barbarian_rage_powers` 109, `witch_hexes` 106. Le
`data_specials_oracle_mystery_*.xml` (34 file) sono le revelation per mistero;
alcuni file "hub" (`oracle_mysteries`, `medium_spirits`, bloodline…) hanno solo
nome+Source+Ref (la Description sta altrove o è assente).

## `data_archetypes_*` — archetipi

Campi: `ArchetypeName`, `ArchetypeSpecial`, `Level`, `Changed`, `Replaced`,
`Details`, `Display`, `EffectMethod`, `Race` (opzionale), `Completed`,
`Source`, `Ref`. Ogni riga = una voce di modifica dell'archetipo (feature
aggiunta/cambiata/sostituita a un dato livello). Uso previsto: supporto agli
archetipi nel builder (non importato in PB-1).

## Compagni

`data_animals.xml` (197): stat base + progressione per livello
(`levelStr/levelCon/…`, `levelSpecialAttacks`). `data_familiars.xml` (168):
statblock completo (ac/bab/save/skill/…). `data_eidolons_*` e
`data_unchained_eidolons_*`: forme base, evoluzioni (con `Cost`, `ReqLevel`,
`ReqForms`, `TimesSelectable`), sottotipi.

## `data_races*` — razze (import D1, 2026-08-07)

Importati da `tools/import_pathbuilder_races.py` verso
`pathmaster-dd/packages/rules-engine-v2/src/data/pathbuilder-races.json` e
`pathbuilder-race-traits.json` (solo nomi + meccaniche, MAI le Description).

Note di formato specifiche:

- `<Race>` compare **solo sulla prima riga** del blocco razza; le righe
  seguenti ereditano la razza corrente. `data_races.xml`: 669 righe → 74
  razze; `data_races_alternative_traits.xml`: 702 righe → 59 razze.
- `<Src>` (races) / `<Source>` (alternative traits) è presente solo su
  alcune righe ma uniforme per razza; il blocco Human non ha Src (source
  `null` dichiarata).
- **Ability adjustments non strutturati**: vivono nella Description del
  tratto `Ability Bonus`. L'importer parsa SOLO il formato regolare
  segno+numero adiacente al nome caratteristica (`+2 Constitution`,
  `–2 Charisma`, sigle `+2 Str`; meno U+2013/U+2212/ASCII): 15 razze su 74.
  Le altre 59 (incluse quasi tutte le ARG, dove Pathbuilder applica i bonus
  via hook interni `HasEffect`) hanno `abilityAdjustments: null`
  **dichiarato**, mai inventato — elenco nel `report` del JSON.
- Razze flex (`+2 to One Ability Score`): Human, Half-Elf, Half-Orc →
  `flexible: true` (coerente col contratto E6-A6 del converter).
- Taglia: tratto il cui nome è una categoria di taglia; 22 razze senza
  tratto taglia → `size: null` dichiarata.
- `playable`: **lista esplicita** nell'importer (`PLAYABLE_PC_RACES` =
  7 core CRB + 30 ARG featured/uncommon), NON un filtro per Src: le schede
  race-builder Lizardfolk/Gnoll (Src=ARG) restano `playable: false`.
- `ReplacedTraits`/`ChangedTraits`: nomi di tratti separati da `&`; 44
  tratti hanno `ChangedTraits`, ogni tratto sostituisce o cambia qualcosa.

## Formato dei requisiti strutturati dei feat (`data_feats.xml`)

Oltre al testo libero `Prerequisites`, molte righe hanno campi `r*` con
requisiti macchinabili. Conteggi reali sulle 3.320 righe:

| Campo | Righe | Valori distinti | Formato |
|---|---|---|---|
| `rFeats` | 1.383 | 805 | Nomi di talenti richiesti, separati da `&` (es. `Dodge&Mobility`) |
| `rStat` | 628 | 79 | `indice£valoreMin`, più vincoli separati da `&` (es. `3£13`, `5£13&1£13`) |
| `rClassFeature` | 615 | 206 | Nome della capacità di classe richiesta (es. `Bardic Performance`, `Sneak Attack`) |
| `rCharLevel` | 609 | 18 | Livello minimo del personaggio (intero) |
| `rRace` | 533 | 84 | Razze ammesse, separate da `&` (es. `Half-Orc&Orc`) |
| `rBAB` | 475 | 15 | Bonus di attacco base minimo (intero) |
| `rClassLevel` | 129 | 86 | `Classe£livelloMin`, più alternative separate da `&` (es. `Rogue£3&Unchained Rogue£3`) |
| `rCasterLevel` | 110 | 13 | Livello dell'incantatore minimo (intero) |
| `rFeatsWithSpecificInfo` | 72 | 39 | `Talento£scelta` (es. `Skill Focus£Stealth`, `Spell Focus£conjuration`, `Weapon Focus£whip`) |
| `rMagicRef` | 23 | 2 | Tipo di magia richiesta: `0` = arcana, `1` = divina |

### Mappa indice caratteristica di `rStat`

L'indice è la posizione nell'array caratteristiche dell'app:

| Indice | Caratteristica |
|---|---|
| 0 | FOR |
| 1 | DES |
| 2 | COS |
| 3 | INT |
| 4 | SAG |
| 5 | CAR |

Verifica incrociata con il campo testuale `Prerequisites` (esempi reali):

- `Abeyance`: `rStat=3£13` ↔ "Int 13, Spellcraft 5 ranks…";
- `All-Consuming Swing`: `rStat=0£13` ↔ "Str 13, Power Attack, Cleave…";
- `Adept Channel`: `rStat=5£13` ↔ "…Cha 13";
- `Betrayal Sense`: `rStat=4£13` + `rClassLevel=Rogue£3&Unchained Rogue£3` ↔
  "Wis 13, rogue level 3rd, trap sense class feature".

### Note sui separatori

- `£` (U+00A3) separa chiave e valore dentro un vincolo (`rStat`, `rClassLevel`,
  `rFeatsWithSpecificInfo`);
- `&` separa vincoli/alternative multipli dentro lo stesso campo (`rStat`,
  `rFeats`, `rRace`, `rClassLevel`; anche `Category`, che è una lista di
  indici-categoria interni Pathbuilder, es. `0&3&4` — la mappa indice→categoria
  è interna all'app e non è nel dataset; `9` ricorre sui talenti da mostro,
  `10`/`11`/`12`/`14` su categorie minori).

### Campi non strutturati

`EffectMethod` / `RequirementMethod` sono nomi di funzione interni dell'app
(es. `aberrantTumor`, `baseFortSave4`): coprono requisiti non esprimibili con i
campi `r*`. Vanno preservati grezzi (utili come hook) ma non decodificati.

## Policy di licenza (ribadita)

- Meccaniche e nomi: OGL 1.0a — esportabili.
- `Description` e ogni prosa di regole: testo Paizo (PI) — **mai esportato**
  nei JSON committati; resta solo nel dataset locale
  `data/reference/pi_local_only/pathbuilder/` (gitignored).
- I JSON derivati (`pathbuilder-class-features.json`,
  `pathbuilder-feats.json`) includono il campo `description` **solo** per le
  feature di classe destinate ad arricchire gli slot M4 di pathmaster (stesso
  criterio delle description già presenti in `src/catalogs/class-features.ts`):
  il dataset grezzo completo con le Description resta comunque local-only.
