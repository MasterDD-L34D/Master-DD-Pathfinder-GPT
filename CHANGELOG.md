# Changelog

Questo file riassume le modifiche rilevanti introdotte dall’integrazione di **Source Governance v1**.

## 2025-12-17 — Source Governance v1

### Policy core
- `gpt/system_prompt_core.md`: aggiunta sezione **Source Governance v1** con STEP -1 (META-SEARCH) e STEP 0 (RAW anchoring AoN/Paizo), 4 gate, breadcrumb obbligatoria, divieti di inferenza senza RAW.

### Moduli
- `src/modules/base_profile.txt` + `src/data/modules/base_profile.txt`: aggiunto principio `source_governance_v1` (policy obbligatoria per regole/combo/build).
- `src/modules/ruling_expert.txt` + `src/data/modules/ruling_expert.txt`: vincolato l’uso di META (solo dopo STEP 0 come contesto) e reso obbligatorio RAW anchoring prima del verdetto.
- `src/modules/explain_methods.txt` + `src/data/modules/explain_methods.txt`: reso obbligatorio STEP 0 prima di spiegazioni tecniche su regole/feat/spell/item.
- `src/modules/minmax_builder.txt` + `src/data/modules/minmax_builder.txt`: integrazione governance in constraints + breadcrumb/verdetto quando entra META.

### Template/output
- `src/modules/scheda_pg_markdown_template.md` + `src/data/modules/scheda_pg_markdown_template.md`: breadcrumb automatica **solo quando** `fonti_meta` contiene elementi META (rilevazione robusta su `level`/`tipo`/`badge`).

### Documentazione
- `docs/source-governance/SOURCE_GOVERNANCE.md`: policy ufficiale.
- `docs/source-governance/INTEGRATION_PLAN.md`: piano di integrazione.
- `docs/source-governance/TARGET_MATRIX.md`: matrice file → requisiti/modifiche.
- `docs/source-governance/QA_EXAMPLES.md`: esempi QA (2).
- `docs/source-governance/QA_REPORT.md`: report QA.