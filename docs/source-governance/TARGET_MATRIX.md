# TARGET MATRIX — Source Governance v1

Questa matrice mappa i file “target” del repository ai requisiti della policy **Source Governance v1**.

> Nota: in questo repo esistono due copie dei moduli (in `src/modules/` e `src/data/modules/`).
> Le modifiche sono state applicate in modo speculare ad entrambe.

---

## Core / Base Profile

| Target | File | Modifica | Marker |
|---|---|---|---|
| System prompt (core) | `gpt/system_prompt_core.md` | Inserita sezione “Source Governance v1” (STEP -1 META-SEARCH, STEP 0 RAW anchoring, 4 gate, breadcrumb, divieti). | `SOURCE_GOVERNANCE_V1` |
| Base profile (principles) | `src/modules/base_profile.txt` | Aggiunta `principles.source_governance_v1` (testo vincolante per l’intero sistema). | `SOURCE_GOVERNANCE_V1` |
| Base profile (data mirror) | `src/data/modules/base_profile.txt` | Come sopra (copia speculare). | `SOURCE_GOVERNANCE_V1` |

---

## Ruling Module

| Target | File | Modifica | Marker |
|---|---|---|---|
| Ruling Expert | `src/modules/ruling_expert.txt` | Inserita policy: META solo discovery e citabile solo dopo STEP 0; divieto di verdetti senza RAW; breadcrumb obbligatoria. | `SOURCE_GOVERNANCE_V1` |
| Ruling Expert (data mirror) | `src/data/modules/ruling_expert.txt` | Come sopra (copia speculare). | `SOURCE_GOVERNANCE_V1` |

---

## Minmax / Optimization Module

| Target | File | Modifica | Marker |
|---|---|---|---|
| Minmax Builder | `src/modules/minmax_builder.txt` | Policy in `constraints` + breadcrumb/verdetto automatici quando `fonti_meta` contiene sorgenti META (helper + output). | `SOURCE_GOVERNANCE_V1` |
| Minmax Builder (data mirror) | `src/data/modules/minmax_builder.txt` | Come sopra (copia speculare). | `SOURCE_GOVERNANCE_V1` |

---

## Explain Module

| Target | File | Modifica | Marker |
|---|---|---|---|
| Explain Methods | `src/modules/explain_methods.txt` | STEP 0 (RAW anchoring) obbligatorio prima di spiegazioni tecniche su regole/feat/spell/item; META solo dopo STEP 0 e come contesto. | `SOURCE_GOVERNANCE_V1` |
| Explain Methods (data mirror) | `src/data/modules/explain_methods.txt` | Come sopra (copia speculare). | `SOURCE_GOVERNANCE_V1` |

---

## Templates / Rendering / Output

| Target | File | Modifica | Marker |
|---|---|---|---|
| Scheda PG markdown template | `src/modules/scheda_pg_markdown_template.md` | Breadcrumb line condizionale: appare **solo** se sono presenti fonti META. | `SOURCE_GOVERNANCE_V1` |
| Template (data mirror) | `src/data/modules/scheda_pg_markdown_template.md` | Come sopra (copia speculare). | `SOURCE_GOVERNANCE_V1` |
