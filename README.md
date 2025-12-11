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
   ├─ api_usage.md          # Endpoint API, parametri, esempi
   └─ module_index.md       # Indice rapido dei file in src/modules
```

Per obiettivi, milestone e decisioni architetturali sulle build/moduli consulta anche la cartella `planning/`:

- [planning/roadmap.md](planning/roadmap.md) raccoglie roadmap e obiettivi aggiornati.
- [planning/decisions.md](planning/decisions.md) contiene le ADR sulle scelte di build e modularizzazione.

Nota: `docs/module_index.md` elenca tutti i moduli richiesti e documenta anche le cartelle di servizio (es. `quarantine/`, `taverna_saves/`) che non rientrano nel flusso API standard ma vanno tracciate lì; per i dettagli su moduli obbligatori/di servizio vedi la [sezione dedicata](docs/module_index.md#cartelle-di-servizio).

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

### Avvio rapido

1. Esporta le variabili d'ambiente: `export API_KEY="la-tua-chiave"` e, se serve accesso senza chiave, `export ALLOW_ANONYMOUS=true`.
2. Installa le dipendenze: `pip install -r requirements.txt`.
3. Esegui il controllo di formattazione e sintassi: `tools/run_static_analysis.sh`.
4. Avvia l'API: `uvicorn src.app:app --reload --port 8000`.
5. Verifica che risponda: `curl http://localhost:8000/health`.

