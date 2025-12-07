# Knowledge Pack — Guida d’Uso + Demo + Prompt (PF1e Master DD)

> **Versione:** v2 • **Data:** 2025-09-04 • **Compatibilità:** Core 3.3+
> **Nota migrazione:** tutti i percorsi ora puntano a **.txt** (niente .yaml).
> **Badge:** [RAW] [RAI] [PFS] 🧠 META [HR]
> **Recupero moduli:** segui il flusso `decidi modalità → GET /modules/{name} (header x-api-key) → riformula` senza duplicare il kernel nel profilo GPT.

---

## 🔗 Risorse Ufficiali

* [Archives of Nethys (AoN)](https://aonprd.com)
* [Paizo](https://paizo.com)
* [d20PFSRD (fallback)](https://www.d20pfsrd.com)

### 📂 Risorse locali (`src/data`)
- Homebrewery Formatting Guide (V3) - The Homebrewery.pdf
- Items Master List.pdf
- The Gear Guide.pdf
- Ultimate Crafter Guide.pdf

---

## 📣 Supporto

Entra nel gruppo Facebook Pathfinder GdR Italia:
👉 [Pathfinder GdR Italia](https://www.facebook.com/groups/pathfindergdritalia)

---

## Indice
1. Quick Start (Guida d’uso)
2. Router & Modalità
3. Comandi rapidi per modulo
4. Regole & Toggle (PFS/ABP/EitR)
5. Output Modes
6. Salvataggi (tavern_hub.json)
7. Troubleshooting & FAQ
8. Demo Conversazione end‑to‑end
9. Prompt Modulari (copincolla)
10. Checklist di Qualità (QA Master)

---

## 1) Quick Start — Guida d’uso
- **Recupero via API (per tutte le modalità):** decidi la modalità → chiama `GET /modules/{name}` con header `x-api-key: <API_KEY>` → leggi il testo e riformula con i badge [RAW]/[RAI]/[PFS]/[HR]/🧠META quando servono.
- **Crea eroe (Quiz Taverna):** “Voglio creare un PG con il quiz (PFS off).” → 3 fasi da 7–10 domande; output su `scheda_pg_markdown_template.md`; poi **/next_step**.
- **Ottimizza (MinMax v5):** `/start_build` → `/set_player_style Spike` → `/toggle_pfs on` → `/bench -q` → `/next_step`.
- **Ruling separato:** “Chiarisci Power Attack con TWF (PFS off).” → TL;DR → RAW → RAI → PFS.
- **Encounter Designer:** “4 PG L6; foresta fitta buio/alture; lupi crudeli + alfa; Difficile.” → CR target, XP, tattiche, varianti ±1 CR, loot PFS‑safe → **Invia al Libro Mastro**.
- **Libro Mastro:** “Aggiungi ricompense e mostra scostamento WBL.” → `/recalc_wbl` → `/shopping_hint 'difesa'`.
- **Explain (6 metodi):** “Spiegami CR misto (APL 6).” → TL;DR → Passi → Diagramma → Analogia → Esempio → RAW/RAI + quiz.

---

## 2) Router & Modalità (percorsi in .txt)
- **Archivist** → `/mnt/data/archivist.txt` — lore canone, tono accademico.
- **Ruling Expert** → `/mnt/data/ruling_expert.txt` — ruling RAW/RAI/PFS separati.
- **Taverna NPC** → `/mnt/data/Taverna_NPC.txt` — quiz PG/party, tono Locandiere.
- **Narrativa** → `/mnt/data/narrative_flow.txt` — storie, scene, ganci.
- **Explain** → `/mnt/data/explain_methods.txt` — 6 metodi didattici.
- **MinMax Builder** → `/mnt/data/minmax_builder.txt` — ottimizzazione v5.
- **Encounter Designer** → `/mnt/data/Encounter_Designer.txt` — CR/XP, terreno, tattiche, loot.
- **Libro Mastro** → `/mnt/data/adventurer_ledger.txt` — WBL/loot/inventario.
- **Documentazione** → `/mnt/data/meta_doc.txt` — manuale & glossario.

---

## 3) Comandi rapidi per modulo
**TAVERNA NPC (quiz/auto/party)**  
- Quiz 3 fasi (7–10 ciascuna). Output: scheda `.md` con psicologia (Jung/OCEAN/Enneagramma), backstory breve, equip base, ruolo consigliato.  
- CTA: `/next_step` (handoff a MinMax).

**MINMAX BUILDER (v5.0)**  
`/start_build` • `/next_step` • `/set_player_style <Timmy|Johnny|Spike>` • `/toggle_pfs <on|off>` • `/toggle_rules pfs=<on/off> abp=<on/off> eitr=<on/off>` • `/update_build {...}` • `/add_level {livello:N, privilegi:"...", talento:"...", note:"..."}` • `/add_spell <livello> ['Inc1','Inc2']` • `/bench -q` • `/run_benchmark` • `/evaluate_choice 'Scelta' '+x% DPR' '±y CA' '⚠/—'` • `/risk_heatmap` • `/qa_check` • `/export_build <pdf|excel>` • `/export_vtt`.

**RULING EXPERT**  
Domanda naturale + PFS on/off → Output: **TL;DR → RAW (pagina/URL) → RAI → PFS Notes → Fonti**.

**ENCOUNTER DESIGNER**  
Input: APL, n PG, bioma/scenario (+tag terreno), nemici/tema, difficoltà, PFS, obiettivi.  
Output: **CR/XP**, elenco nemici (AoN), terreno/visibilità, **tattiche/morale**, varianti ±1 CR, **loot PFS‑safe**, CTA → `/send_to_ledger`.

**LIBRO MASTRO**  
Cassa, inventario, parcels, craft queue, WBL audit.  
`/recalc_wbl` • `/shopping_hint <focus>` • `/export_ledger`.

**ARCHIVIST / NARRATIVA / EXPLAIN / DOC**  
- Archivist: cronologie, fonti, divergenze edizioni.  
- Narrativa: scene e test abilità.  
- Explain: 6 metodi + quiz.  
- Doc: manuale, FAQ, glossario.

---

## 4) Regole & Toggle (PFS/ABP/EitR)
- **Defaults:** pfs=off, abp=off, eitr=off  
- **/toggle_pfs <on|off>**  
- **/toggle_rules pfs=<on/off> abp=<on/off> eitr=<on/off>**  
Linee guida: con **PFS ON** filtra 3PP/HR e marca **[NON PFS]** i contenuti non legali; separa sempre **RAW** da **RAI**.

---

## 5) Output Modes
- **Completo (📚)** — spiegazione estesa *(default)*  
- **Sintesi (🧾)** — 2–5 bullet/paragrafi  
- **Solo Fonti (📎)** — elenco citazioni/fonti  

---

## 6) Salvataggi (tavern_hub.json)
Schema consigliato: `feature_flags` (pfs/abp/eitr), `quiz_runs`, `characters`, `builds`, `encounters`, `ledger` (currency, inventory, policies, wbl_target_level, audit), `vtt_exports`, `snapshots`, `id_counter`, `notes`.  
Linee guida: snapshot prima di export; `sell_rate` default 0.5.

---

## 7) Troubleshooting & FAQ
- **File mancanti / binding errati:** verifica estensioni `.txt` e path.  
- **Encounter non parte:** uniforma nome file a `Encounter_Designer.txt`.  
- **Scheda PG non genera:** `character_sheet_template` deve puntare a `.md`.  
- **PFS ON ma compaiono 3PP:** ricontrolla `/toggle_pfs on` e rigenera l’output.  
- **Badge mancanti in coda:** attiva `seals_parachute: on` nel core.

---

## 8) Demo Conversazione — End‑to‑End
Prima di ogni scena: il GPT sceglie la modalità, chiama `GET /modules/{name}` (header `x-api-key`) e riformula i contenuti; ogni blocco di risposta mantiene i tag [RAW]/[RAI]/[PFS]/[HR]/🧠META coerenti con le fonti.

**Scena 1 — Taverna (Quiz PG)**
Utente: “Voglio creare un PG con il quiz, tono low‑fantasy, niente 3PP, PFS off. Stile Spike.”
Assistente [META]: avvio quiz 3×(7–10 domande); CTA → `/next_step`.
Output: scheda su `scheda_pg_markdown_template.md` con stats, ruolo, backstory breve, equip base.

**Scena 2 — Ruling Expert**
Utente: “Power Attack con fauchard e due armi. PFS off.”
Risposta [RAW][RAI]:
- **TL;DR**: malus PA su entrambe le mani; bonus danni scala 2H (×1.5), non si duplica sulla off‑hand.
- **RAW**: CRB p.113–114; FAQ Paizo.  
- **RAI**: note sullo scaling 2H/TWF.  
- **PFS**: (off) nessun vincolo.  
- **Fonti**: CRB; AoN.

**Scena 3 — Encounter Designer**
Utente: “4 PG L6; foresta fitta, buio/alture; lupi crudeli + alfa (Jezelda); Difficile; PFS off.”
Output: **APL 6 → CR 8 (Difficile), XP 4.800**; nemici (3× Dire Wolf CR3 + 1× Werewolf Alpha CR6); ambiente (−5 Percezione, alture +1, sottobosco MD); **tattiche** (flanking & trip; alfa in copertura alta; ululato); **morale** (ritirata <30% PF); **varianti** (CR 7/9); **loot PFS‑safe** (pozioni CL3, frecce d’argento, talismano boschivo).
CTA: `/send_to_ledger auto` o `/export_vtt`.

**Scena 4 — Libro Mastro**  
Utente: “Aggiungi loot e mostra scostamento WBL.”  
Output: cassa +1.250 gp equivalenti (sell_rate 0.5 dove applicabile); Δ vs WBL L6 (16.000 gp): media party 15.200 gp (−5%); suggeriti 3 upgrade difensivi.  
CTA: `/recalc_wbl` → `/shopping_hint 'difesa'`.

**Scena 5 — Explain (6 metodi)**  
Utente: “CR misto (APL 6).”  
Output: 1) TL;DR 2) Passi 3) Diagramma 4) Analogia 5) Esempio 6) RAW vs RAI + 3 quiz lampo.

