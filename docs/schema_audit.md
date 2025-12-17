# Audit schema e vincoli (JSON Schema)

## Contesto
- Non è presente un database locale; lo schema corrente è definito dai JSON Schema in `schemas/`.
- Gli schema modellano i payload JSON di build, moduli e cataloghi di riferimento, con pochissime restrizioni tipiche dei database relazionali (PK/FK, vincoli di unicità o obbligatorietà puntuali).

## Sintesi delle strutture (DDL logico)
### Build payload (core)
- **Struttura:** oggetto con campi obbligatori `build_state`, `benchmark`, `export`; altre sezioni (`narrative`, `sheet`, `ledger`, `request`, `query_params`, `body_params`, `step_audit`, `completeness`, `composite`) sono facoltative e ammettono proprietà aggiuntive.【F:schemas/build_core.schema.json†L1-L242】
- **Vincoli espliciti:** solo obbligatorietà dei tre campi core; i sottoschemi `build_state`, `benchmark`, `export` e `textual_block` non definiscono proprietà richieste, né tipi più stretti, quindi accettano qualsiasi oggetto/array/stringa/null. Il sottoschema `step_audit` ora richiede timestamp richiesta, hash della chiave client, esito (`accepted`/`denied`/`backoff`), conteggio tentativi e motivazione di backoff (null se assente), più IP opzionale.【F:schemas/build_core.schema.json†L11-L241】【F:schemas/build_core.schema.json†L328-L369】
- **Note DDL:** può essere visto come tabella `build_core(build_state JSON NOT NULL, benchmark JSON NOT NULL, export JSON NOT NULL, …)` senza chiave primaria.

### Build payload (extended)
- **Struttura:** estende `build_core` richiedendo almeno una sezione tra `narrative`, `sheet`, `ledger` o `composite` in aggiunta ai dati core.【F:schemas/build_extended.schema.json†L1-L35】
- **Vincoli espliciti:** nessuna chiave; eredita le aperture di `build_core` e aggiunge solo il vincolo “almeno una sezione extended”.

### Build payload (full-PG)
- **Struttura:** oggetto che richiede `build_state`, `benchmark`, `export`, `sheet_payload` e `composite`; `sheet_payload` usa `scheda_pg.schema.json` e può comparire sia al top-level sia dentro `composite.build`.【F:schemas/build_full_pg.schema.json†L1-L102】
- **Vincoli espliciti:** obbligatorietà dei campi sopra elencati; `composite.build` replica gli stessi obblighi ma senza regole di coerenza rispetto al top-level (duplicazione potenzialmente divergente). Nessuna chiave primaria o relazione verso altre entità.

### Scheda PG (sheet payload)
- **Struttura:** oggetto estremamente ampio per il rendering della scheda; nessun campo è richiesto e sono ammessi campi aggiuntivi, con molte proprietà numeriche/stringa facoltative.【F:schemas/scheda_pg.schema.json†L1-L80】
- **Vincoli espliciti:** assenti; funge da documento libero più che da tabella strutturata.

### Catalogo di riferimento
- **Struttura:** array di `reference_entry` con campi obbligatori `name`, `source`, `prerequisites`, `tags`, `references`; altre proprietà opzionali come `reference_urls`, `source_id`, `notes` e `additionalProperties` disabilitati per le entry.【F:schemas/reference_catalog.schema.json†L1-L81】
- **Vincoli espliciti:** obbligatorietà e lunghezze minime per i campi base, unicità degli elementi in `tags`; nessun vincolo di unicità per `name`/`source_id` e nessun collegamento a build o moduli.

### Metadati modulo
- **Struttura:** oggetto con `name`, `size_bytes`, `suffix` obbligatori; `version` e `compatibility` opzionali (quest’ultima può essere stringa, oggetto o array).【F:schemas/module_metadata.schema.json†L1-L34】
- **Vincoli espliciti:** solo tipi base e `size_bytes >= 0`; nessun identificatore univoco o relazione con altri schemi.

## Chiavi primarie, chiavi esterne e vincoli mancanti
- **Assenza di PK:** nessuno degli schemi definisce campi identificativi univoci; le “tabelle” build, scheda, catalogo e moduli risultano senza chiave primaria esplicita.
- **Relazioni/FK mancanti o deboli:**
  - I payload `composite.build` duplicano i campi top-level senza vincoli di coerenza (mancano FK o controlli che garantiscano l’allineamento).【F:schemas/build_full_pg.schema.json†L36-L102】【F:schemas/build_core.schema.json†L202-L239】
  - `sheet_payload` non è collegato a `build_state` o `benchmark`; nessun vincolo assicura che i dati di scheda riflettano la build associata.【F:schemas/build_full_pg.schema.json†L13-L80】
  - Il catalogo di riferimento non è relazionato alle build o ai moduli; `name` e `source_id` potrebbero duplicarsi senza controllo.【F:schemas/reference_catalog.schema.json†L1-L81】
  - I metadati modulo non forzano coerenza su `compatibility` (tipi multipli) e non sono collegati ai cataloghi o alle build; manca un vincolo di unicità su `name`/`version`.【F:schemas/module_metadata.schema.json†L1-L34】

## Evidenze di integrità potenzialmente sospette
- **Tabelle/oggetti senza PK:** tutte le strutture sopra elencate (build_core/extended/full-PG, scheda_pg, reference_catalog, module_metadata) sono prive di chiavi primarie esplicite.
- **FK o relazioni sospette:** duplicazione di `build_state`/`benchmark`/`export` tra top-level e `composite.build` può produrre disallineamenti; `sheet_payload` è riusato in più punti senza referenze; il catalogo e i moduli non legano le voci a build o fonti tramite identificatori condivisi.
- **Vincoli di forma deboli:** campi chiave come `build_state`, `benchmark`, `export` accettano qualsiasi oggetto, riducendo la capacità di prevenire dati incompleti o incoerenti.【F:schemas/build_core.schema.json†L11-L241】

## Raccomandazioni (opzionali)
- Introdurre identificatori univoci (es. `build_id`, `module_id`) e referenze esplicite tra build, scheda e moduli.
- Stringere i sottoschemi `build_state`/`benchmark`/`export` con proprietà richieste e tipi più precisi, includendo i campi di audit essenziali.
- Normalizzare `reference_catalog` imponendo unicità su `name` o `source_id` e collegamenti alle build/moduli che consumano le voci catalogate.
- Uniformare il tipo di `compatibility` nei metadati modulo e vincolare la coerenza tra top-level e `composite.build` per evitare divergenze.