Se incontri errori `401` o `429`, regola il [backoff di autenticazione](#backoff-autenticazione-auth_backoff_) tramite le variabili `AUTH_BACKOFF_*` per gestire ritardi e blocchi temporanei.

#### Backoff autenticazione (`AUTH_BACKOFF_*`)

Per mitigare tentativi ripetuti con chiavi errate, puoi regolare il backoff sugli
header `x-api-key` tramite due variabili d'ambiente:

- `AUTH_BACKOFF_THRESHOLD` (default: `5`): numero di richieste fallite prima di attivare
  il blocco temporaneo.
- `AUTH_BACKOFF_SECONDS` (default: `60`): durata del blocco (`429 Too Many Requests` con
  header `Retry-After`) applicato all'IP che ha superato la soglia.

Consulta `docs/api_usage.md` per panoramica rapida di endpoint, parametri (`mode`, `stub`, header `x-api-key`) e messaggi d'errore standard.

### Analisi statica

Prima di aprire una PR esegui un controllo veloce di formattazione e sintassi:

```bash
tools/run_static_analysis.sh
```

Lo script lancia `black --check` sui file Python e compila i moduli con
`python -m compileall` per rilevare errori di sintassi.

Su push e pull request, il workflow GitHub Actions **Static Analysis** esegue
lo stesso script per garantire che il codice resti formattato e privo di errori
di sintassi prima del merge.

Per i moduli, il dump completo è **disattivato di default** (`ALLOW_MODULE_DUMP=false`).
`/modules/{name}` restituisce solo estratti (4000 caratteri + marcatore finale) e blocca
gli asset non testuali: la risposta include `X-Content-Partial: true` e `206 Partial Content`
per segnalare che il contenuto è incompleto. Imposta `ALLOW_MODULE_DUMP=true` solo se
ti serve il dump completo per QA o export.

Per monitorare i salvataggi generati dal flusso Taverna, sono disponibili gli endpoint
`GET /modules/taverna_saves/meta` (path, quota `max_files`, spazio residuo, policy di
overflow) e `GET /modules/taverna_saves/quota` (occupazione rapida della cartella). Il
payload include note di remediation per Echo gate <8.5 (ripeti /grade, usa /refine_npc o,
in sandbox, disattiva temporaneamente con /echo off) e per QA CHECK bloccanti: completa
Canvas+Ledger, ripeti /self_check e verifica Echo ≥ soglia prima di rilanciare /save_npc o
/npc_export (bloccati finché QA=CHECK o Echo è sotto soglia).

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
# Nota: valida sempre /health e /metrics con l'API key corretta prima dei run;
# se ricevi 401/429 regola AUTH_BACKOFF_THRESHOLD/SECONDS per aumentare il margine.
# Se l'API non gira in locale, passa un endpoint raggiungibile oppure usa
# la variabile API_URL per evitare errori di connessione su http://localhost:8000
export API_KEY="la-tua-chiave-segreta"
# Esempio con endpoint locale
python tools/generate_build_db.py --api-url http://localhost:8000 --mode extended
# Esempio con endpoint remoto/containerizzato
# API_URL="https://builder.example.com" python tools/generate_build_db.py --mode extended
# Se l'endpoint non espone /health ma sai che è raggiungibile, aggiungi --skip-health-check

# È possibile limitare le classi passandole come argomenti finali
python tools/generate_build_db.py Alchemist Wizard Paladin

# Oppure filtrare a monte le richieste provenienti dalla spec con le flag dedicate
# (utile per rigenerare blocchi di 5 classi per volta)
python tools/generate_build_db.py --spec-file docs/examples/pg_variants.yml --classes Alchemist Barbarian Bard Cavalier Cleric

# Puoi anche limitare i checkpoint di livello a un sottoinsieme preciso
python tools/generate_build_db.py --spec-file docs/examples/pg_variants.yml --levels 1 5

# Se devi generare batch piccoli (es. 10 file alla volta) puoi impostare un tetto
python tools/generate_build_db.py --max-items 10 --skip-unchanged

# Quando hai bisogno di riavviare batch successivi, combina max-items con offset/paginazione
python tools/generate_build_db.py --max-items 10 --offset 0   # Batch 1
python tools/generate_build_db.py --max-items 10 --offset 10  # Batch 2
python tools/generate_build_db.py --max-items 10 --offset 20  # Batch 3 (e così via)
python tools/generate_build_db.py --max-items 10 --page 1 --page-size 10  # Equivalente a offset 0
python tools/generate_build_db.py --max-items 10 --page 2 --page-size 10  # Equivalente a offset 10
# Ripeti incrementando l'offset/la pagina finché non hai coperto tutte le classi e i checkpoint richiesti
```

Per impostazione predefinita usa la modalità `extended` (16 step completi) e salva l'output in `src/data/builds/<classe>.json`, creando anche un indice riassuntivo in `src/data/build_index.json` con lo stato di ogni richiesta. In parallelo scarica i moduli RAW più usati dal flusso (per schede e PG completi) in `src/data/modules/` con indice `src/data/module_index.json`. L'header `x-api-key` viene popolato dalla variabile d'ambiente `API_KEY` salvo override esplicito tramite `--api-key`. Ogni chiamata include il parametro `mode=core|extended` e l'indice registra lo `step_total` osservato, così puoi verificare che i 16 step appaiano solo quando richiedi `extended`.

Ogni build viene recuperata sui checkpoint di livello dichiarati nella spec (default 1/5/10) e scritta in file separati con suffisso `_lvlXX` (es. `Fighter_lvl05.json`): le entry dell'indice `build_index.json` includono il campo `level` e un riepilogo `checkpoints` con i totali/invalidi (incluse le invalidazioni di schema o completezza) per ciascun livello.

#### Troubleshooting

- Endpoint senza `/health`: aggiungi `--skip-health-check` per saltare il probe iniziale quando l'API è accessibile ma non espone l'handler di health (o usa l'ambiente `API_URL` per puntare a un host remoto se non è `localhost`).
- Validazione schema fallita: usa `--strict` per far fallire lo script al primo JSON non conforme; con `--keep-invalid` salvi comunque le risposte difettose per ispezionarle. In `build_index.json` troverai gli esiti dei singoli step (`status`, `errors`, `step_total`) e puoi capire quale build/race/archetipo ha rotto lo schema; `module_index.json` riporta eventuali moduli scartati o corrotti con `validation_errors`.
- Copertura vs resilienza: con `--dual-pass` lo script esegue prima un round fail-fast (`--strict`) e poi uno tollerante che forza `--keep-invalid`, così puoi confrontare copertura e errori. Aggiungi `--dual-pass-report reports/dual_pass.json` per salvare un riepilogo e `--invalid-archive-dir artifacts/invalid_payloads` per copiare automaticamente i payload non conformi segnalati dagli indici.
- Host remoto non raggiungibile su `localhost`: esporta `API_URL` o passa `--api-url https://builder.example.com` per indirizzare lo script verso l'endpoint corretto, anche dietro tunnel/port-forward.

Esempi rapidi:

```bash
# Forza la validazione rigorosa e interrompe al primo errore
python tools/generate_build_db.py --api-url http://localhost:8000 --mode extended --strict

# Mantiene i payload non validi per analisi successive
python tools/generate_build_db.py --api-url http://localhost:8000 --mode extended --keep-invalid
```

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

Se hai già generato il database e vuoi avviare una review offline, usa la nuova modalità di sola validazione: non effettua chiamate di rete e produce un report riassuntivo (per default `src/data/build_review.json`).

```bash
python tools/generate_build_db.py --validate-db --review-output src/data/build_review.json
```

Il report include conteggi di build e moduli validi/invalidi, file mancanti e relativi errori di schema così da facilitare la revisione manuale. Nella sezione `builds.checkpoints` trovi il riepilogo dei checkpoint di livello (per default 1/5/10) con totali, invalidazioni e conteggi distinti per errori di schema o completezza, così puoi identificare rapidamente quali livelli sono più fragili. Lo stesso riepilogo viene scritto anche in `build_index.json`, affiancato alle entry per livello generate con suffisso `_lvlXX`.

### Endpoints principali

- `GET /health` — ping rapido
- `GET /modules` — lista dei file modulo disponibili
- `GET /modules/{name}` — contenuto testuale di un modulo (es. `base_profile.txt`)
- `GET /modules/{name}/meta` — info sintetiche sul modulo (dimensione, tipo) + versioning/compatibilità se presenti nell'header
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