---

## 9) Prompt Modulari — Copia/Incolla
### 9.1 RULING EXPERT — RAW/RAI/PFS
[badge] [RAW][RAI][PFS] • [tono] tecnico  
**Istruzioni:** separa **RAW** (letterale) da **RAI** (FAQ/dev). Con **PFS ON** filtra non‑legali e marca **[NON PFS]**.  
**Prompt**
```
Contesto tavolo: <campagna/HR>
Domanda: <testo regola>
Edge cases: <casi limite>
PFS: <on/off>
```
**Output atteso:** 🧾 TL;DR • 📕 RAW (pagina/URL) • 🛠 RAI • 🛡 PFS • 📎 Fonti

### 9.2 ARCHIVIST — Lore ufficiale
[badge] [RAW][META] • [tono] accademico  
**Prompt**
```
Tema: <regione/NPC/divinità/evento>
Periodo: <anno/era>
Profondità: <breve/medio/approfondito>
PFS: <on/off>
```
**Output atteso:** riassunto canone; cronologia; riferimenti; box “Divergenze edizioni”.

### 9.3 TAVERNA NPC — Quiz/PG/Party
[badge] 🧠 META (+ [RAW] dove serve) • [tono] Locandiere  
**Prompt**
```
Obiettivo: <quiz PG / autogenerazione / allineamento party>
Vincoli: <razze/classi vietate, PFS on/off>
Extra: psicologia, backstory breve, equip base, ruolo consigliato, suggerimenti interpretativi.
```
**Output atteso:** scheda pronta `scheda_pg_markdown_template.md`; quiz 3×(7–10 domande).

