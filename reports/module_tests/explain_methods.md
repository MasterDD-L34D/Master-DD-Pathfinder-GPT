# Verifica API e analisi modulo `explain_methods.txt`

## Ambiente di test
- Server FastAPI locale avviato con `ALLOW_ANONYMOUS=true` su `http://localhost:8000`; run separato con `ALLOW_MODULE_DUMP=true` per dump completo e `ALLOW_MODULE_DUMP=false` per verificare il troncamento dei testi.【f222e6†L1-L8】【981c3b†L1-L6】

## Esiti API
1. **`GET /health`** — `200 OK`, directories `modules` e `data` accessibili, nessun file richiesto mancante.【f222e6†L1-L8】
2. **`GET /modules`** — `200 OK`, elenco include `explain_methods.txt` con dimensione/suffisso corretti.【a4f30d†L1-L13】
3. **`GET /modules/explain_methods.txt/meta`** — `200 OK`, metadati `name/size_bytes/suffix` coerenti con file su disco.【f07e23†L1-L7】
4. **`GET /modules/explain_methods.txt` (dump abilitato)** — `200 OK`, `content-type: text/plain; charset=utf-8`, download integrale 13.8 KB.【403fe6†L1-L20】
5. **`GET /modules/missing.txt`** — `404 Module not found`, conferma gestione errori standard su path errati.【c4e48f†L1-L7】
6. **`GET /modules/explain_methods.txt` con `ALLOW_MODULE_DUMP=false`** — risposta testuale con marker `[contenuto troncato]` dopo ~4000 caratteri, come previsto dal fallback streaming.【981c3b†L1-L6】【F:src/app.py†L543-L563】
7. **Parametri `mode`/`stub`** — endpoint `/modules/{name}` accetta `mode` (default `extended`) e `stub`/`mode=stub` per servire payload builder validato solo su `minmax_builder.txt`; per `explain_methods.txt` l'effetto è neutro e viene servito il file.【F:src/app.py†L367-L533】

## Metadati e scopo del modulo
- Modalità **Explain** v3.2-hybrid (last_updated 2025-08-20), erede di `base_profile.txt`; fornisce multi-metodo di spiegazione, quiz/teach-back, diagrammi ASCII e rubriche QA/MDA, con deleghe documentate verso Ruling/Archivist/MinMax gestite dal kernel.【F:src/modules/explain_methods.txt†L1-L34】
- Trigger: parole chiave su spiegazioni/metodi; speed modes `balanced/fast/full` regolano concisione e depth.【F:src/modules/explain_methods.txt†L21-L41】
- Policy: RAW gate attivo, `exposure_guard` vieta dump integrali di moduli, citazioni con policy estesa e hook di disambiguation/humility/cite_when_needed.【F:src/modules/explain_methods.txt†L205-L230】

## Modello dati (state principale)
- **Runtime/state** include `method`, `depth`, `speed`, `output_mode`, `raw_gate`; memoria traccia `explain.preferred_method`, `explain.preferred_depth`, `tone` con riuso prefer-last-method.【F:src/modules/explain_methods.txt†L35-L62】
- **Status** e logging espongono `method/depth/speed/output`, flag raw_gate, citations policy e ultimo redirect; session log salva timestamp, topic, metodo, speed, fonti, flag di incertezza con policy di output limitata.【F:src/modules/explain_methods.txt†L104-L117】【F:src/modules/explain_methods.txt†L271-L277】【F:src/modules/explain_methods.txt†L296-L303】

## Comandi principali
- `/explain` (topic, method=auto, depth="medio", output_mode="Completo"): effettua parse, applica RAW gate e genera struttura per metodo scelto; se RAW/RAI/PFS mostra redirect a Ruling/Archivist.【F:src/modules/explain_methods.txt†L82-L117】【F:src/modules/explain_methods.txt†L231-L239】
- `/switch_method` e `/set_method` forzano metodo; `/compare_methods` mostra affiancati due metodi; `/set_output_mode` imposta `Sintesi/Completo/Solo fonti`.【F:src/modules/explain_methods.txt†L88-L113】【F:src/modules/explain_methods.txt†L193-L200】
- `/fast` e `/full` settano speed mode; `/status` restituisce stato corrente e tool disponibili; `/explain_self_check` e `/show_explain_map` forniscono diagnostica e mini-mappa ASCII del flusso.【F:src/modules/explain_methods.txt†L100-L117】【F:src/modules/explain_methods.txt†L249-L260】【F:src/modules/explain_methods.txt†L296-L303】
- **Auto-invocazioni/flow**: pipeline documenta step parse→RAW gate→plan→draft→QA/MDA→output con QA checklist e MDA passes; auto-suggest follow-up/quiz nelle `suggest_followups` e `auto_suggest_next`.【F:src/modules/explain_methods.txt†L42-L116】【F:src/modules/explain_methods.txt†L231-L248】【F:src/modules/explain_methods.txt†L279-L287】

