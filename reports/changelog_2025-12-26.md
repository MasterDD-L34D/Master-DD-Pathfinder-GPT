# Changelog RC 2025-12-26

## Fonti e ambito
- Basato su `planning/module_work_plan.md` aggiornato al 2025-12-11, con tutti i moduli marcati **Pronto per sviluppo** e storie **Done** nei tracker critici e satellite.【F:planning/module_work_plan.md†L13-L99】【F:planning/module_work_plan.md†L314-L344】
- Evidenze QA dal regression pass del 2025-12-11 (job tracker con `pytest` **73/73 pass**) e attestato automatico di copertura generato dal job tracker sui log archiviati.【F:reports/qa_log.md†L1-L7】【F:reports/coverage_attestato_2025-12-11.md†L3-L15】
- Verifica di coerenza: gli esiti QA confermano che lo stato **Pronto per sviluppo** è allineato ai log e alle storie chiuse.【F:planning/module_work_plan.md†L347-L359】【F:reports/qa_log.md†L46-L48】

## Copertura QA e suite eseguite
- Regression 2025-12-11: import automatico della suite `pytest` (73/73) come log unico per la chiusura delle storie Done.【F:reports/qa_log.md†L3-L7】【F:planning/module_work_plan.md†L347-L350】
- Attestato di copertura archiviato in `reports/coverage_attestato_2025-12-11.md`, collegato al job tracker e alle storie Done.【F:reports/coverage_attestato_2025-12-11.md†L3-L15】
- Suite di riferimento: `pytest tests/test_app.py -q` (dump policy, CTA QA, 401/403) utilizzata nel regression pass e nelle verifiche successive di readiness.【F:reports/qa_log.md†L8-L24】【F:reports/qa_log.md†L66-L75】

## Moduli coperti (stato "Pronto per sviluppo")
- **Encounter_Designer**, **Taverna_NPC**, **adventurer_ledger**, **archivist**, **base_profile**, **explain_methods**, **knowledge_pack**, **meta_doc**, **minmax_builder**, **narrative_flow**, **ruling_expert**, **scheda_pg_markdown_template**, **sigilli_runner_module**, **tavern_hub**, **Cartelle di servizio**: tutti marcati **Pronto per sviluppo** con task P1/P2 chiusi secondo il piano operativo.【F:planning/module_work_plan.md†L13-L158】【F:planning/module_work_plan.md†L260-L279】
- Storie critiche chiuse con evidenza nei report modulo e log `pytest` (73 pass), mantenendo coerenza con i gate QA/export e la dump policy.【F:planning/module_work_plan.md†L363-L379】【F:reports/qa_log.md†L46-L48】

## Sintesi storie Done e owner per sign-off
- **Moduli critici**: ENC-* (Owner: **Alice Bianchi**), SIG-* (Owner: **Fabio Marchetti**), BAS-* (Owner: **Andrea Rizzi**) — tutte le storie segnate Done con QA 73/73 e prove di dump/CTA.【F:planning/module_work_plan.md†L282-L310】【F:planning/module_work_plan.md†L363-L379】
- **Moduli satellite**: TAV-* (**Elisa Romano**), LED-* (**Luca Ferri**), ARC-* (**Martina Gallo**), RUL-* (**Valentina Riva**), SCH-* (**Matteo Leone**) — storie Done con coverage dal regression 2025-12-11.【F:planning/module_work_plan.md†L314-L344】【F:reports/qa_log.md†L46-L48】
- Owner già notificati nel piano per conferma assenza di blocchi; il draft deve essere condiviso con gli stessi owner prima del tag RC.【F:planning/module_work_plan.md†L98-L100】

## Decisioni e impatti
- Nessuna riapertura di storie o note aperte dopo l’import dei log `pytest` 2025-12-11; readiness invariata per tutti i moduli in scope.【F:reports/qa_log.md†L46-L48】
- Le note di rilascio devono richiamare la dump policy (`ALLOW_MODULE_DUMP=false` → marker/header `X-Content-*`, 403 su PDF/binari) e i gate QA/CTA su export (Encounter/MinMax/Taverna/Narrative).【F:reports/qa_log.md†L8-L16】【F:reports/qa_log.md†L79-L88】

## Checklist pre-RC
- [x] Conferma owner moduli critici e satellite sul presente changelog (vedi sezione precedente).
- [x] Allegare il changelog al ticket di rilascio 2025-12-26 e al canale di rilascio insieme ai log QA 2025-12-11 e all’attestato automatico.【F:planning/module_work_plan.md†L350-L361】【F:reports/qa_log.md†L79-L91】
- [x] Preparare tag/branch `rc/2025-12-26` dopo sign-off, utilizzando questo changelog come base ufficiale.【F:planning/module_work_plan.md†L356-L359】
