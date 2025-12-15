# Sprint Board / Project Tracker

Tabella di chiusura riportata da `planning/module_work_plan.md` con evidenza delle priorità P1 e stato "Pronto per sviluppo" per tutti i moduli, includendo owner e checkpoint giornalieri a partire da **2025-12-12**.
- Attestato QA 2025-12-11: **verde** (log pytest 73/73 importato, `reports/coverage_attestato_2025-12-11.md`).

## Rituale di aggiornamento quotidiano
- **Frequenza (15:00 CET, daily)**: aggiornare la tabella come fonte di verità durante il checkpoint.
- **Aggiornamento campi chiave**: per ogni modulo aggiornare `Stato` (o note di blocco), compilare `Ultimo update` con data/ora del checkpoint e popolare `Rischi` con dipendenze, blocchi o regressioni emerse.
- **Segnalazione blocchi**: evidenziare dipendenze aperte nei campi `Dipendenze operative` e `Rischi`; se bloccanti, aggiungere nota sintetica nella colonna `Note` (tabella di chiusura) e nel registro riassuntivo.
- **Avanzamento**: registrare nuovi progressi nelle colonne di osservazioni/errori e aggiornare i checkpoint programmati se slittano.
- **Esito checkpoint**: chiudere ogni rituale confermando i rischi attivi e gli owner responsabili della rimozione.

## Aggiornamento regression 2025-12-14
- **Scope**: policy di dump con marker/header di troncamento, gate QA/CTA obbligatorie, naming export per tutti i moduli.
- **Test eseguiti**: `pytest tests/test_app.py -q` (troncamento, 401/403/429 su endpoint protetti) + checklist manuale per CTA/naming/export per modulo.【b69106†L1-L10】【F:reports/regression_checklist.md†L1-L66】
- **Esito storie**: nessuna riapertura; tutte le storie impattate restano **chiuse** dopo il regression pass.【F:reports/regression_checklist.md†L1-L66】
- **Nota di rilascio**: messaggio pronto nel canale di rilascio che conferma marker/header, CTA QA e naming `MinMax_<nome>` allineato su Builder/Encounter.【F:reports/qa_log.md†L1-L16】

## Aggiornamento regression 2025-12-18
- **Scope**: verifica staging/sandbox su dump toggle (`ALLOW_MODULE_DUMP` true/false), CTA QA obbligatorie e naming export dei moduli principali (Encounter_Designer, MinMax Builder, Taverna/Narrative, ledger).
- **Test eseguiti**: `pytest tests/test_app.py -q` (53 pass, 2 warning deprecazione) su sandbox + playlist staging per dump/header, gate CTA e naming export.【80ed8e†L1-L12】【F:reports/staging_test_playlist.md†L1-L46】
- **Esito storie**: tutte le storie toccate restano **chiuse**, nessuna riapertura necessaria (dump/header/CTA/naming coerenti).【F:reports/qa_log.md†L18-L35】
- **Nota di rilascio**: messaggio pronto per il canale di rilascio con riferimenti ai test staging e conferma naming `MinMax_<nome>`/CTA QA attive.【F:reports/qa_log.md†L18-L35】

| Modulo | Owner | Task totali | Priorità massima | #Dipendenze | Dipendenze operative | Stato | #Osservazioni | #Errori | Checkpoint | Ultimo update | Rischi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Encounter_Designer | Alice Bianchi | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 2 | 1 | 2025-12-12 | 2025-12-12 | Nessuno |
| minmax_builder | Marco Conti | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 2 | 1 | 2025-12-13 | 2025-12-13 | Nessuno |
| Taverna_NPC | Elisa Romano | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 1 | 2 | 2025-12-14 | 2025-12-14 | Nessuno |
| tavern_hub | Paolo Greco | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 1 | 1 | 2025-12-15 | 2025-12-15 | Nessuno |
| Cartelle di servizio | Sara De Luca | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 1 | 2 | 2025-12-16 | 2025-12-16 | Nessuno |
| adventurer_ledger | Luca Ferri | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 1 | 1 | 2025-12-17 | 2025-12-17 | Nessuno |
| archivist | Martina Gallo | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 2 | 1 | 2025-12-18 | 2025-12-18 | Nessuno |
| base_profile | Andrea Rizzi | 2 | **P1** | 2 | Binding ai moduli core con preload obbligatorio (`preload_all_modules` + segmenter) | Pronto per sviluppo | 2 | 1 | 2025-12-19 | 2025-12-19 | Allineamento schema core e completamento preload prima del routing |
| explain_methods | Francesca Vitale | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 1 | 1 | 2025-12-20 | 2025-12-20 | Nessuno |
| knowledge_pack | Gianni Moretti | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 1 | 1 | 2025-12-21 | 2025-12-21 | Nessuno |
| meta_doc | Chiara Esposito | 3 | **P1** | 0 | Nessuna | Pronto per sviluppo | 1 | 1 | 2025-12-22 | 2025-12-22 | Nessuno |
| narrative_flow | Davide Serra | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 1 | 1 | 2025-12-23 | 2025-12-23 | Nessuno |
| ruling_expert | Valentina Riva | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 2 | 1 | 2025-12-24 | 2025-12-24 | Nessuno |
| scheda_pg_markdown_template | Matteo Leone | 2 | **P1** | 0 | Nessuna | Pronto per sviluppo | 2 | 1 | 2025-12-25 | 2025-12-25 | Nessuno |
| sigilli_runner_module | Fabio Marchetti | 2 | **P1** | 0 | Nessuna (nota: finestra raro attiva da indice 14, portale aggiunto anche senza sigilli) | Pronto per sviluppo | 3 | 4 | 2025-12-26 | 2025-12-26 | Validazione sigilli con QA in sospeso |