## Flow guidato, CTA e template
- UI hints invitano a scegliere metodo e offrono CTA di follow-up/quiz; header richiede conferma metodo/profondità/speed, con messaggi di errore per topic mancante, metodo ignoto e redirect RAW.【F:src/modules/explain_methods.txt†L42-L58】
- Output structure predefinita per ogni metodo (ELI5, First Principles, Storytelling, Visualization, Analogies, Technical) e output modes `Sintesi/Completo/Solo fonti` con esempi di combinazioni.【F:src/modules/explain_methods.txt†L118-L205】【F:src/modules/explain_methods.txt†L193-L200】
- Visualizzazione supportata da kit ASCII (sequence/tree/table) integrati in Visualization.【F:src/modules/explain_methods.txt†L149-L171】

## QA templates e helper
- Quality checks: coverage, grounding, jargon, esempi PF1e, math_safety, bias; output checklist impone header, marcatura fonti, struttura minima e aggiornamento memoria/redirect.【F:src/modules/explain_methods.txt†L74-L115】【F:src/modules/explain_methods.txt†L205-L215】
- RAW router kernel-managed con parole chiave e redirect a Ruling; exposure_guard impedisce dump integrali e limita output a derivazioni/estratti.【F:src/modules/explain_methods.txt†L216-L225】
- QA/MDA pipeline con passi Technical/Operational/DataModel/FlowLogic/DoubleReview; diagnostica `/explain_self_check` mostra esito QA/MDA; testing include router quick tests con attese metodo/delega.【F:src/modules/explain_methods.txt†L231-L248】【F:src/modules/explain_methods.txt†L249-L260】【F:src/modules/explain_methods.txt†L312-L317】
- Formula/metriche note: max_words per metodo/output, tracking preferenze, esempi CR/XP non presenti; badge PFS citato in benchmark builder non applicabile a questo modulo.

## Osservazioni
- Il flusso guidato con header/CTA seleziona metodo, profondità e speed, propone follow-up/quiz e fornisce template dedicati (ELI5, First Principles, Storytelling, Visualization, Analogies, Technical) con supporto ASCII per la resa visuale.【F:src/modules/explain_methods.txt†L42-L200】【F:src/modules/explain_methods.txt†L149-L171】【F:src/modules/explain_methods.txt†L231-L248】

## Errori
- **Protezione dump**: `exposure_guard` vieta dump integrali, ma con `ALLOW_MODULE_DUMP=true` l'API serve il file completo; con `ALLOW_MODULE_DUMP=false` il troncamento a 4000 char funziona ma non menziona header MIME nel corpo — comportamento conforme all'handler generico.【F:src/app.py†L543-L563】【F:src/modules/explain_methods.txt†L216-L225】【981c3b†L1-L6】

## Miglioramenti suggeriti
- **Deleghe/quiz**: il modulo documenta deleghe ma ne delega enforcement al kernel; quiz teach-back e auto-suggest follow-up già descritti e coerenti con UI hints.【F:src/modules/explain_methods.txt†L30-L48】【F:src/modules/explain_methods.txt†L94-L117】

## Fix necessari
- Nessuno: l’header del modulo riporta già la versione **3.3-hybrid-kernel** in linea con il changelog e i requisiti QA, senza altre azioni pendenti.【F:src/modules/explain_methods.txt†L1-L4】【F:src/modules/explain_methods.txt†L318-L325】

## Note di verifica
- Export e logging riportano filename atteso, payload MD/JSON e tag MDA (`MDA:explain_export`) per ogni run QA, con esempi in `export_trace` e nei self check.【F:src/modules/explain_methods.txt†L15-L21】【F:src/modules/explain_methods.txt†L288-L297】【F:src/modules/explain_methods.txt†L347-L348】
- Con `ALLOW_MODULE_DUMP=false` la risposta è troncata con marker finale, mantenendo header MIME coerente con la policy di streaming.【F:src/app.py†L543-L563】【981c3b†L1-L6】
- CTA e header guidati sono aggiornati: selezione metodo/profondità/speed, template per ogni metodo e flow QA/MDA già inclusi nella UI.【F:src/modules/explain_methods.txt†L42-L113】【F:src/modules/explain_methods.txt†L118-L205】
