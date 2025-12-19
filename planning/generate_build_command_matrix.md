# Comandi e piani di raccolta build (mode=extended)

Questa matrice raccoglie i comandi aggiornati per eseguire `tools/generate_build_db.py` in modalità `extended`, con discovery moduli e filtri mirati. Gli esempi sono pensati per colmare i gap prioritari delle schede PF1e combinando classi, razze, archetipi e hook di background senza duplicare payload inutili.

## Principi guida
- **Modalità fissa:** usare sempre `--mode extended` per ottenere payload a 16 step e validazione completa degli slot narrativi.
- **Spec e combinazioni:** preferire `--spec-file` (per preservare la copertura manuale) e usare `--races`/`--archetypes`/`--background-hooks` solo per colmare cluster mancanti.
- **Discovery moduli:** attivare `--discover-modules` e applicare filtri `--include`/`--exclude` per scaricare solo i target necessari (scheda + narrativa) riducendo il carico API.
- **Strict first:** eseguire prima un passaggio `--strict` e, se servono payload incompleti per analisi, ripetere con `--keep-invalid` + `--dual-pass-report` per un confronto immediato.

## Comandi base (spec file)
- **Run prioritario con spec esteso e discovery:**
  ```bash
  API_URL=$API_URL API_KEY=$API_KEY \
  python tools/generate_build_db.py \
    --api-url ${API_URL:-http://localhost:8000} \
    --mode extended \
    --spec-file docs/examples/pg_variants.yml \
    --discover-modules --include 'scheda_*' 'narrative_*' --exclude 'test_*' \
    --output-dir src/data/builds --modules-output-dir src/data/modules \
    --index-path src/data/build_index.json --module-index-path src/data/module_index.json \
    --max-retries 3 --strict
  ```
  - Usa lo spec ufficiale e filtra i moduli generando solo scheda+narrativa.

- **Spec alternativo con livelli mirati:**
  ```bash
  python tools/generate_build_db.py \
    --mode extended --spec-file planning/mesmerist_catfolk_spec.yml \
    --discover-modules --include '*.txt' --exclude 'debug_*' \
    --levels 1 5 10 --max-items 12 --skip-unchanged \
    --output-dir src/data/builds --modules-output-dir src/data/modules \
    --index-path src/data/build_index.json --module-index-path src/data/module_index.json \
    --strict
  ```

## Comandi combinatori (gap coverage)
- **Prodotto cartesiano classe/razza/archetipo/background:**
  ```bash
  python tools/generate_build_db.py \
    --mode extended --classes Alchemist Bard Cavalier Ranger \
    --races Catfolk Aasimar Dhampir \
    --archetypes "Beast Rider" "Trapper" "Urban Barbarian" \
    --background-hooks "Guild Agent" "Frontier Tracker" \
    --discover-modules --include 'scheda_*' 'narrative_*' --exclude 'legacy_*' \
    --keep-all-combos --prefer-unused-race \
    --output-dir src/data/builds --modules-output-dir src/data/modules \
    --index-path src/data/build_index.json --module-index-path src/data/module_index.json \
    --max-retries 3 --strict
  ```
  - Mantiene tutte le combinazioni generate, utile per riempire i cluster meno coperti.

- **Batch piccolo per archetipi mancanti (con fallback spec disattivato):**
  ```bash
  python tools/generate_build_db.py \
    --mode extended --no-default-spec \
    --classes Cleric Inquisitor Paladin \
    --archetypes "Sacred Shield" "Sanctified Slayer" \
    --background-hooks "Temple Archivist" \
    --races "Human" "Aasimar" \
    --discover-modules --include '*.txt' --exclude 'test_*' \
    --max-items 8 --offset 0 --skip-unchanged \
    --output-dir src/data/builds --modules-output-dir src/data/modules \
    --index-path src/data/build_index.json --module-index-path src/data/module_index.json \
    --strict
  ```

## Aggiornamento catalogo RAW/SRD
Quando servono nuove voci di riferimento (talenti, archetipi, hook di background):
1. Aggiungere/aggiornare i record in `data/reference/*.json` seguendo lo schema `reference_catalog.schema.json`.
2. Aggiornare `data/reference/manifest.json` incrementando `version` e includendo i nuovi file.
3. Sincronizzare `src/data/module_index.json` se cambiano i moduli di riferimento o il loro `reference_catalog_version`.
4. Rieseguire `python tools/generate_build_db.py --validate-db --review-output src/data/build_review.json` per verificare gli indici locali.

## Snapshot, rollback e versioning indici
- **Snapshot pre-run:**
  ```bash
  SNAP_DIR=reports/snapshots/$(date -u +"%Y%m%dT%H%M%SZ")
  mkdir -p "$SNAP_DIR"
  cp src/data/build_index.json "$SNAP_DIR/build_index.pre.json"
  cp src/data/module_index.json "$SNAP_DIR/module_index.pre.json"
  ```
- **Snapshot post-run:**
  ```bash
  cp src/data/build_index.json "$SNAP_DIR/build_index.post.json"
  cp src/data/module_index.json "$SNAP_DIR/module_index.post.json"
  ```
- **Rollback rapido:**
  ```bash
  cp "$SNAP_DIR/build_index.pre.json" src/data/build_index.json
  cp "$SNAP_DIR/module_index.pre.json" src/data/module_index.json
  ```
- **Versioning consigliato:** includere il timestamp ISO nel nome del sottofolder e annotare l'actor/comando usato in un README locale nel folder snapshot.
