# Item Forge — generazione oggetti magici PF1e (A-leggera)

Generazione di oggetti magici custom con **numeri deterministici** e **flavor LLM** separati (PRD §9.2, decisione 4, ratifica 2026-07-26). Eredita lo schema "Formato Torneo" dal legacy `tooling/Item-generator` (archiviato); il suo DB "588 oggetti" si è rivelato una lista di intestazioni di pagina AoN senza dati (non importato — i dati veri sono i cataloghi reference già in casa).

## Filosofia

- **Numeri = deterministico verificato** (`tools/item_forge.py`): prezzi da formule ufficiali (incantesimo × LI × fattore uso; bonus² × fattore tipo; bacchette/bastoni ×750/×400), costo crafting = prezzo/2, LI minimo RAW (2×livello−1), aura da LI, CD, rarità. Ogni input invalido è un errore onesto (mai default silenziosi).
- **Flavor = LLM** (`tools/item_forge_flavor.py`): Ollama (`OLLAMA_BASE_URL`/`OLLAMA_MODEL`, come il provider RAG) produce nome, descrizione (2-4 frasi senza regole), 3 bullet di dettaglio, nota playtest, hook — con validazione JSON. Badge finale esplicito: "deterministico verificato · LLM da verificare al tavolo".
- **Incantesimi dal catalogo**: `forge_from_spell("fireball", 5)` risolve livello/scuola da `spells.json` (mechanics), errore onesto con suggerimenti se il nome manca.

## Uso

```bash
.venv/Scripts/python tools/item_forge_flavor.py \
  "un anello che protegge dal fuoco, dono di un drago rosso pentito" \
  --spell "resist energy" --cl 5
# oppure JSON: --json
```

Output: markdown Formato Torneo (aura/LI/slot/prezzo/rarità deterministici + flavor).

## Test

`tests/test_item_forge.py` (23: formule + lookup + blocco, con riferimenti ufficiali — ring of protection 2.000, cloak of resistance 1.000, wand of fireball 11.250) e `tests/test_item_forge_flavor.py` (8: parse/prompt/render con LLM iniettato, niente Ollama nei test).

## Limite noto

Il flavor dal 7B/14B locale è grezzo (inventa meccaniche nei bullet): i numeri restano affidabili, il testo va revisionato dal GM — per questo il badge lo dichiara. Migliora col modello di default via `OLLAMA_MODEL`.
