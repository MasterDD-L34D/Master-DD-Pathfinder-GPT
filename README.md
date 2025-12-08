# Pathfinder 1E Master DD — Core Repo (API + Prompt Kit)

Questo repository contiene il "cuore" del tuo GPT **Pathfinder 1E Master DD** in forma esterna:
- tutti i moduli originali (`base_profile.txt`, `Taverna_NPC.txt`, `minmax_builder.txt`, ecc.)
- una piccola API in Python (FastAPI) che espone i moduli al GPT tramite Actions
- i file di supporto (knowledge pack, template scheda, guide PDF)
- un prompt compatto da incollare nel builder dei GPT, che usa questa API invece di includere tutto il base_profile

## Struttura

```text
pathfinder_master_dd_repo/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ src/
│  ├─ app.py                # FastAPI con endpoint per i moduli
│  ├─ config.py             # Configurazione path e sicurezza base
│  ├─ modules/              # TUTTI i tuoi moduli originali (txt/md/json)
│  └─ data/                 # PDF di supporto (gear guide, crafter guide, ecc.)
├─ gpt/
│  ├─ system_prompt_core.md # Istruzioni compatte da incollare nel GPT
│  └─ openapi.json          # Spec Actions per collegare l'API
└─ docs/
   ├─ architecture.md       # Spiegazione architettura Kernel + moduli
   └─ module_index.md       # Indice rapido dei file in src/modules
```

### Requisiti

- Python 3.10+
- `pip install -r requirements.txt`

L'API richiede per default una chiave: esporta `API_KEY` nell'ambiente per abilitarla:

```bash
export API_KEY="la-tua-chiave-segreta"
```

Se vuoi abilitare esplicitamente l'accesso anonimo, imposta `ALLOW_ANONYMOUS=true`. In
assenza di `API_KEY` e senza questo flag, l'API risponderà con `401 Unauthorized` alle
richieste prive di chiave.

Per i moduli, il dump completo è **attivo di default**. Se vuoi evitare che
`/modules/{name}` restituisca contenuti troppo lunghi, imposta
`ALLOW_MODULE_DUMP=false`: il testo verrà troncato a 4000 caratteri con un marcatore
finale. Il modulo **Documentazione** si aspetta estratti/riassunti come default; attiva
solo se ti serve il dump completo.

### Avvio API locale

```bash
export API_KEY="la-tua-chiave"
# opzionale: sblocca l'accesso senza chiave
# export ALLOW_ANONYMOUS=true
uvicorn src.app:app --reload --port 8000
```

L'endpoint di base sarà ad esempio: `http://localhost:8000`

Durante il setup nel GPT, forza sempre la modalità esplicita (`/set_mode core` oppure `/set_mode extended`) e verifica che l'avanzamento riporti `[step/step_total]` coerente: 8 step per `core`, 16 per `extended`.

### Generare il database di build (e i dump dei moduli)

Uno script di utilità (`tools/generate_build_db.py`) raccoglie automaticamente le build PF1e per tutte le classi target interrogando l'endpoint del **MinMax Builder** e, in parallelo, scarica i moduli grezzi indispensabili per ricostruire schede complete (base profile, taverna/narrativa, template scheda):

```bash
# Assicurati di avere l'API in esecuzione e una chiave valida
export API_KEY="la-tua-chiave-segreta"
python tools/generate_build_db.py --api-url http://localhost:8000 --mode extended

# È possibile limitare le classi passandole come argomenti finali
python tools/generate_build_db.py Alchemist Wizard Paladin
```

Per impostazione predefinita usa la modalità `extended` (16 step completi) e salva l'output in `src/data/builds/<classe>.json`, creando anche un indice riassuntivo in `src/data/build_index.json` con lo stato di ogni richiesta. In parallelo scarica i moduli RAW più usati dal flusso (per schede e PG completi) in `src/data/modules/` con indice `src/data/module_index.json`. L'header `x-api-key` viene popolato dalla variabile d'ambiente `API_KEY` salvo override esplicito tramite `--api-key`. Ogni chiamata include il parametro `mode=core|extended` e l'indice registra lo `step_total` osservato, così puoi verificare che i 16 step appaiano solo quando richiedi `extended`.

#### Selezione moduli: statici o via discovery

- Con `--modules` puoi continuare a pinnare manualmente i file da scaricare (default: i 5 moduli critici per scheda/narrativa).
- Con `--discover-modules` lo script interroga `GET /modules` e unisce i risultati ai moduli espliciti, così non perdi nuovi asset pubblicati sull'API.
- Puoi applicare filtri glob solo ai moduli scoperti: `--include '*.txt' modules/*` limita i download ai pattern indicati, mentre `--exclude 'beta_*'` rimuove i match specificati. L'indice `module_index.json` annota timestamp e filtri usati nella discovery per riprodurre esattamente la lista.