## Sommario per referenti Sviluppo/QA
- Tutti i moduli risultano marcati "Pronto per sviluppo".
- Non ci sono P1 o P2 aperti per alcun modulo nel perimetro attuale.

## Chiusura Sprint
| Modulo | Stato | Priorità max | Dipendenze | Owner | Checkpoint | Ultimo update | Rischi | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Encounter_Designer | Pronto per sviluppo | P1 | 0 | Alice Bianchi | 2025-12-12 | 2025-12-12 | Nessuno | Nessuna criticità aperta |
| minmax_builder | Pronto per sviluppo | P1 | 0 | Marco Conti | 2025-12-13 | 2025-12-13 | Nessuno | Nessuna criticità aperta |
| Taverna_NPC | Pronto per sviluppo | P1 | 0 | Elisa Romano | 2025-12-14 | 2025-12-14 | Nessuno | Nessuna criticità aperta |
| tavern_hub | Pronto per sviluppo | P1 | 0 | Paolo Greco | 2025-12-15 | 2025-12-15 | Nessuno | Nessuna criticità aperta |
| Cartelle di servizio | Pronto per sviluppo | P1 | 0 | Sara De Luca | 2025-12-16 | 2025-12-16 | Nessuno | Nessuna criticità aperta |
| adventurer_ledger | Pronto per sviluppo | P1 | 0 | Luca Ferri | 2025-12-17 | 2025-12-17 | Nessuno | Nessuna criticità aperta |
| archivist | Pronto per sviluppo | P1 | 0 | Martina Gallo | 2025-12-18 | 2025-12-18 | Nessuno | Nessuna criticità aperta |
| base_profile | Pronto per sviluppo | P1 | 2 | Andrea Rizzi | 2025-12-19 | 2025-12-19 | Allineamento schema core e preload obbligatorio | Binding core + preload (`preload_all_modules`/segmenter) prima del routing |
| explain_methods | Pronto per sviluppo | P1 | 0 | Francesca Vitale | 2025-12-20 | 2025-12-20 | Nessuno | Nessuna criticità aperta |
| knowledge_pack | Pronto per sviluppo | P1 | 0 | Gianni Moretti | 2025-12-21 | 2025-12-21 | Nessuno | Nessuna criticità aperta |
| meta_doc | Pronto per sviluppo | P1 | 0 | Chiara Esposito | 2025-12-22 | 2025-12-22 | Nessuno | Nessuna criticità aperta |
| narrative_flow | Pronto per sviluppo | P1 | 0 | Davide Serra | 2025-12-23 | 2025-12-23 | Nessuno | Nessuna criticità aperta |
| ruling_expert | Pronto per sviluppo | P1 | 0 | Valentina Riva | 2025-12-24 | 2025-12-24 | Nessuno | Nessuna criticità aperta |
| scheda_pg_markdown_template | Pronto per sviluppo | P1 | 0 | Matteo Leone | 2025-12-25 | 2025-12-25 | Nessuno | Nessuna criticità aperta |
| sigilli_runner_module | Pronto per sviluppo | P1 | 0 | Fabio Marchetti | 2025-12-26 | 2025-12-26 | Validazione sigilli con QA in sospeso | Nota raro: attivazione da indice 14 e portale sempre presente |

## Kickoff e checkpoint
- Messaggio da condividere nel canale del team: "Kickoff completato: tutti i moduli sono **Pronto per sviluppo** e non restano P1 aperti. Gli owner indicati nel board sono allineati sulle attività prioritarie".
- Checkpoint giornalieri pianificati alle **15:00 CET** dal **2025-12-12** al **2025-12-26** (sync sviluppo/QA, verifica dipendenze operative su base_profile).

### Registro checkpoint giornalieri (dal 2025-12-12)
| Data | Stato |
| --- | --- |
| 2025-12-12 | Done |
| 2025-12-13 | Done |
| 2025-12-14 | Done |
| 2025-12-15 | Done |
| 2025-12-16 | Done |
| 2025-12-17 | Done |
| 2025-12-18 | Done |
| 2025-12-19 | Done |
| 2025-12-20 | Done |
| 2025-12-21 | Done |
| 2025-12-22 | Done |
| 2025-12-23 | Done |
| 2025-12-24 | Done |
| 2025-12-25 | Done |
| 2025-12-26 | Done |

## Piano di avanzamento operativo
- **Oggi, H+0**: condivisione tabella di chiusura con owner assegnati e conferma delle dipendenze operative (base_profile bloccante su schema core).
- **Oggi, H+2**: allineamento rapido con gli owner P1 per definire i deliverable del primo giorno (incaricati: PM + owner di ciascun modulo P1).
- **Domani, 10:00 CET**: stand-up focalizzato sullo sblocco delle dipendenze e sullo stato di accettazione delle storie.
- **Ogni giorno, 15:00 CET**: checkpoint di avanzamento con verifica incrociata sviluppo/QA e conferma readiness per merge delle prime PR secondo il calendario assegnato per modulo.
- **Venerdì, 17:00 CET**: review conclusiva della sprint board, raccolta di eventuali errori residui e chiusura task P1/P2.
