# Razze non-core complete (77) + subrazze/alternate traits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Portare `races.json` a copertura completa dell'indice AoN (7 core + 70 non-core = **77 razze**) e arricchire TUTTE le entry con `mechanics.subraces` e `mechanics.alternate_traits` (replaces strutturato), con split PI in `pi_local_only/subraces.json` e follow-up oracolo 29/29.

**Architecture:** Task 1 estende i parser in `tools/import_reference.py`: `parse_race_subraces`/`parse_race_alternate_traits` (sezioni h1.title, markup annidato E a siblings — AoN è incoerente) agganciati a `parse_race`. Task 2: enumerazione deterministica dai due indici `Races.aspx?Category=Core|NonCore`, integrazione in `build_races` (assert ability_mods → raccolta anomalie report-only), split PI (nomi subrace/trait PI → `subraces_local.json`). Task 3: warm-cache seriale (53 pagine), dry-run, apply, gate legal. Task 4: review swarm a batch, gate seriali, doc, notifica oracolo 29/29 a pathmaster-dd, handoff.

**Tech Stack:** Python 3, BeautifulSoup, pytest, `tools/reference_fetch`. Nessuna nuova dipendenza.

**Spec (grilling 2026-07-25):** perimetro C (tutto l'indice AoN); scope B (subrazze + alternate traits) su TUTTE le 77 (retrofit 24 da cache); Favored Class Options escluse; `subraces [{name, description}]`, `alternate_traits [{name, replaces[], description, source}]`; nomi PI → local con campo `race`; anomalie ability-mods report-only (fallback `{"any": 2}` esistente); notifica oracolo 29/29.

---

### Task 1: Parser subrazze + alternate traits

**Files:**
- Modify: `tooling/Master-DD-Taverna/tools/import_reference.py` (`parse_race` + 3 funzioni nuove)
- Test: `tooling/Master-DD-Taverna/tests/test_import_reference.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_import_reference.py`, dopo `test_parse_race_exotic_strix`, aggiungere:

```python
RACE_SECTIONS_HTML = """
<html><body>
<h1 class="title">Elf Racial Traits</h1>
<p><b>+2 Dexterity, +2 Intelligence, –2 Constitution</b>: Elves are nimble.</p>
<p><b>Medium</b>: Elves are Medium creatures.</p>
<p><b>Normal Speed</b>: Elves have a base speed of 30 feet.</p>
<p><b>Languages</b>: Elves begin play speaking Common and Elven. Elves with high Intelligence scores can choose from the following: Celestial, Draconic.</p>
<h1 class="title">Subraces</h1>
<h3 class="framing">Aquatic Elves</h3>
<p>These elves live beneath the waves.</p>
<h3 class="framing">Ekujae Elves</h3>
<p>Wild elves of the jungle.</p>
<h1 class="title">Elf Alternate Racial Trait<h2 class="title">Replaces Elven Immunities</h2><b><img src="images\\PathfinderSocietySymbol.gif"/> Blightborn</b><br /><b>Source</b> <a href="http://paizo.com/x"><i>Horror Adventures pg. 38</i></a><br />Elves from cursed lands develop resistance. This racial trait replaces elven immunities.<br /><br /><b>Dreamspeaker</b><br /><b>Source</b> <a href="http://paizo.com/y"><i>Advanced Race Guide pg. 22</i></a><br />A few elves tap into dreams. This racial trait replaces elven immunities.<h2 class="title">Replaces Keen Senses</h2><b>Sharp Senses</b><br /><b>Source</b> <a href="http://paizo.com/z"><i>Advanced Race Guide pg. 22</i></a><br />Keener than keen.</h1>
<h1 class="title">Elf Favored Class Options</h1>
<p>Wizard: +1/2 bonus.</p>
</body></html>
"""


def test_parse_race_subraces_and_alternate_traits():
    """Sezioni Subraces (h3.framing siblings) e Alternate Racial Trait
    (contenuto annidato nell'h1): parse con replaces strutturato; Favored
    Class Options escluse."""
    entry = parse_race(RACE_SECTIONS_HTML, "Elf")
    mech = entry["mechanics"]
    assert mech["ability_mods"] == {"dex": 2, "int": 2, "con": -2}
    subs = mech["subraces"]
    assert [s["name"] for s in subs] == ["Aquatic Elves", "Ekujae Elves"]
    assert subs[0]["description"] == "These elves live beneath the waves."
    alts = mech["alternate_traits"]
    assert [a["name"] for a in alts] == ["Blightborn", "Dreamspeaker", "Sharp Senses"]
    assert alts[0]["replaces"] == ["Elven Immunities"]
    assert alts[0]["source"] == "Horror Adventures"
    assert alts[0]["description"].startswith("Elves from cursed lands")
    assert alts[2]["replaces"] == ["Keen Senses"]
    # Favored Class Options NON finiscono da nessuna parte
    assert "Wizard" not in str(mech)


def test_parse_race_without_sections_gives_empty_lists():
    entry = parse_race(CLASS_HTML_FREE_MINIMAL := """
<html><body>
<h1 class="title">Human Racial Traits</h1>
<p><b>+2 to One Ability Score</b>: Humans get +2 to one ability.</p>
<p><b>Medium</b>: Humans are Medium creatures.</p>
<p><b>Normal Speed</b>: Humans have a base speed of 30 feet.</p>
<p><b>Languages</b>: Humans begin play speaking Common.</p>
</body></html>
""", "Human")
    assert entry["mechanics"]["subraces"] == []
    assert entry["mechanics"]["alternate_traits"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tooling/Master-DD-Taverna && .venv/Scripts/python -m pytest tests/test_import_reference.py -k subraces -v`
Expected: FAIL — `KeyError: 'subraces'`.

- [ ] **Step 3: Implement i parser**

In `tools/import_reference.py`, dopo `parse_race` (o prima), aggiungere:

```python
def _iter_section(soup, h1_pred):
    """Elementi di una sezione h1.title fino alla h1.title successiva.

    AoN e' incoerente: la sezione Alternate Racial Trait e' ANNIDATA dentro
    l'h1 (markup malformato), la sezione Subraces e' a SIBLING. Si iterano
    prima i descendants dell'h1 poi i siblings fino alla prossima h1.title."""
    from bs4 import NavigableString, Tag
    h1 = next((h for h in soup.find_all("h1", class_="title")
               if h1_pred(clean(h.get_text()))), None)
    if h1 is None:
        return
    for el in h1.descendants:
        yield el
    for sib in h1.next_siblings:
        if isinstance(sib, Tag) and sib.name == "h1" and "title" in (sib.get("class") or []):
            break
        if isinstance(sib, Tag):
            for el in sib.descendants:
                yield el
            yield sib


def _section_text_nodes(el):
    """True per i NavigableString di contenuto (non dentro b/i/a/h/sup)."""
    from bs4 import NavigableString
    return isinstance(el, NavigableString) and el.parent.name not in (
        "b", "i", "a", "h1", "h2", "h3", "sup", "script", "style")


def parse_race_subraces(html):
    """Sezione 'Subraces': [{name, description}] da h3.framing + prosa."""
    soup = BeautifulSoup(html, "html.parser")
    subs, current, parts = [], None, []

    def flush():
        if current:
            subs.append({"name": current,
                         "description": clean(" ".join(p for p in parts if p))})

    for el in _iter_section(soup, lambda t: t.strip().lower() == "subraces"):
        if getattr(el, "name", None) == "h3" and "framing" in (el.get("class") or []):
            flush()
            current, parts = clean(el.get_text()), []
        elif _section_text_nodes(el):
            if current:
                parts.append(clean(str(el)))
    flush()
    return subs


def parse_race_alternate_traits(html):
    """Sezione '<Race> Alternate Racial Trait[s]': [{name, replaces, source, description}].

    Gruppi h2.title 'Replaces X' (replaces pre-digerito AoN); nomi tratto in
    <b> (con img PFS opzionale); source dal primo <i> con 'pg.'; description =
    prosa fino al tratto/gruppo successivo."""
    soup = BeautifulSoup(html, "html.parser")
    traits, current, parts, source = [], None, [], ""
    replaces = []

    def flush():
        if current:
            traits.append({"name": current, "replaces": list(replaces),
                           "source": source,
                           "description": clean(" ".join(p for p in parts if p))})

    for el in _iter_section(soup, lambda t: "alternate racial trait" in t.lower()):
        name_attr = getattr(el, "name", None)
        if name_attr == "h2" and "title" in (el.get("class") or []):
            m = re.match(r"(?i)\s*Replaces\s+(.+)", clean(el.get_text()))
            if m:
                flush()
                current, parts, source = None, [], ""
                replaces = [x.strip() for x in m.group(1).split(",") if x.strip()]
            continue
        if name_attr == "b":
            t = clean(el.get_text())
            if t and t != "Source":
                flush()
                current, parts, source = t, [], ""
            continue
        if name_attr == "i":
            txt = clean(el.get_text())
            if current and not source and "pg." in txt:
                source = re.sub(r"\s*pg\.\s*\d+.*$", "", txt).strip()
            continue
        if _section_text_nodes(el):
            if current:
                parts.append(clean(str(el)))
    flush()
    return traits
```

Poi in `parse_race`: aggiungere le due chiavi a `mech` subito dopo la sua inizializzazione e popolarle in coda, e aggiornare la docstring. Modifica concreta — sostituire la riga di init:

```python
    mech = {"ability_mods": {}, "size": None, "speed": None, "traits": [],
            "languages": {"auto": [], "bonus": []}}
```

con:

```python
    mech = {"ability_mods": {}, "size": None, "speed": None, "traits": [],
            "languages": {"auto": [], "bonus": []},
            "subraces": parse_race_subraces(html),
            "alternate_traits": parse_race_alternate_traits(html)}
```

e la docstring da "SOLO tratti base CRB (OGC): subrazze/alternate/favored options NON parse (PI Golarion)." a:

```python
    """Pagina RacesDisplay: sezione 'Racial Traits' con righe bold-led,
    piu' sezioni Subraces e Alternate Racial Trait (lotto 2026-07-25).

    Favored Class Options NON parse (scope: subrazze + alternate traits)."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_import_reference.py -v`
Expected: tutto verde (i 2 nuovi + nessuna regressione sulle fixture esistenti: le fixture senza sezioni ottengono liste vuote).

- [ ] **Step 5: Commit**

```bash
cd tooling/Master-DD-Taverna
git add tools/import_reference.py tests/test_import_reference.py planning/2026-07-25-noncore-races-complete.md
git commit -m "feat(tools): parse race subraces and alternate traits sections"
```

---

### Task 2: Enumerazione indice + integrazione build_races + split PI

**Files:**
- Modify: `tooling/Master-DD-Taverna/tools/import_reference.py` (`race_index_names`, `build_races`, split PI)
- Test: `tooling/Master-DD-Taverna/tests/test_import_reference.py` (fixture indice + split PI)

- [ ] **Step 1: Write the failing test**

Aggiungere a `tests/test_import_reference.py`:

```python
RACE_INDEX_HTML = """
<html><body>
<a href="RacesDisplay.aspx?ItemName=Aasimar">Aasimar</a>
<a href="RacesDisplay.aspx?ItemName=Catfolk">Catfolk</a>
<a href="RacesDisplay.aspx?ItemName=Aasimar">Aasimar</a>
<a href="RacesDisplay.aspx?ItemName=Vine%20Leshy">Vine Leshy</a>
</body></html>
"""


def test_race_index_names_from_html():
    from tools.import_reference import _race_index_names_from_html
    assert _race_index_names_from_html(RACE_INDEX_HTML) == [
        "Aasimar", "Catfolk", "Vine Leshy"]


def test_pi_split_moves_named_subraces():
    """Nomi subrace/trait PI -> subraces_local con campo race; gli altri restano."""
    from tools.import_reference import _pi_split_race_sections
    entry = {"name": "Elf", "mechanics": {
        "subraces": [{"name": "Aquatic Elves", "description": "x"},
                     {"name": "Ekujae Elves", "description": "y"}],
        "alternate_traits": [{"name": "Blightborn", "replaces": ["Elven Immunities"],
                              "source": "Horror Adventures", "description": "z"}]}}
    local = []
    _pi_split_race_sections(entry, local)
    assert [s["name"] for s in entry["mechanics"]["subraces"]] == ["Aquatic Elves"]
    assert local == [{"race": "Elf", "kind": "subrace", "name": "Ekujae Elves",
                      "description": "y"}]
    assert entry["mechanics"]["alternate_traits"][0]["name"] == "Blightborn"
```

Nota: "Ekujae" deve risultare PI (`is_pi_name`): verifica preliminare che "Ekujae" sia in PI_WORDS; se non lo fosse, il test guida l'aggiunta del termine alla lista gate (stessa procedura dei supplementi precedenti) oppure va scelto un altro nome PI reale come fixture.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_import_reference.py -k "race_index or pi_split" -v`
Expected: FAIL — ImportError/attributi mancanti.

- [ ] **Step 3: Implement enumerazione + build + split**

In `tools/import_reference.py`:

```python
def _race_index_names_from_html(html):
    """Link RacesDisplay di una pagina indice -> nomi, dedup in ordine."""
    out = []
    for n in re.findall(r"RacesDisplay\.aspx\?ItemName=([^\"&]+)", html):
        n = n.replace("%20", " ")
        if n not in out:
            out.append(n)
    return out


def race_index_names():
    """Tutte le razze non-core dall'indice AoN (fetch seriale con cache)."""
    html = fetch(BASE + "Races.aspx?Category=NonCore")
    return _race_index_names_from_html(html)
```

In `build_races`: sostituire il loop `for race in RACES_ALL:` con l'unione enumerata e trasformare l'assert ability_mods in raccolta anomalie:

```python
    races = RACES_CORE + [n for n in race_index_names() if n not in RACES_CORE]
    anomalies = []
    local_subraces = []
    for race in races:
        url = BASE + f"RacesDisplay.aspx?ItemName={race.replace(' ', '%20')}"
        parsed = parse_race(fetch(url), race)
        if not parsed["mechanics"]["ability_mods"]:
            anomalies.append(race)
            print(f"nota: {race}: ability_mods non parsati (report-only, nessuna invenzione)")
        # ... blocco lingue PI invariato ...
        _pi_split_race_sections(parsed, local_subraces)
        if race in by_name:
            by_name[race].update(parsed)
        else:
            catalog["entries"].append(parsed)
    if anomalies:
        print(f"ATTENZIONE: ability_mods mancanti per {len(anomalies)} razze: {', '.join(anomalies)}")
```

E la funzione di split (con sanitize delle description):

```python
def _pi_split_race_sections(entry, local_out):
    """Subraces/traits con nome PI -> local_out (campo race); description sanitize."""
    mech = entry["mechanics"]
    for key, kind in (("subraces", "subrace"), ("alternate_traits", "alternate_trait")):
        kept = []
        for item in mech.get(key, []):
            item["description"] = sanitize_text(item.get("description") or "", description=True)
            if is_pi_name(item["name"]):
                local_out.append({"race": entry["name"], "kind": kind, **item})
            else:
                kept.append(item)
        mech[key] = kept
```

Import necessari in cima: `from tools.expand_spells_gist import is_pi_name`, `from tools.sanitize_reference_pi import sanitize_text`.

Scrittura `subraces_local.json`: in `build_races(write=True)`, dopo `write_catalog`, scrivere `pi_local_only/subraces_local.json` (header `_license`/`_source` local-only, entries=local_subraces) e stampare il conteggio. Update manifest (files.races + catalogs races/subraces_local) nel Task 3 Step 3 (dopo il conteggio reale), non nel builder: il manifest resta un'operazione da gate.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_import_reference.py -v`
Expected: verde.

- [ ] **Step 5: Commit**

```bash
cd tooling/Master-DD-Taverna
git add tools/import_reference.py tests/test_import_reference.py
git commit -m "feat(tools): enumerate noncore races and split pi subraces"
```

---

### Task 3: Warm-cache + dry-run + apply + gate legal

**Files:**
- Modify (generati): `data/reference/ogl/races.json`, `data/reference/pi_local_only/subraces_local.json` (NON committato), `data/reference/manifest.json`

- [ ] **Step 1: Warm-cache seriale (53 pagine)**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -c "
import sys; sys.path.insert(0, '.')
from tools.reference_fetch import fetch, cache_path
from tools.import_reference import race_index_names, RACES_CORE, BASE
ok = fail = 0
for n in race_index_names():
    url = BASE + 'RacesDisplay.aspx?ItemName=' + n.replace(' ', '%20')
    if cache_path(url).exists():
        ok += 1; continue
    try:
        fetch(url, delay=2.0, cache=True); ok += 1
    except Exception as exc:
        fail += 1; print('FALLITO', n, str(exc)[:70])
print(f'cache: {ok} ok, {fail} falliti')
"
```

Expected: 70 ok in ~2 minuti (le 17 esotiche già in cache). Falliti: annotare, verificare URL sulla pagina indice.

- [ ] **Step 2: Dry-run**

```bash
.venv/Scripts/python tools/import_reference.py --domain races
```

Expected: report con 77 entry; anomalie ability_mods elencate (attese per razze anomale: Android, Wyrwood, Green Martian...); subrazze/trait PI stampati. **Controllare che le 24 esistenti non perdano campi** (merge in place preserva i curati).

- [ ] **Step 3: Apply + manifest + gate legal**

```bash
.venv/Scripts/python tools/import_reference.py --domain races --write
.venv/Scripts/python -c "
import json
from datetime import date
m = json.load(open('data/reference/manifest.json', encoding='utf-8'))
r = json.load(open('data/reference/ogl/races.json', encoding='utf-8'))
s = json.load(open('data/reference/pi_local_only/subraces_local.json', encoding='utf-8'))
m['files']['races']['entries'] = len(r['entries'])
today = date.today().isoformat()
for c in m['catalogs']:
    if c['kind'] == 'races':
        c['entries'] = len(r['entries']); c['last_verified'] = today
m['catalogs'] = [c for c in m['catalogs'] if c['kind'] != 'subraces_local']
m['catalogs'].append({
    'file': 'pi_local_only/subraces_local.json', 'kind': 'subraces_local',
    'source': 'Archives of Nethys (aonprd.com)', 'license': 'OGL-1.0a',
    'is_ogc': False, 'is_pi': False, 'cup_allowed': False, 'local_only': True,
    'entries': len(s['entries']),
    'notes': 'Subrazze/alternate racial traits con nome PI (policy 2026-07-25). NON redistribuire.',
    'last_verified': today})
json.dump(m, open('data/reference/manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('manifest: races', len(r['entries']), '| subraces_local', len(s['entries']))
"
.venv/Scripts/python tools/legal_filter.py
```

Expected: races 77; legal_filter **0 violazioni** (se residui: supplemento DESCRIPTION_ONLY + revert + re-apply, come da pattern). Verificare `git status` NON elenchi `subraces_local.json`.

- [ ] **Step 4: Validazione deterministica**

```bash
.venv/Scripts/python -c "
import json
r = json.load(open('data/reference/ogl/races.json', encoding='utf-8'))
es = r['entries']
names = [e['name'] for e in es]
assert len(set(names)) == len(names), 'duplicati!'
assert len(es) == 77, len(es)
no_mods = [e['name'] for e in es if not e['mechanics']['ability_mods']]
subs = sum(len(e['mechanics'].get('subraces', [])) for e in es)
alts = sum(len(e['mechanics'].get('alternate_traits', [])) for e in es)
print(f'77 razze OK; senza ability_mods: {len(no_mods)} {no_mods}')
print(f'subraces: {subs}; alternate_traits: {alts}')
"
```

Expected: 77, nessuna assertion. Se le senza-mods sono >8, ispezionare prima di procedere (possibile regressione parser).

- [ ] **Step 5: Commit**

```bash
cd tooling/Master-DD-Taverna
git add data/reference/ogl/races.json data/reference/manifest.json
git commit -m "feat(reference): complete race coverage to all 77 aon races"
```

---

### Task 4: Review swarm, gate seriali, doc, oracolo, handoff

- [ ] **Step 1: Review swarm (sostitutivo strutturato dello spot check)**

Dispatch di **8 subagent explore** in parallelo (AgentSwarm), ciascuno con ~10 razze assegnate: per ogni razza, confrontare 1 entry del catalogo con la pagina in cache (`data/reference/aon_cache/`, path ottenuto da `tools/reference_fetch.cache_path` dell'URL `RacesDisplay.aspx?ItemName=<Razza>`): ability_mods, size, speed, 2 tratti a campione, 1 subrace/trait alternativo a campione. Output: lista anomalie per razza (o "conforme"). Il controller raccoglie e valuta; anomalie vere → fix mirato prima dei gate.

- [ ] **Step 2: Gate seriali**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -m pytest tests/ -q
.venv/Scripts/python tools/validate_schemas.py
.venv/Scripts/python tools/legal_filter.py
.venv/Scripts/python tools/index_rag.py --include-local
cd ../.. && python launch.py test
```

Expected: tutto verde; reindice ri-encoda i chunk races (77 entry modificate).

- [ ] **Step 3: Nota IMPORT_PLAYBOOK §6.6 + commit/push**

```markdown
## 6.6 Razze complete (2026-07-25)

`races.json` a copertura completa: 7 core + 70 non-core enumerate dagli indici `Races.aspx?Category=Core|NonCore` (`race_index_names()`). Tutte le 77 entry hanno `mechanics.subraces` e `mechanics.alternate_traits` (replaces strutturato AoN); nomi PI → `pi_local_only/subraces_local.json` (campo `race`). Ability-mods mancanti = report-only (nessuna invenzione). Favored Class Options escluse (candidato futuro). Rigenerare con `import_reference.py --domain races --write`.
```

Commit + push.

- [ ] **Step 4: Notifica oracolo 29/29 a pathmaster-dd**

Creare `tooling/pathmaster-dd/docs/superpowers/specs/2026-07-25-oracolo-29-29-aasimar.md`: Aasimar importata (lotto razze complete), `paladin_aasimar` sbloccata, copertura 29/29; resta valido il caveat normalizzazione nomi. Commit nel repo pathmaster-dd (soggetto ≤72 char). Aggiornare la riga "Copertura oracolo" in `docs/WORKFLOW.md` §4 (29/29) e committare in Master-DD-Taverna.

- [ ] **Step 5: Handoff**

Aggiornare `sessione-2026-07-16/HANDOFF_ATTIVO.md` + `AVVIO_PROSSIMA_SESSIONE.md` (coda) e sincronizzare le 5 fonti `notebooklm-fonti/`.

---

## Self-Review

**Spec coverage:**
- Perimetro C (tutto l'indice) → Task 2 enumerazione + Task 3 ✓
- Subrazze + alternate traits su tutte le 77 (retrofit incluso: build_races riparsea anche le 24 esistenti da cache) → Task 1 + Task 2 build ✓
- Schema {subraces, alternate_traits con replaces/source/description} → Task 1 ✓
- PI split con campo race + sanitize + legal 0 → Task 2 + Task 3 Step 3 ✓
- Anomalie report-only → Task 2 Step 3 ✓
- Favored Class Options escluse → Task 1 test esplicito ✓
- Review swarm → Task 4 Step 1 ✓
- Oracolo 29/29 → Task 4 Step 4 ✓
- Gate/doc/handoff → Task 4 ✓

**Placeholder scan:** una nota di verifica fixture ("Ekujae" in PI_WORDS) con istruzione concreta di fallback; nessun TBD.

**Type consistency:** `parse_race_subraces(html) -> list[{name, description}]`; `parse_race_alternate_traits(html) -> list[{name, replaces, source, description}]`; `_race_index_names_from_html(html) -> list[str]`; `_pi_split_race_sections(entry, local_out) -> None` — identici in tool e test. Riutilizzo verificato: `is_pi_name` (expand_spells_gist), `sanitize_text` (sanitize_reference_pi), `fetch/cache_path/BASE/clean` (già in import_reference).