Esempi:

```bash
# Scarica i moduli statici + tutto ciò che è visibile via /modules
python tools/generate_build_db.py --discover-modules

# Scarica solo i moduli .txt scoperti e mantiene un modulo extra pinnato
python tools/generate_build_db.py --discover-modules --include '*.txt' --modules base_profile.txt meta_doc.txt

# Escludi gli asset di test ma lascia i moduli espliciti
python tools/generate_build_db.py --discover-modules --exclude 'test_*' --modules base_profile.txt scheda_pg_markdown_template.md
```

I file generati sono consumabili come database locale per esport, benchmark e stato di build: ogni JSON contiene i campi `build_state`, `benchmark` ed `export` prodotti dal builder, più metadati di fetch (`class`, `mode`, `source_url`). I moduli scaricati (es. `base_profile.txt`, `Taverna_NPC.txt`, `narrative_flow.txt`, `scheda_pg_markdown_template.md`, `adventurer_ledger.txt`) rimangono grezzi e coerenti con l'API così da poter combinare build, scheda e narrativa mantenendo varianti di classe/razza/archetipo definite dai moduli stessi.

Per orchestrare richieste più articolate (classe + razza/archetipo/modello + hook di background) puoi usare `--spec-file` con un file YAML/JSON che descrive ogni PG. Ogni voce definisce la classe, eventuali parametri addizionali da passare come query/body e il prefisso del file di output. Se non passi `--spec-file` viene caricato automaticamente `docs/examples/pg_variants.yml`, così da coprire almeno un set di combinazioni razza/archetipo per le classi chiave. In alternativa puoi far generare un prodotto cartesiano di varianti con le nuove flag CLI: `--races`, `--archetypes`, `--background-hooks` (tutti opzionali), abbinate alla lista di classi finale.

Il JSON di risposta includerà anche le sezioni extra restituite dall'API (es. narrativa, markup scheda, ledger) in `composite.{narrative|sheet|ledger}`, mentre l'indice `build_index.json` annoterà le varianti (`class`, `race`, `archetype`, `mode`, `spec_id`, `background`) per misurare copertura e refill del DB.

Esempio di spec (`docs/examples/pg_spec.yml`):

```yaml
# Mode di default per le richieste senza override
mode: extended
requests:
  - id: mm-hellknight-elf
    class: Fighter
    race: Elf
    archetype: Hellknight Armiger
    model: "Armiger (Hellknight)"
    background_hooks: "Giurata dell'Ordine del Pyre, addestrata alla disciplina inflessibile."
    output_prefix: fighter_hellknight_elf
    query:
      race: Elf
      archetype: Hellknight Armiger
      theme: "hellknight armiger"
      homebrewery_ready: true
    body:
      hooks:
        - "Servire l'Ordine e affrontare minacce extraplanari"
        - "Cerca una via di redenzione per un peccato passato"
      sheet_locale: it-IT
```

Invocazione con spec (genera build + narrativa + markup scheda + ledger se restituiti dal builder):

```bash
python tools/generate_build_db.py --api-url http://localhost:8000 --spec-file docs/examples/pg_spec.yml --modules base_profile.txt narrative_flow.txt scheda_pg_markdown_template.md adventurer_ledger.txt
```

Ogni payload recuperato viene validato rispetto agli schemi JSON disponibili in `schemas/`:

- `build_core.schema.json` verifica le risposte minime (solo `build_state`, `benchmark`, `export`).
- `build_extended.schema.json` richiede almeno una sezione addizionale (narrativa, scheda o ledger).
- `build_full_pg.schema.json` si aspetta il blocco composito completo con sezioni aggiuntive del PG.
- `module_metadata.schema.json` valida i metadati restituiti da `/modules/{name}/meta` prima di salvare i file.

Il comportamento di validazione è configurabile:

- Di default l'esecuzione è *warn-only*: gli errori di schema vengono loggati e annotati negli indici (`build_index.json`, `module_index.json`) ma l'esecuzione prosegue.
- Usa `--strict` per interrompere subito alla prima anomalia di validazione.
- Con `--keep-invalid` puoi chiedere allo script di scrivere comunque i file che non superano la validazione; in assenza del flag gli output non validi vengono scartati.

Per la scheda Markdown (`scheda_pg_markdown_template.md`) il payload viene validato contro `schemas/scheda_pg.schema.json`, che copre:

