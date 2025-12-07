# Revisione formati moduli chiave

Questa nota riassume la revisione di quattro moduli di prompt per verificarne chiarezza, completezza dei formati e coerenza con il comportamento atteso. Evidenzia eventuali campi obsoleti/non usati e propone una checklist di output standard riutilizzabile.

## Adventurer Ledger (`src/modules/adventurer_ledger.txt`)
- **Chiarezza**: il formato è dettagliato (metadata, policies, helpers, templates, comandi). La sezione Magic Item Creator è integrata e coerente con il resto del modulo.
- **Incertezze/possibili obsolescenze**
  - `policies.mic_randomization` di default è `Mild`, mentre il welcome command raccomanda `mic_randomization=Moderate`; serve allineare default/guida.
  - `data_structures.loot_state.context.player_style` è annotato per suggerimenti/shop ma non compare negli helpers principali: valutare se rimuoverlo o usarlo in `build_buylist`/`generate_magic`.
  - `types.Art`/`Gem` sono definiti ma non referenziati nei generatori (che producono solo `Art` via `generate_goods`): chiarire o semplificare.
  - `helpers.generate_mundane`/`generate_magic` usano cataloghi fissi: indicare che sono placeholder (per evitare percezione di tabella RAW) o collegarli a sorgenti dinamiche.
- **Coerenza**: i vincoli RAW/PFS sono coerenti con il kernel (flag pfs, badge, gating WBL) e con il tono di trasparenza richiesto dal prompt principale.

## Explain Methods (`src/modules/explain_methods.txt`)
- **Chiarezza**: metodi, strutture e speed mode sono autoesplicativi. La politica citazioni è dichiarata.
- **Incertezze/possibili obsolescenze**
  - I metodi non mappano esplicitamente a `output_modes` nella definizione: aggiungere esempi di combinazione metodo+speed (es. Visualization+Sintesi) potrebbe ridurre ambiguità.
  - `runtime.raw_gate: true` dipende dal kernel ma non richiama direttamente il router: citare il messaggio di redirect in `commands` aiuterebbe la coerenza.
- **Coerenza**: il redirect verso Ruling/Archivist/MinMax è documentato e rispetta il flusso kernel.

## Sigilli Runner (`src/modules/sigilli_runner_module.txt`)
- **Chiarezza**: soglie, tabelle e stato in memoria sono definiti chiaramente. L’euristica `_looks_like_code` è specificata.
- **Incertezze/possibili obsolescenze**
  - `sigilli_code_lines` conta righe con `-` come “codice”: può assegnare bonus su semplici liste; valutare filtro più stretto (backtick o `{}`) o soglia più alta.
  - `sigilli_portal` linka al vecchio portale GPT (`chatgpt.com`): sostituire con l’URL corrente del progetto, se diverso.
- **Coerenza**: il modulo è autonomo e non confligge con policy RAW/RAI; aggiungere note su lingue/output potrebbe allinearlo meglio al prompt principale.

## Scheda PG Markdown (`src/modules/scheda_pg_markdown_template.md`)
- **Chiarezza**: il template include macro, breakdown CA/CMD, economia d’azione, risorse e hook per ledger/vtt.
- **Incertezze/possibili obsolescenze**
  - Flag di visualizzazione: `SHOW_MINMAX/SHOW_VTT/SHOW_QA/SHOW_EXPLAIN/SHOW_LEDGER` sono definiti ma non usati nel corpo; se non gestiti dal renderer esterno, vanno rimossi o applicati con `if`.
  - Mancano note su localizzazione numerica (separatori decimali) e su come gestire sezioni vuote (alcune tabelle restano con header senza righe): aggiungere esempi o placeholder espliciti.
  - La tabella `Risorse Giornaliere` è hardcoded su una riga generica: prevedere loop su risorse dichiarate o indicare che è un modello di esempio.

## Checklist di output standard (riutilizzabile nei moduli)
Per uniformare l’uso ripetibile, inserire una sezione `output_checklist` nei moduli che producono testo strutturato. Bozza di checklist:
- ✅ **Header di contesto**: nome modulo, modalità/speed attivi, lingua, data/seed se applicabile.
- ✅ **Assunzioni dichiarate**: regole RAW/RAI/PFS applicate, homebrew disattivo salvo flag espliciti.
- ✅ **Struttura minima**: titolo, sommario/bullet, corpo principale, esempi (se previsti), sezione “Limitazioni/QA”.
- ✅ **Tagging fonti**: marcatura per fonte (RAW/PFS/HR/META) e badge origine quando il kernel lo supporta.
- ✅ **Dati numerici**: unità, arrotondamenti/policy (es. `rounding` del ledger), tolleranze WBL o altre soglie.
- ✅ **Coerenza locale**: lingua allineata al prompt, formati numerici (`,` vs `.`), simboli usati in tabelle.
- ✅ **Esportazione**: dichiarare il formato target (Markdown/JSON/VTT) e link/prompt per export alternativi.
- ✅ **QA rapida**: 3–5 check specifici del modulo (es. delta WBL entro tolleranza; citazioni presenti; template senza campi vuoti bloccanti).
- ✅ **Memoria/stato**: se viene toccata la memoria, elencare le chiavi aggiornate e il motivo.

Integrare la checklist direttamente nei moduli come sezione dedicata, oppure come riferimento nel `commands` `/help` o `/status` per promuovere la ripetibilità.
