# Piano C2 task 2 — sotto-cataloghi talenti (rage powers, mercy, rogue talents, ...)

Data: 2026-07-26. Coda: `AVVIO_PROSSIMA_SESSIONE.md` §5.0 C2 task 2.
Task 1 (chiuso, `024edf6`): `mechanics.features` core con testo su 35 classi.
Task 2 (questo piano): i **talenti selezionabili** (liste di opzioni per classe)
che vivono su pagine dedicate AoN, non nella sezione Class Features.

## Scope

Sette pool (dalla coda: "rage powers, mercy, rogue talents, discoveries, hexes,
ki powers, deeds"):

| Pool | Classe | Fonte AoN (verificata 200 il 2026-07-26) |
|---|---|---|
| rage power | Barbarian | `BarbarianRagePowers.aspx` |
| mercy | Paladin | `PaladinMercies.aspx` |
| rogue talent | Rogue | `RogueTalents.aspx` |
| discovery | Alchemist | `AlchemistDiscoveries.aspx` |
| hex | Witch | `WitchHexes.aspx` |
| deed | Swashbuckler | `SwashbucklerDeeds.aspx` |
| ki power | Monk (Unchained) | `ClassDisplay.aspx?ItemName=Monk%20(Unchained)`, sezione "Ki Powers (Su)" |

Fuori scope (residui documentati, classi non in catalogo o lotti futuri):
ninja tricks (Ninja non in classes.json), magus arcana, oracle mysteries,
sorcerer bloodlines, advanced rogue talents se pagina/sezione separata
(valutare: se nella stessa pagina RogueTalents.aspx includerli come pool
"advanced rogue talent").

## Decisioni

- **Nuovo catalogo** `data/reference/ogl/talents.json` (pattern feats/spells),
  NON dentro classes.json: i talenti sono entry autonome ricercabili dal RAG
  e riusabili dal builder; classes.json resta il riassunto per classe.
- **Schema entry** (allineato ai cataloghi esistenti):
  `name`, `source`, `source_id`, `prerequisites` (dal testo "Prerequisite(s)"),
  `tags` (`["talent", <pool-tag>]` + tag fonte come da convenzione),
  `references`, `reference_urls`, `description` (testo regola sanitizzato),
  `mechanics`: `{class, pool, kind}` con `kind` = Ex|Su|Sp|null dal suffisso
  "(Ex)/(Su)/(Sp)" nel nome (tolto dal nome, come archetipi/features).
- **PI gate**: `is_pi_name` (da `tools/expand_spells_gist.py`, come archetipi).
  Nomi PI → `pi_local_only/talents_local.json` verbatim; description
  sanitizzata con `sanitize_text` nel catalogo OGL. Gate `legal_filter` = 0.
- **Tool nuovo** `tools/import_talents.py` (pattern `import_archetypes.py`):
  dry-run di default, `--write`, `--offline`; fetch via
  `tools/reference_fetch.py` (cache); parser per pagina dove il markup diverge.
- **Manifest**: kind `talents` (+ `talents_local` se PI), note aggiornate.
- **Test**: `tests/test_import_talents.py` — parser offline su fixture HTML
  reali (da cache) per almeno 2 pool di markup diverso + invarianti catalogo
  (dedup (pool, name), source_id unici, kind ammessi).
- **Chiusura lotto**: reindice incrementale (`tools/index_rag.py --include-local`),
  `python launch.py test` OK, legal_filter 0, validate_schemas 0;
  doc `docs/IMPORT_PLAYBOOK.md` §6.10; report qualità rigenerato.

## Rischi

- Markup eterogeneo tra le 7 pagine (tabelle vs elenchi `<b>`): parser
  per-pool con fixture, mai inventare campi assenti in fonte (text vuoto =
  assenza onesta, convenzione lotti precedenti).
- Pagina Monk (Unchained): la sezione "Ki Powers (Su)" e' dentro la pagina
  classe — estrarre solo quella sezione, non ri-importare le class features.
- Rage powers pagina AoN: verificare che non includa anche "Stance rage powers"
  o sezioni separate (se presenti, pool separato o esclusione documentata).