### 9.4 MINMAX BUILDER — Ottimizzazione v5
[badge] 🧠 META (+ [RAW] per riferimenti) • [tono] tecnico  
**Shortcut** `/start_build → /set_player_style <Spike|Johnny|Timmy> → /toggle_pfs on/off → /next_step → /bench -q`  
**Prompt**
```
Ruolo/Classe: <es. Striker / Slayer>
Stile giocatore: <Spike/Johnny/Timmy>
Vincoli: <PFS on/off; ABP/EitR>
Fonti: <manuali ammessi, HR>
```
**Output atteso:** build card + benchmark quick (DPR early/late, Defense, Scaling); badge META per ogni consiglio.

### 9.5 ENCOUNTER DESIGNER — CR/XP, Terreno, Tattiche
[badge] [RAW][PFS] + 🧠 META • [tono] pratico  
**Prompt**
```
APL party: <valore> (PG: <n>, L medio <L>, gear ~WBL)
Bioma/Scenario: <foresta/urbano/dungeon…> + Tag: <buio, alture, acqua, coperture, stretti>
Tema/Nemici: <famiglia/creature>
Difficoltà: <Facile/Media/Difficile/Letale>
PFS: <on/off>
Obiettivi narrativi: <inseguimento, difendere PNG, timer>
```
**Output atteso:** CR/XP, tattiche/morale, varianti ±1 CR, loot PFS‑safe, hook ➜ Libro Mastro.

