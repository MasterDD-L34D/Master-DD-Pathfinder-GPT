# Changelog — Finestra RC 2025-12-26

## Fonti QA e attestazioni
- Basato sui log QA del 2025-12-11/12/13/14/18 che coprono dump policy, gate QA/CTA e naming export condiviso per i moduli core, con regression pass `pytest` verde (73 test) usato per chiudere le storie di finestra.
- Attestato automatico di copertura 2025-12-11 allegato (flag verde su tutte le storie **Done** e moduli **Pronto per sviluppo**).

## Policy di dump e protezioni
- Dump disabilitato con marker `[contenuto troncato]` e header `X-Content-*` su `.txt`, blocco 403 per PDF/binari e suffix `-partial` nei listing, validato dai regression pass e dalla sandbox staging.
- Endpoint protetti (`/modules`, `/knowledge`, `/metrics`) richiedono API key: 401/429 per key mancante o errata e 403 sulle metriche, con accesso consentito solo con chiave valida o `ALLOW_ANONYMOUS` esplicito.

## Gate QA/CTA e naming export
- Encounter Designer forza `/validate_encounter` prima di ogni export JSON/PDF (CTA guidate step 6) e mantiene naming condivisa con MinMax Builder.
- MinMax Builder applica il gate `export_requires`/`qa_check`, produce sempre `MinMax_<nome>.pdf/.xlsx/.json` e resta dietro i gate QA/CTA.
- Moduli narrativi/documentali (Taverna/Narrative/Meta) applicano CTA di remediation/QA prima delle preview/export e rispettano il troncamento quando `ALLOW_MODULE_DUMP=false`.

## Storie chiuse nella finestra
- ENC-OBS/ERR, BAS-OBS/ERR, SIG-OBS/ERR, TAV-OBS/ERR, LED-OBS/ERR, ARC-OBS, RUL-OBS, SCH-OBS, HUB-OBS/ERR, SER-OBS/ERR, MIN-OBS/ERR, META-OBS, KNO-OBS, NAR-OBS, EXP-OBS: tutti i moduli indicati risultano chiusi con marker dump, CTA QA e protezioni API allineate ai log QA.

## Evidenze di test
- Regression 2025-12-11: `pytest` completo (73 pass) usato per l’attestato automatico e la chiusura delle storie.
- Regression 2025-12-12/13/14/18: `pytest tests/test_app.py -q` (50/53 pass secondo scope) con warning di deprecazione attesi, confermando dump policy, gate QA/CTA e naming export.

## Allegati per rilascio
- Attestato automatico: `reports/coverage_attestato_2025-12-11.md`.
- Log QA consolidati: `reports/qa_log.md`.
