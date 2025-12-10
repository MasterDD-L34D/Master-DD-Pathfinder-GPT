# Verifica API e analisi modulo `ruling_expert.txt`

## Ambiente di test
- FastAPI locale avviato con `API_KEY=testing` e dump completo abilitato (default `ALLOW_MODULE_DUMP=true`).【1aba59†L1-L4】
- Secondo run con `ALLOW_MODULE_DUMP=false` per verificare il troncamento server-side e l'impatto del flag di sicurezza previsto in `settings.allow_module_dump`.【c08648†L20-L28】【c0fb0d†L1-L4】

## Esiti API
1. `GET /health` → `200 OK` con stato `ok` e directories/modules requisiti presenti.【c28ff5†L1-L8】
2. `GET /modules` con API key → elenco completo dei moduli disponibile con nome/suffix/size.【0c0921†L1-L11】
3. `GET /modules/ruling_expert.txt/meta` con API key → `200 OK` e metadati corretti.【9f6bb4†L1-L7】
4. `GET /modules/ruling_expert.txt` con `ALLOW_MODULE_DUMP=true` → `200 OK`, file servito integralmente (Content-Disposition allegato).【3cdfab†L1-L24】
5. `GET /modules/nope.txt/meta` con API key → `404 Module not found` confermato.【871928†L1-L8】
6. `GET /modules/ruling_expert.txt` con `ALLOW_MODULE_DUMP=false` → risposta `200 OK` ma contenuto limitato a ~4000 caratteri seguito da `[contenuto troncato]`.【88122c†L1-L74】

## Metadati / Scopo
- Nome **Ruling Expert** v3.1 (last_updated 2025-08-20), eredità `base_profile.txt`, integrazioni dichiarate con MinMax Builder, Documentazione, Taverna NPC, Explain, Archivist, trigger per richieste RAW/RAI/PFS e conflitti di regole.【F:src/modules/ruling_expert.txt†L1-L12】
- Principi e vincoli: solo materiale PF1e ufficiale con tag obbligatori RAW/RAI/PFS/HR, necessità di almeno una fonte verificabile, citazioni brevi, niente 3PP salvo richiesta; priorità fonti AoN→Paizo book/FAQ→PFS→d20pfsrd.【F:src/modules/ruling_expert.txt†L13-L45】
- Sicurezza e policy: `require_citation_strict: true`, esposizione limitata (no raw dump) e guardrail anti–prompt-injection con pattern bloccati e risposta standard.【F:src/modules/ruling_expert.txt†L65-L105】

## Modello dati
- Stato runtime: `pfs_mode`, `pfs_season`, `locale`, `require_citation_strict`, modalità speed/output, priorità di giurisdizione e vincoli di citazione/recency.【F:src/modules/ruling_expert.txt†L61-L105】
- Helpers chiave per normalizzazione/URL e qualità numerica: `normalize_term`, `aon_display_url`, `stacking_check` per verificare stacking dei bonus, `apply_hr_tag` per sigillo HR.【F:src/modules/ruling_expert.txt†L115-L194】
- Decoratore su `reply.meta.hr` che propaga il contesto HR se attivato a runtime.【F:src/modules/ruling_expert.txt†L185-L194】【F:src/modules/ruling_expert.txt†L420-L423】