- Flag di rendering opzionali (`print_mode`, `show_minmax`, `show_vtt`, `show_qa`, `show_explain`, `show_ledger`, `decimal_comma`).
- Blocchi numerici e riepiloghi (`statistiche`, `statistiche_chiave`, `salvezze`, bonus CA/attacco/danni, slot incantesimi, CD scuola). Questi campi accettano anche numeri in formato stringa per compatibilità con l'API.
- Metadati di build e benchmark (`classi`, `benchmarks`, `benchmark_comparison`, etichetta `benchmark_reference_label`).
- Sezioni testuali di supporto (`rules_status_text`, `ap_warning`, `uncertainty_flags`, `glossario_golarion`, `fonti`, `fonti_meta`, `spoiler_mode`).
- Ledger opzionale (`ledger_invested_gp`, `ledger_encumbrance_hint`, movimenti/parcel/crafting PFS, valute `currency`).

Esempio di payload valido per la scheda (estratto da una risposta del builder, con campi opzionali popolati):

```json
{
  "class": "Fighter",
  "export": {
    "sheet_payload": {
      "print_mode": false,
      "show_minmax": true,
      "show_vtt": true,
      "decimal_comma": true,
      "classi": [{"nome": "Fighter", "livelli": 7, "archetipi": ["Lore Warden"]}],
      "statistiche": {"Forza": 18, "Destrezza": 16, "Costituzione": 14, "Intelligenza": 14, "Saggezza": 10, "Carisma": 8},
      "statistiche_chiave": {"PF": 67, "CA": 24, "DPR_Base": 21.5, "meta_tier": "T3"},
      "salvezze": {"Tempra": 9, "Riflessi": 7, "Volontà": 3},
      "benchmarks": {"meta_tier": "T3", "DPR_late_status": "ok", "risk_top3": {"feats": [], "spells": []}},
      "attack_bonus": {"melee": "+13/+8", "ranged": "+11/+6"},
      "damage": {"melee": "2d6+9", "special": "Power Attack attivo"},
      "fonti": ["CRB", "APG"],
      "fonti_meta": [{"badge": "PFS", "tipo": "boon", "link": "https://example.test/boon"}],
      "rules_status_text": "PFS-legal con boons annotati",
      "ledger_invested_gp": 5300,
      "ledger_movimenti": [
        {"data": "4712-08-01", "tipo": "acquisto", "oggetto": "Full Plate", "qty": 1, "tot": 1500, "pfs": true}
      ],
      "ledger_parcels": [{"nome": "Diamante", "val_gp": 500, "assegnatario": "party"}],
      "currency": {"gp": 245, "sp": 12}
    }
  }
}
```

Con la modalità *warn-only* i fallimenti di validazione della scheda o del payload build non interrompono il download: l'entry corrispondente negli indici viene marcata `status: "invalid"` con un campo `error` descrittivo, ma il resto delle richieste continua. In `--strict` l'errore viene propagato e l'esecuzione termina alla prima violazione; con `--keep-invalid` il file JSON o il modulo raw vengono comunque salvati accanto all'indice, utile per ispezionare manualmente i dati difettosi.

### Endpoints principali

- `GET /health` — ping rapido
- `GET /modules` — lista dei file modulo disponibili
- `GET /modules/{name}` — contenuto testuale di un modulo (es. `base_profile.txt`)
- `GET /modules/{name}/meta` — info sintetiche sul modulo (dimensione, tipo)
- `GET /knowledge` — lista risorse PDF/MD disponibili
- `GET /knowledge/{name}/meta` — metadata su una risorsa

Per tutti gli endpoint di moduli e knowledge è richiesto l'header `x-api-key` che deve
contenere il valore configurato in `API_KEY`. L'accesso anonimo è disabilitato di default;
per aprirlo è necessario impostare `ALLOW_ANONYMOUS=true`.

> Nel builder GPT userai il file `gpt/openapi.json` come **Actions Spec** e il testo
> di `gpt/system_prompt_core.md` come **istruzioni**. Così il GPT non deve più contenere
> l'intero `base_profile.txt`, ma può chiedere all'API i moduli quando servono.

## Asset di knowledge pack inclusi

Sono già presenti quattro PDF in `src/data` utilizzati dai moduli/knowledge pack:

- `Homebrewery Formatting Guide (V3) - The Homebrewery.pdf`
- `Items Master List.pdf`
- `The Gear Guide.pdf`
- `Ultimate Crafter Guide.pdf`

## Asset opzionali (non inclusi)

Le azioni per importare pregens PFS o generare Record Sheet CUP non sono abilitate perché
richiedono pacchetti zip non distribuiti. Se vuoi attivarle:

1. Scarica i pacchetti ufficiali e rinominali come `pfs_pregens.zip` e `record_sheets.zip`.
2. Copiali in `src/data/`.
3. Aggiorna `src/modules/Taverna_NPC.txt` per puntare ai nuovi asset (sezione `assets`) e
   riabilitare i flag/azioni corrispondenti.
