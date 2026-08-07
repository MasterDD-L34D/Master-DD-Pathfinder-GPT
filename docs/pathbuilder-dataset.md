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
| `data_archetypes_*` | 42 | 5.069 | Archetipi di classe (uno per classe, incluse ninja/samurai/unchained) — **importato (D2)**: `pathbuilder-archetypes.json` |
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
| `data_armor.xml` | 58 | Armor, Category, Bonus, MaxDex, CheckPenalty, Arcane_Spell, Speed_30ft, Weight1 | **Importato (D4)**: `pathbuilder-equipment.json` — 58 armature/scudi (stat strutturate; MaxDex 99→null, CheckPenalty magnitudine→segno meno, Arcane_Spell frazione→%, Speed -1→null) |
| `data_armor_magic.xml` | 68 | Categories, Effect | Qualità magiche per armature (non importato in D4: candidato D6) |
| `data_weapons.xml` | 313 | Weapon, Category, Proficiency, Damage, DamageType, CritRange, CritMultiplier, RangeIncrement, Hands, Finessable, WeaponGroup, UsesAmmo, DefaultDamage, naturalWeapon | **Importato (D4)**: `pathbuilder-equipment.json` — 313 armi (13 senza danno dichiarato, 2 doppie con critico per estremità; MAI costo/peso: assenti nel dato) |
| `data_weapon_effects.xml` | 97 | Name, Categories, Damage | Qualità magiche per armi (non importato in D4: candidato D6) |
| `data_equipment_slotted.xml` | 2.855 | Name, Item, Slot, Cost, Weight, BonusType, EffectType, Amount, DefaultAmount, Description, Finished, Source, Ref | **Importato (D4)**: `pathbuilder-equipment.json` — 2.783 oggetti nome+costo+slot (72 righe template senza Name saltate; 6 nomi duplicati dichiarati; MAI Description/Ref/BonusType/Amount) |
| `data_spells.xml` | 2.922 | name, school, subschool, descriptor, castingTime, components, range, area, effect, targets, duration, savingThrow, sr, description, source, spellLevelsDisplay + una colonna per classe (Alchemist…Wizard) + domain/bloodline/patron/mythic | **Importato (D5)**: `pathbuilder-spells.json` — 2.922 spell (livelli da spellLevelsDisplay, 4 segmenti irregolari raw, colonne stale non esportate; MAI description/mythic) + riconciliazione a 3 fonti `spell-sources.json` |
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

## `data_archetypes_*` — archetipi (import D2, 2026-08-07)

Importati da `tools/import_pathbuilder_archetypes.py` verso
`pathmaster-dd/packages/rules-engine-v2/src/data/pathbuilder-archetypes.json`
(solo nomi + meccaniche, MAI le `<Details>`). Forma del JSON: per classe
(nome file), per archetipo: `source`, `race` (archetipi razziali) ed
`entries` = lista di `{special, level, replaced[], changed[], effectHook?}`.

Campi reali: `ArchetypeName`, `ArchetypeSpecial`, `Level`, `Changed`,
`Replaced`, `Details` (PI, mai esportata), `Display`, `EffectMethod`, `Race`
(opzionale), `Completed`, `Source`, `Ref`. Ogni riga = una voce di modifica
dell'archetipo (feature aggiunta/cambiata/sostituita a un dato livello).
Conteggi: 42 file, **5.069 righe → 1.361 archetipi, 5.063 entries**.

Note di formato specifiche:

- `<ArchetypeName>` compare **solo sulla prima riga** del blocco archetipo
  (con `<Source>`, `<Details>`, `<Ref>`); le righe seguenti ereditano
  l'archetipo corrente. Nessun nome duplicato dentro una classe.
- `<Replaced>`/`<Changed>`: voci separate da `&`; i suffissi progressivi
  (`Trap Sense +1&...&+6`, `Weapon Training 1..4`) restano parte del nome
  (progressione = dato onesto, non dedotta). Un solo separatore di coda nel
  dataset (`Smite Evil&`, paladin): tollerato.
- `<Completed>Yes</Completed>`: sentinella di fine blocco — 6 righe hanno
  SOLO Completed e sono saltate (`report.skippedCompletedSentinels`).
- 3 entries senza `<Level>` (Clone Master "Bomb", Esoteric "Unarmed Strike",
  Contemplative "Know the Unseen Disciples"): `level: null` dichiarato.
- `<EffectMethod>` = hook interno dell'app (camelCase), NON un effetto:
  esportato come `effectHook` dichiarato, mai decodificato.
- `<Race>` (100 archetipi razziali): una riga per archetipo → `race` a
  livello archetipo, `null` altrove.