## Comandi principali
- Core rulings e fonti: `/ruling`, `/compare_raw_rai`, `/pfs_check`, `/errata_check`, `/cite_rule`, `/source`, `/rule_source`, `/pfs_diff` coprono giudizi, confronti e citazioni; `/variation_guidance` esplicita differenze PFS/Unchained/HR.【F:src/modules/ruling_expert.txt†L195-L221】
- Setup/stato: `/status`, `/set_pfs`, `/fast`, `/full`, `/set_locale`, `/set_pfs_season`, `/strict_citations` aggiornano runtime (scope PFS, speed/output, locale, enforcement citazioni).【F:src/modules/ruling_expert.txt†L200-L244】【F:src/modules/ruling_expert.txt†L274-L283】
- QA e strumenti di supporto: `/ruling_self_check`, `/show_ruling_map`, `/source_audit`, `/router_smoke_tests`, `/offline_check`, `/cache_status`, `/ambiguity_probe`, `/math_guard_test` forniscono auto-verifiche, mappe di flusso e prove di disambiguazione/calcolo.【F:src/modules/ruling_expert.txt†L205-L227】【F:src/modules/ruling_expert.txt†L366-L410】
- Flag HR e stacking: `/hr_mode` marca il reply come House Rule e aggiorna `runtime.hr_context`; `/stacking_check` restituisce esito ed esplicita il motivo (stack/no stack).【F:src/modules/ruling_expert.txt†L254-L273】

## Flow guidato, CTA e template
- Pipeline step-by-step con guardrail anti-injection, parsing/scoping, disambiguazione, recupero RAW, verifica FAQ/Errata, varianti/Unchained, controlli PFS, analisi numerica (arithmetic_guard), citazioni e QA finale.【F:src/modules/ruling_expert.txt†L284-L317】
- Linee guida di risposta: tono neutrale, lingua utente, limite citazioni 25 parole, calcolo a passi per bonus/malus/molt., ordine RAW→FAQ→PFS e avviso su uso di d20pfsrd.【F:src/modules/ruling_expert.txt†L319-L329】
- CTA e suggerimenti: soglia di disambiguazione 0.65 con prompt guidato, suggerimenti automatici post-risposta e template `status` per mostrare scope/speed/PFS/cache.【F:src/modules/ruling_expert.txt†L331-L336】【F:src/modules/ruling_expert.txt†L417-L424】
- Output structure/template UI: sezioni RAW/RAI/PFS/HR predefinite e template per feat/spell/condition/combat/skill/item/hazard/generic, utili per layout narrativo/QA.【F:src/modules/ruling_expert.txt†L342-L356】

## QA templates e helper
- Checklist MDA: presenza di almeno una fonte ufficiale, tag corretti, citazioni formattate, gestione ambiguità, calcoli a passi, esclusione 3PP salvo richiesta.【F:src/modules/ruling_expert.txt†L358-L364】
- Strumenti QA/diagnostica con output di esempio per self-check, mappe di flusso, audit fonti, stato offline/cache, probe di ambiguità e test arithmetic_guard.【F:src/modules/ruling_expert.txt†L366-L410】
- Output format e citazione: `citation_format` definisce inline/list e `min_required: 1`, ribadendo l’aspettativa di fonti; utile per export JSON/filename consistenti.【F:src/modules/ruling_expert.txt†L337-L356】

## Osservazioni, errori e miglioramenti proposti
- **Allineare policy di esposizione**: il modulo dichiara `exposure_policy: no_raw_dump`, ma l’API di default (`ALLOW_MODULE_DUMP=true`) serve il file completo; solo con `ALLOW_MODULE_DUMP=false` avviene il troncamento. Suggerito impostare `ALLOW_MODULE_DUMP=false` in ambienti pubblici o applicare whitelist per coerenza con la policy del modulo.【F:src/modules/ruling_expert.txt†L80-L85】【c08648†L20-L28】【88122c†L1-L74】
- **Documentare payload stub builder**: l’endpoint `/modules/minmax_builder.txt` in modalità `stub` costruisce state compositi con `build_state`, `sheet`, `benchmark`, `ledger`, `export` e `composite` coerenti con lo schema del builder.【F:src/app.py†L366-L572】 Chiarire nel modulo come questi campi si mappano su rulings/QA potrebbe agevolare l’integrazione.
- **Rafforzare CTA per PFS**: il flow indica season awareness e priorità PFS ma il `status_example` non mostra esplicitamente il badge/season derivato; aggiungere un prompt CTA per confermare la stagione PFS potrebbe ridurre ambiguità di giurisdizione.【F:src/modules/ruling_expert.txt†L300-L317】【F:src/modules/ruling_expert.txt†L417-L424】
