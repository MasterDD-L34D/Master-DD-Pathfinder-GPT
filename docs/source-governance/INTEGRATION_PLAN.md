# Integration Plan — Source Governance v1 (repo + Codex)

Questo documento guida l’integrazione della policy **Source Governance v1** nel repository (config/moduli/template).

## Obiettivo
- Evitare inferenze su regole PF1e senza consultare il testo ufficiale
- Rendere l’uso di fonti META **trasparente, controllato e classificato**
- Standardizzare discovery (query) e reporting (breadcrumb + verdict)

## Input richiesti
- Repo con file di configurazione/moduli/template
- File policy: `docs/source-governance/SOURCE_GOVERNANCE.md`

## Output attesi (deliverable)
1) Aggiunta documentazione:
   - `docs/source-governance/SOURCE_GOVERNANCE.md`
   - (opz.) `docs/source-governance/QA_EXAMPLES.md`
2) Modifiche ai file core/moduli/template con blocchi idempotenti
3) `CHANGELOG.md` con mappa modifiche
4) `QA_REPORT.md` con check automatici e test end-to-end

---

## Fase A — Repo discovery & Target Matrix
1) Scansiona repo per trovare:
   - file core (principles/sources/router/policies)
   - modulo ruling (RAW/RAI/PFS)
   - modulo minmax (build/benchmark/optimization)
   - modulo explain (metodi didattici)
   - template di output (rendering/format)
2) Produce `TARGET_MATRIX.md` (file → patch prevista).

Criterio di accettazione:
- ogni componente deve avere almeno 1 file target (o fallback dichiarato).

---

## Fase B — Patch idempotenti (sentinel)
Regola: ogni inserzione deve essere racchiusa da marker:

- `# BEGIN SOURCE_GOVERNANCE_V1`
- `# END SOURCE_GOVERNANCE_V1`

Così il patching è idempotente e reviewabile in PR.

---

## Fase C — Cosa inserire (per componente)

### 1) Core/Base profile
Inserire:
- STEP -1 (META-SEARCH) come discovery: output `META-CANDIDATE`
- STEP 0 (RAW anchoring) come prerequisito bloccante per verdict su combo/build/regole
- divieto esplicito di inferenze “a memoria” su feat/spell/item
- riferimento a breadcrumb e classificazione finale quando META usato

### 2) Ruling module
Inserire:
- META citabile solo dopo STEP 0 e solo come contesto (mai per determinare RAW)
- se META contraddice RAW: `RAW-INCOMPATIBLE` o `HR` (se richiesto)
- output: separazione RAW/RAI/PFS invariata

### 3) MinMax module
Inserire:
- se entra META: breadcrumb obbligatorio
- verdict obbligatorio: `RAW-COMPLIANT / RAW-AMBIGUOUS / RAW-INCOMPATIBLE`
- regole automatiche:
  - autore sconosciuto → max `RAW-AMBIGUOUS`
  - prereq/stacking non chiari → `RAW-AMBIGUOUS`
  - contraddice AoN/Errata → `RAW-INCOMPATIBLE`

### 4) Explain module
Inserire:
- prima di spiegazioni tecniche su regole/feat/spell/item: richiedere STEP 0
- se STEP 0 non completabile: dichiarare limite e proporre ricerca/citazione

### 5) Templates / Rendering
Inserire hook condizionale:
- se META presente → stampa breadcrumb + verdict
- se META assente → nessuna riga aggiunta

---

## Fase D — QA
Eseguire:
- grep marker: ogni `BEGIN/END SOURCE_GOVERNANCE_V1` una sola volta per file
- lint sintassi (YAML/JSON) se applicabile
- test end-to-end manuale (prompts):
  1) "Ho trovato una build online che dice X, funziona?"
     - deve comparire breadcrumb
     - deve comparire verdict
     - deve dichiarare STEP 0 (AoN/Paizo consultati)

---

## Note operative per Codex
- Preferire PR con commit piccoli e descrittivi
- Non modificare logica non correlata al governance
- Aggiornare `CHANGELOG.md` con: file, sezione, motivo, impatto