### 9.6 LIBRO MASTRO — WBL/Loot/Inventario
[badge] [PFS][RAW] + 🧠 META • [tono] contabile  
**Prompt**
```
Valute iniziali: <pp/gp/sp/cp>
Inventario chiave: <oggetti>
Movimenti: <voce|Δ gp|fonte|PFS>
Obiettivo WBL: <target liv>
```
**Output atteso:** Cassa; Valore investito; Δ vs WBL; Movimenti; Parcels; Coda Crafting; Audit & PFS.

### 9.7 NARRATIVA — Storie/Archi/Scene
[badge] 🧠 META • [tono] evocativo  
**Prompt** `Tema · Scena (setup/obiettivo/conflitto) · Vincoli (PG/PNG, ambientazione)`  
**Output atteso:** trama 3 atti / scene pronte; spunti test abilità.

### 9.8 EXPLAIN — Sei Metodi
[badge] 🧠 META DIDATTICO • [tono] tutor  
**Prompt** `Tema · Livello: ELI5/Intuitivo/Procedurale/Algoritmico/Con esempi/Tecnico`  
**Output atteso:** 1) TL;DR 2) Passi 3) Diagramma 4) Analogia 5) Esempio 6) RAW vs RAI + quiz.

---

## 10) Checklist di Qualità (QA Master)
**Generale**  
- [ ] Badge corretti in output: [RAW], [RAI], [PFS], 🧠 META, [HR].  
- [ ] Fonti citate con pagina/URL (AoN, CRB, FAQ).  
- [ ] Separazione **RAW vs RAI vs META vs HR**.  
- [ ] **PFS toggle** rispettato (filtra e marca [NON PFS]).  
- [ ] Sigilli coerenti con modalità.

**Taverna NPC**  
- [ ] Quiz 3×(7–10) domande, non ripetitive.  
- [ ] Scheda `scheda_pg_markdown_template.md` completa.  
- [ ] Psicologia + backstory + ruolo consigliato presenti.

**Ruling Expert**  
- [ ] Struttura: TL;DR → RAW → RAI → PFS → Fonti.  
- [ ] RAW con pagina/URL AoN.  
- [ ] RAI da FAQ/dev, non ipotesi.  
- [ ] PFS ON: marchiatura **[NON PFS]** dove dovuto.

**MinMax Builder**  
- [ ] Flusso a step rispettato; benchmark (early/late) eseguito.  
- [ ] Export bloccato se QA fail.  
- [ ] Build card: DPR, CA, Saves, Scaling, meta_tier.

**Encounter Designer**  
- [ ] APL→CR/XP corretti; nemici con ref AoN.  
- [ ] Terreno/visibilità + **tattiche/morale**.  
- [ ] Varianti ±1 CR.  
- [ ] Loot PFS‑safe + hook Libro Mastro.

**Libro Mastro**  
- [ ] WBL audit aggiornato; Δ vs target livello.  
- [ ] Parcels registrati; inventario con peso/carico.  
- [ ] Shopping hints utili (difesa/attacco/utility).

**Explain**  
- [ ] 6 metodi presenti; diagramma leggibile; quiz finale.

— **FINE KNOWLEDGE PACK v2** —

