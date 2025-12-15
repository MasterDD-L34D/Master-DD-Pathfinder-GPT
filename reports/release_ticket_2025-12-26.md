# Ticket di rilascio — Finestra RC 2025-12-26

## Allegati
- **Changelog RC 2025-12-26**: `reports/changelog_2025-12-26.md`.
- **Attestato automatico QA (73/73 verde)**: `reports/coverage_attestato_2025-12-11.md`.
- **Log QA di riferimento**: `reports/qa_log.md` (QA 2025-12-11/12/13/14/18).
- **Tag/branch RC**: tag annotato `rc/2025-12-26` (commit `5968b375e2` con changelog aggiornato) già pubblicato e usato dalla pipeline di rilascio.

## Note operative
- Il changelog riflette la dump policy (`ALLOW_MODULE_DUMP=false` → marker/header `X-Content-*`, 403 su PDF/binari) e i gate QA/CTA su export Encounter/MinMax/Taverna/Narrative.
- L’attestato automatico certifica che tutte le storie marcate **Done** sono coperte dal regression pass del 2025-12-11 e che i moduli sono **Pronto per sviluppo**.
- Dopo il tagging RC (`rc/2025-12-26`) condividere questo ticket nel canale di rilascio con link agli allegati per la tracciabilità.