- **Slot rivelazione oracle numerati per ordine di concessione**:
  "Revelation 1..6" = livelli 1°/3°/7°/11°/15°/19° (verificato su Spirit
  Guide: "Revelation 2&3&5" = RAW ACG 106 rivelazioni di 3°/7°/15°).
- Classi PB fuori dal nostro corpus classi (`unchained_rogue`, `omdura`):
  importate comunque (sono dataset); la risoluzione motore le raggiunge solo
  se la classe esiste in `classes.json` (comportamento dichiarato).
- Motore (D2): catena **curato (`ARCHETYPE_REPLACEMENTS`, 46) > PB >
  sconosciuto** in `catalogs/archetypes.ts`; mappa nomi→feature-ID ESPLICITA
  in `catalogs/archetypes-pb.ts` (registro scelte: rules-engine-v2
  `INTERPRETATIONS.md` § "Archetipi Pathbuilder").

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

## `data_weapons` / `data_armor` / `data_equipment_slotted` — equipaggiamento (import D4, 2026-08-07)

Importati da `tools/import_pathbuilder_equipment.py` in
`pathbuilder-equipment.json` (pathmaster `rules-engine-v2/src/data/`).
Catalogo unificato lato motore: `src/catalogs/equipment.ts` (PCGen vince sui
valori duplicati, PB aggiunge copertura — v. `docs/superpowers/pcgen-import.md`
e `packages/rules-engine-v2/INTERPRETATIONS.md`).

Note di formato (ricognizione 2026-08-07):

- **`data_weapons.xml` (313)**: `Proficiency` -1 naturale/disarmato, 0
  semplice, 1 da guerra, 2 esotica, 3 da fuoco; `Category` 0 leggera, 1 una
  mano, 2 due mani, 3 da tiro, 4/5 da fuoco a una/due mani, 6 naturale.
  Mappe **dichiarate** nel JSON (derivate da ispezione dei membri, non da
  documentazione PB assente). `Damage` `-1` / `DamageType` `0` / `CritRange`
  `-1` = assenti nel dato → `null` dichiarato (13 armi senza danno: touch
  attack, reti, blast cinetici). `CritRange` è il MINIMO del dado (19 =
  19-20). `Hands` 0 = una mano/leggera, 1 = due mani. `WeaponGroup` separa
  i gruppi con `&`. Armi doppie (2: Gnome hooked hammer, Taiaha): `Damage`
  e `CritMultiplier` per estremità (`1d8&1d6`, `3&4`) → `critMultipliers`
  lista. **Costo/peso assenti nel dato: mai inventati** (il catalogo
  unificato li prende da PCGen).
- **`data_armor.xml` (58)**: `Category` 0 leggera, 1 media, 2 pesante, 3
  scudo, 4 scudo torre, 5 accessorio magico (8 righe "Bracers of Armor +N",
  escluse dai preset e dichiarate). `MaxDex` 99 = nessun cap → `null`.
  `CheckPenalty` è la MAGNITUDINE positiva (5 = ACP -5 RAW): il segno meno è
  applicato in export. `Arcane_Spell` è una frazione (0.3 = 30%).
  `Speed_30ft` -1 = n/a (scudi) → `null`. **Costo assente nel dato.**
- **`data_equipment_slotted.xml` (2.855)**: esportate le 2.783 righe con
  `Name` (tutte `Finished=Yes`): name, cost (mo, anche frazionario; una riga
  con separatore migliaia "25,000" → 25000), slot (codice 0-25), slotLabel,
  source. **72 righe senza Name** sono template di bonus
  (EffectType/BonusType/Amount), non oggetti: saltate e conteggiate
  (`slottedUnnamedSkipped`). 11 righe con Name senza `Slot` → null
  dichiarato. 6 nomi duplicati con slot/fonte diversi (Darkflare,
  Pantograph, Troll styptic, Goblinvine, Leechwort, Winterbite): entrambe
  le voci restano, dichiarati nel report. MAI esportati: `Description` (PI),
  `Ref` (URL d20pfsrd), `BonusType`/`Amount` — l'enhancement magico resta
  preset di nome + stat base, MAI bonus inventato.
- **Mappa slot (dichiarata nel JSON)**: 0 belt, 1 body, 2 chest, 3 eyes, 4
  feet, 5 hands, 6 head, 7 headband, 8 neck, 9 shoulders, 10 wrists, 11
  slotless, 12 ring, 13 rod, 14 staff, 15 adventuring-gear, 16 book, 17
  tool, 18 religious-item, 19 outfit, 20 alchemical-component, 21
  animal-gear, 22 potion, 23 scroll, 24 wand, 25 ammunition.

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
