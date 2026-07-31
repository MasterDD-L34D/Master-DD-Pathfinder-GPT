# WORKFLOW — come lavoriamo su Master-DD-Taverna

> Metodo consolidato nelle sessioni 2026-07-18/19 (lotti 1-4, Fasi 1-3, feat effects). Da leggere insieme a `AGENTS.md` (regole del repo) e `docs/IMPORT_PLAYBOOK.md` (metodo per gli import dati). Per il contesto cross-repo: `tooling/pathmaster-dd/docs/superpowers/`.

---

## 1. Il ciclo di lavoro (lotto)

1. **Analisi** — gap reale misurato (codice, dati, test), mai assunto. Deliverable: cosa promette vs cosa fa.
2. **Piano TDD completo** (`writing-plans`): task bite-sized con **codice completo in ogni step** (niente placeholder), file esatti, comandi con output atteso, self-review prima di presentarlo. Piani in `planning/YYYY-MM-DD-<feature>.md`, committati.
3. **Esecuzione subagent-driven**: per OGNI task, un implementer fresco (contesto curato dal controller, niente plan file da leggere — testo completo nel prompt), poi **due review indipendenti**:
   - **Spec review**: l'implementazione corrisponde alla spec? (verifica su file reali, non sul report)
   - **Quality review**: è ben costruita? (test eseguiti, edge case, convenzioni)
   - Fix loop fino ad approvazione; il controller verifica ogni fix (grep + test, non fidarsi del report).
4. **Final review** dell'intero lotto (coerenza end-to-end, use case reale, regressioni, igiene) → fix finali.
5. **Verifica rituale** (sempre, con evidenza fresca): `python launch.py test` → TUTTE LE VERIFICHE OK; `legal_filter` 0; `validate_schemas` 0; YAML-check dei moduli `.txt` toccati; reindice RAG se toccati moduli o dati reference.
6. **Push + handoff**: aggiornare `sessione-2026-07-16/HANDOFF_ATTIVO.md` (timestamp, riga stato, voce completato).

## 2. Le review come rete — cosa hanno trovato davvero

Non cerimonie: ogni lotto recente ha avuto bug veri intercettati solo dalle review indipendenti.

- **Bug di regole (RAW)**: conteggio talenti base sbagliato ai livelli pari (`1 + level//2` invece di `(level+1)//2`); Toughness non scalato oltre lv3; "class level 1st" rifiutato a lv1; Monk senza bonus feat; armature multiple bloccanti; taglia Small ignorata.
- **Bug di dati**: ~75% di attribuzioni fonte errate (equipment); 43+ occorrenze PI Golarion sfuggite al filtro base; prerequisiti autoreferenziali; Knowledge senza cross-ref (case/`(all)`).
- **Bug di test**: test che passano solo con il `.env` locale (fixture non ermetica); valori attesi calcolati male (AC, saves, skill totals); trappole `class` vs `class_` nei draft helper.
- **Bug di documentazione**: docstring che dichiarano il falso dopo una feature (limitazione effetti talenti), elenchi kind non aggiornati, nome file errato (`equipment.json` vs `equipment_mundane.json`).

Regola: **un'implementazione non è "pronta" finché una seconda testa non l'ha verificata su file e comandi reali.**

## 3. Policy commit (hook commit-guard attivo)

- Conventional Commits: `type(scope): subject` ≤ 72 char, minuscolo iniziale, niente punto finale.
- **MAI `Co-Authored-By:`** (bloccato dall'hook, ADR-0011 policy-C).
- **ADR-0011 (adottato il 2026-07-19)**: ogni commit include i trailer
  `Coding-Agent: <agent-id>` e `Trace-Id: <uuidv7>`. **Dal 2026-07-25 sono BLOCCANTI**
  (coda D3): l'hook commit-msg globale (`~/.local/share/git-hooks/commit-msg`) rifiuta
  i commit senza trailer su tutti i repo sotto `C:/dev/pathfinder` (scoped per path;
  gli altri repo non cambiano). Bypass documentato: `git commit --no-verify`.
  Commit sempre via `git commit -F <file>`.
- **Mai riscrittura della storia**: la policy vale da adesso in poi; i commit precedenti restano com'erano.

## 4. Il contratto del builder (`src/pc/`)

Il builder deterministico è consumato dall'harness a tre vie di pathmaster-dd come terzo oracolo. Regole di evoluzione:

- **Default che decidono numeri: sempre DICHIARATI** nel codice (commento) e in README/docstring (es. `favored_class_bonus: "hp"` di default, `hp_method: "average"` PFS, euristica ranged `< 30 ft`, floor skill 1, WBL best-effort a lv>1, lista `FINESSE_WEAPONS` curata).
- **Cambi di forma input/output: segnalati** (changelog del modulo + nota in commit body) — un adapter si aggiorna, una rottura silenziosa avvelena l'oracolo.
- **Filosofia: valida-e-boccia, mai aggiustare in silenzio.** Errori bloccanti per input illegali; warning per best-effort dichiarati; niente correzioni silenziose dei draft.
- **Limitazioni sempre esplicite** in docstring + README (cosa il motore NON modella: effetti talenti non in `feat_effects.py`, archetipi, multiclasse, effetti condizionali).

## 5. Punti di contatto cross-repo (pathmaster-dd)

| Canale | Stato | Note |
|---|---|---|
| **Terzo oracolo differenziale** (v1 \| v2 \| builder Taverna) | ✅ TOOL VERSIONATO (REF-07 chiuso 2026-07-31; nato spike 2026-07-19) | Il builder ha trovato 2 bug RAW comuni ai due motori pathmaster (favored class "none", conteggio feat lv1); post-fix i tre concordano sui 7 build confrontabili. Invariante feat-count adottato in entrambi i loro `feat-slots.ts` con credito. Evoluzione contratto 2026-07-19 (commit `a7842e4`): nuovo campo opzionale `spells` nel draft (default `[]`); sheet con chiave `spells` solo se la selezione è non vuota; draft senza `spells` → output invariato. |
| **Leva 2 import** (cataloghi Taverna → `UNMODELED_DATA` v2) | Aperto, basso valore ora | I 2839 feat OGL possono popolare/verificare il perimetro unmodeled. |
| **Chronicle M2-B dizionario campagna** | Futuro | I cataloghi OGL (PI già pulita) come seme vocabolario PF1e. |
| **Regola ground-truth condivisa** | Permanente | Doc = ipotesi; git + SRD = verità. La concordanza a tre NON è correttezza: nei disaccordi si apre il SRD, non si vota a maggioranza. |
| **Copertura oracolo** | **29/29 raggiunta; rilancio ESEGUITO** | 2026-07-25 sera: rilancio completo sulle 28 build base (`tools/oracle-three-way.mjs` + `tools/oracle_three_way.py`, report `reports/oracle_three_way.md`). **2 bug condivisi v1+v2 trovati e fixati** (`99f72c4`: kasatha abilityAdjustments str/wis/int−2 → **dex/wis** da AoN; hunter BAB "full" → **threeQuarter**): hunter_kasatha tornata CONCORDE. Stati finali: 2 concorde, 1 diverge (nota: limite dichiarato engine Taverna — effetti talenti fuori modello, §4), 10 `FUORI_BUDGET_GPT` (point-buy 26–41 > 25: stats illegali corpus), 10 `FEAT_ILLEGALE_GPT` (conteggio talenti > RAW a lv1, nota spike), 2 `PREREQ_ILLEGALE_GPT` (prerequisito non soddisfatto), 4 flex indeterminato, 3 statline duplicate (A4: fighter_dwarf = druid_half_orc = ranger_halfelf). **Decisione C (2026-07-25)**: registry `src/data/builds/_oracle_defects.json` (26 build flaggate, rigenerato dall'oracolo) = sottoinsieme legale per i test dei motori; ricostruzione onesta del corpus = lotto futuro (A). |
| **Tool oracolo: uso e perimetro (REF-07, 2026-07-31)** | Versionato e testato | Catena completa: `cd pathmaster-dd && ./node_modules/.bin/tsx tools/oracle-three-way.mjs` (dump `data/reference/oracle-three-way.json`, 28 build base) → `.venv/Scripts/python tools/oracle_three_way.py` (default **read-only**, stampa il report) \| `--write` (rigenera `reports/oracle_three_way.md` + registry difetti) \| `--check` (gate: exit 1 se il registry su disco è in drift). Test propri: `tests/test_oracle_three_way.py` (15 test: normalizzazioni, classi difetto, contratto CLI, smoke catena reale). **Perimetro L1 strutturale**: le varianti `_lvl05/_lvl10` (84 file totali) non sono oracolate perché per contratto lotto A portano input L1 (statline lv1, solo talenti lv1, `classi[].livelli=1`) con derivati ricalcolati dal builder — il livello target vive solo in `rebuild_gpt_a.livello`; oracolarle richiede un lotto dedicato (contratto corpus con livello dichiarato + metodo HP dei motori a lv>1), non un ritocco dell'harness. Razze esotiche: già coperte (kasatha/strix/tengu/shabti/kitsune/vanara/grippli/vishkanya/suli/oread/wayang/fetchling/catfolk/samsaran nel corpus, tutte nel catalogo OGL del builder). |

### 5.1 Lotto A (G1) — tabella decisioni rebuild corpus GPT-A (2026-07-27)

Decisioni controller 2026-07-25 (congelate): budget point-buy **25 (Epic Fantasy)**; talenti centrali tenuti, accessori droppati, prerequisiti RAW al livello; sostituzioni dichiarate; statline duplicate ridisegnate 25pb editoriali; flex dichiarato via contratto `sheet_payload.bonus_razziale_flessibile` (E6-A6); derivati (PF/TS/CA/BAB/skill) ricalcolati dal builder `src/pc`, mai mantenuti GPT-A. La stessa tabella vive come dati auditabili (`DECISIONS`) in cima a `tools/rebuild_corpus_gpt_a.py` (dry-run `--dry-run`, backup in `src/data/builds/archive/`, idempotente; test `tests/test_rebuild_corpus_gpt_a.py`).

| Build | Difetti | Correzione |
|---|---|---|
| alchemist-goblin-vivisectionist | feat_count | tieni Iniziativa migliorata; droppa Colpo possente (RAW Forza 13, FOR 12) |
| alchemist_goblin_bombardier | feat_count | tieni Iniziativa migliorata; droppa Colpo possente (mischia, off-concept bombe) |
| arcanist_tiefling_hexcrafter_blood_arcanist | feat_count | tieni Spell Focus (maledizioni) (hex); droppa Accuratezza Magica |
| barbarian_fetchling_invulnerable_rager | feat_count | tieni Colpo possente (FOR 16, BAB pieno); droppa Iniziativa migliorata |
| bard_kitsune_sound_striker_sandman | stats 31pb | nuova 8/14/13/12/10/18 (25pb, CAR); latente: 3 talenti → tieni Focalizzazione Abilità: Intrattenere, droppa Armonia Letale + Scacciare Sogni (prereq Perform 5/3 gradi, illegali lv1) |
| bloodrager-shabti-steelblood-metamagic-rager | feat_count | tieni Colpo possente; droppa Iniziativa migliorata |
| brawler_grippli_mutagenic_mauler_strangler | stats 29pb | nuova 16/16/14/10/13/7 (24pb, FOR/DES) |
| cavalier_strix_strategist_honor_guard | stats 33pb | nuova 17/13/14/12/10/12 (25pb, FOR primaria, CAR strategist) |
| cleric_samsaran_cloistered_evangelist | feat_count | tieni Iniziativa migliorata; droppa Colpo possente (concept bardico) |
| druid_half_orc_feral | flex + duplicata | NUOVA 15/13/14/10/17/7 (24pb, SAG) + flex SAG → SAG 19; latente: 2 talenti → tieni Iniziativa migliorata |
| druid_wayang_mooncaller_shapeshifter | feat_count | tieni Iniziativa migliorata; droppa Colpo possente (RAW BAB +1, BAB +0) |
| fighter_dwarf_shielded | duplicata | tiene statline 16/14/14/10/12/8 (20pb) e i 2 talenti (slot fighter 3): legale |
| fighter_weapon_master_human | flex | statline invariata (20pb); flex FOR → FOR 18 |
| gunslinger_strix_gun_tank | stats 27pb | nuova 13/17/14/10/14/8 (24pb, DES/COS) |
| gunslinger_tengu_pistolero_bolt_ace | stats 26pb | nuova 12/18/13/10/14/8 (25pb, DES bolt ace) |
| investigator_catfolk_empiricist_psychic_detective | stats 40pb | nuova 10/16/12/17/12/8 (25pb, INT) |
| kineticist_strix_kinetic_knight_overwhelming_soul | stats 33pb | nuova 12/16/13/10/10/16 (25pb, CAR/DES) |
| kineticist_suli_kinetic_knight_overwhelming_soul | stats 41pb | nuova 14/14/13/8/10/17 (24pb, CAR) |
| magus_kitsune_bladebound_hexcrafter | stats 27pb | nuova 10/16/13/16/10/12 (25pb, INT/DES); sheet_payload.statistiche era assente: ora garantito |
| medium_oread_spirit_dancer_reanimated_medium | feat_count | tieni Iniziativa migliorata; droppa Colpo possente (concept caster) |
| monk_vanara_qinggong_master_of_many_styles | feat_count + prereq | 4→2: Tiger Style → **Scorpion Style** (sostituzione dichiarata; prereq IUS concesso monk), Crane Style → **Dodge**; droppata voce combinata "Tiger Style + Crane Style" (non in catalogo) |
| ranger_halfelf_skirmisher | flex + duplicata | NUOVA 14/17/13/10/14/8 (24pb, DES) + flex DES → DES 19; latente: 2 talenti → tieni Iniziativa migliorata |
| rogue_halfling_cutpurse | prereq | Arma accurata → **Skill Focus (Sleight of Hand)** (sostituzione dichiarata; BAB +1 irraggiungibile al lv1, reintegro lv3) |
| witch_sylph_gravewalker_hedge_witch | stats 34pb | nuova 8/14/12/18/12/10 (24pb, INT) |
| wizard_elf_universalist | feat_count | tieni Iniziativa migliorata; droppa Colpo possente (concept caster) |
| wizard_human_evoker | flex | statline invariata (20pb legale, editoriale povera: dichiarato); flex INT |

Limiti dichiarati del rebuild: archetipi non modellati dal builder (restano flavor); aumenti caratteristica lv4/8 non modellati (varianti _lvl05/_lvl10 tengono la statline del lv1); varianti ereditano i talenti corretti del lv1 (scelta legale a ogni livello), `progressione[lv>1].talenti = []`; equip/inventario/attacco/danni/velocità restano flavor GPT-A (builder senza equip: CA = 10 + DES + taglia); skill GPT trattate come scelte (nomi IT→EN mappati, gradi = livello fino a budget, totali dal builder; "Conoscenze" generico droppato).

**Esito stadio B (2026-07-27)**: rebuild eseguito su tutte le 26 build (78 file, backup in `archive/`), dump e oracolo rilanciati: **registry difetti VUOTO**, 28 build base → 17 concorde a tre, 11 diverge, 0 errori. Le 11 divergenze sono residue engine dichiarate (NON difetti di corpus): 4 build divergono perché v1 modella capacità di classe sempre-attive (Mutagen sui due alchemist e sul brawler mutagenic mauler, Rage sul barbarian, Bloodrage+Mutagen sul bloodrager) — limite dichiarato del builder Taverna (§4, effetti fuori modello); 7 build divergono per sospetti bug dei cataloghi engine v1+v2 (da verificare su AoN in un lotto engine dedicato, NON nel lotto corpus): Strix `wis +2` (RAW: solo +2 Des/−2 Car), Tengu `str −2` (RAW: −2 Cos), Kineticist `ref poor` (RAW: good), Monk `bab full` (RAW: 3/4), Shabti `int −2` (da verificare). Allineamento contratto E6-A6: il dump `oracle-three-way.mjs` legge `bonus_razziale_flessibile` e lo inietta nel personaggio v1 (v1 non modella il flex); l'oracolo python usa la scelta dichiarata invece di indovinarla dallo sheet. Fix collaterale builder: alias `Iniziativa migliorata` → Improved Initiative in `feat_effects` (v2 applicava già il +4). I test pathmaster che pinnavano i vecchi difetti di corpus (`converter-warnings`, `converter-feat-count`) sono da migrare nello stadio C.

## 6. Come si riprende in futuro (checklist)

1. Leggi `sessione-2026-07-16/HANDOFF_ATTIVO.md` (stato corrente) e `AGENTS.md`.
2. Se importi dati: `docs/IMPORT_PLAYBOOK.md` (pattern, trappole, PI, checklist registrazione).
3. Se tocchi il builder: rispetta il contratto in §4; se tocchi `src/modules/`: rituale YAML → reindice → test → handoff.
4. Esegui col ciclo in §1; le review non si saltano; i commit seguono §3.
5. Prima di dichiarare qualcosa "fatto": evidenza fresca del comando di verifica (mai dal report).

---

*Creato il 2026-07-19 dopo l'ingaggio da pathmaster-dd (`docs/superpowers/specs/2026-07-19-handoff-kimi-terzo-oracolo.md`).*
