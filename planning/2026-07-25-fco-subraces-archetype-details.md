# FCO + subrazze meccaniche + dettagli ArchetypeDisplay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tre arricchimenti catalogo confermati 2026-07-25: (3) `favored_class_options` su tutte le 77 razze (offline, pagine in cache); (4) subrazze con `source` + attribuzione `alternate_traits` (offline); (2) `features` complete (level/replaces/alters/text) sui 961 archetipi da ArchetypeDisplay (fetch seriale ~35 min).

**Architecture:** Task 1 e 2 estendono `tools/import_reference.py` (parser sezioni razza + build_races). Task 3 estende `tools/import_archetypes.py` con fetch dettagli + parse features. Ogni task: TDD, apply, gate legal, commit. Gate finali + doc + handoff in coda.

**Tech Stack:** Python 3, BeautifulSoup, pytest, `tools/reference_fetch`. Nessuna nuova dipendenza.

**Spec (confermate 2026-07-25):** FCO `[{class, source, bonus}]`; subraces `[{name, source, description, alternate_traits[]}]` (frase "have the X alternate racial trait(s)", zero invenzioni); archetype `features [{name, level, replaces[], alters[], text}]` (suffissi (Ex)/(Su)/(Sp) tolti dal nome; `mechanics.replaces` di indice resta come sommario).

---

### Task 1: Favored Class Options (77 razze, offline)

**Files:**
- Modify: `tooling/Master-DD-Taverna/tools/import_reference.py` (`parse_race_favored_class_options` + hook in `parse_race`)
- Test: `tooling/Master-DD-Taverna/tests/test_import_reference.py`

- [ ] **Step 1: Write the failing test**

Aggiungere a `tests/test_import_reference.py`:

```python
RACE_FCO_HTML = """
<html><body>
<h1 class="title">Elf Racial Traits</h1>
<p><b>+2 Dexterity, +2 Intelligence, –2 Constitution</b>: Elves are nimble.</p>
<p><b>Medium</b>: Elves are Medium creatures.</p>
<p><b>Normal Speed</b>: Elves have a base speed of 30 feet.</p>
<p><b>Languages</b>: Elves begin play speaking Common and Elven.</p>
<h1 class="title">Elf Favored Class Options</h1>Instead of receiving an additional skill rank or hit point, Elves have options.<br /><br /><b><img src="images\\PathfinderSocietySymbol.gif"/> Alchemist</b> (<a href="http://paizo.com/x"><i>Advanced Race Guide pg. 23</i></a>): Add one extract formula to his formula book.<br /><b>Arcanist</b> (<a href="http://paizo.com/y"><i>Advanced Class Guide pg. 69</i></a>): Increase points in the arcane reservoir by 1.<br />
</body></html>
"""


def test_parse_race_favored_class_options():
    """Sezione '<Race> Favored Class Options': [{class, source, bonus}]."""
    entry = parse_race(RACE_FCO_HTML, "Elf")
    fco = entry["mechanics"]["favored_class_options"]
    assert len(fco) == 2
    assert fco[0] == {"class": "Alchemist", "source": "Advanced Race Guide",
                      "bonus": "Add one extract formula to his formula book."}
    assert fco[1]["class"] == "Arcanist"
    assert fco[1]["source"] == "Advanced Class Guide"
    assert fco[1]["bonus"].startswith("Increase points")
    # intro della sezione NON finisce nei bonus
    assert "Instead of receiving" not in str(fco)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tooling/Master-DD-Taverna && .venv/Scripts/python -m pytest tests/test_import_reference.py -k favored -q`
Expected: FAIL — KeyError 'favored_class_options'.

- [ ] **Step 3: Implement**

In `tools/import_reference.py`, dopo `parse_race_alternate_traits`:

```python
def parse_race_favored_class_options(html):
    """Sezione '<Race> Favored Class Options': [{class, source, bonus}].

    Entry regolari: '<b>Classe</b> (<a><i>Libro pg. N</i></a>): bonus<br />'.
    L'intro della sezione e' saltata (accumulo solo dopo il primo <b>)."""
    soup = BeautifulSoup(html, "html.parser")
    options, current, parts, source = [], None, [], ""

    def flush():
        if current:
            options.append({"class": current, "source": source,
                            "bonus": clean(" ".join(p for p in parts if p)).lstrip("(:; ") .rstrip(".") + "."})

    for el in _iter_section(soup, lambda t: "favored class options" in t.lower()):
        name_attr = getattr(el, "name", None)
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
    return options
```

In `parse_race`, aggiungere la chiave a `mech`:

```python
            "subraces": parse_race_subraces(html),
            "alternate_traits": parse_race_alternate_traits(html),
            "favored_class_options": parse_race_favored_class_options(html)}
```

- [ ] **Step 4: Run test + apply + gate**

```bash
.venv/Scripts/python -m pytest tests/test_import_reference.py -q        # verde
.venv/Scripts/python tools/import_reference.py --domain races --write   # 77 entry
.venv/Scripts/python -c "
import json
r = json.load(open('data/reference/ogl/races.json', encoding='utf-8'))
n = sum(len(e['mechanics'].get('favored_class_options', [])) for e in r['entries'])
empty = [e['name'] for e in r['entries'] if not e['mechanics'].get('favored_class_options')]
print('FCO totali:', n, '| razze senza:', len(empty), empty[:10])
"
.venv/Scripts/python tools/legal_filter.py                              # 0 violazioni
```

Expected: centinaia di FCO; alcune razze senza (mostruose/recenti — atteso, report a video). Se legal >0: sanitize supplement + revert + re-apply.

- [ ] **Step 5: Commit** `feat(tools): parse favored class options for all races`

---

### Task 2: Subrazze con source + attribuzione alternate_traits

**Files:**
- Modify: `tooling/Master-DD-Taverna/tools/import_reference.py` (`parse_race_subraces`)
- Test: `tooling/Master-DD-Taverna/tests/test_import_reference.py`

- [ ] **Step 1: Write the failing test**

Aggiungere (dopo il test FCO):

```python
RACE_SUBRACE_ATTR_HTML = """
<html><body>
<h1 class="title">Subraces</h1>
<h3 class="framing">Aquatic Elves</h3><b>Source</b> <a href="http://paizo.com/x"><i>Heroes from the Fringe pg. 10</i></a><br />Aquatic elves are the oceanic cousins of landborn elves. These elves often have the aquatic mastery alternate racial trait described below.<br /><br /><h3 class="framing">Tower Elf</h3><b>Source</b> <a href="http://paizo.com/y"><i>Advanced Race Guide pg. 23</i></a><br />These elves have the arcane focus and urbanite alternate racial traits.<br /><br />
</body></html>
"""


def test_parse_race_subraces_source_and_trait_attribution():
    """Subraces: source dal <i> con pg.; alternate_traits dalla frase
    'have the X[, Y and Z] alternate racial trait(s)'. Nessuna invenzione:
    frase assente -> lista vuota."""
    subs = parse_race_subraces(RACE_SUBRACE_ATTR_HTML)
    assert subs[0]["source"] == "Heroes from the Fringe"
    assert subs[0]["alternate_traits"] == ["Aquatic Mastery"]
    assert subs[1]["alternate_traits"] == ["Arcane Focus", "Urbanite"]
    assert subs[1]["source"] == "Advanced Race Guide"
```

Nota: la capitalizzazione dei nomi tratto è normalizzata Title Case ("aquatic mastery" → "Aquatic Mastery").

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_import_reference.py -k attribution -q`
Expected: FAIL — KeyError 'source' / 'alternate_traits'.

- [ ] **Step 3: Implement**

Riscrivere `parse_race_subraces` in `tools/import_reference.py`:

```python
_SUBRACE_ATTR_RE = re.compile(
    r"(?:have|has) the ([^.]+?) alternate racial traits?\b", re.I)


def _split_trait_names(text):
    """'arcane focus and urbanite' -> ['Arcane Focus', 'Urbanite'] (Title Case)."""
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", text.strip())
    return [" ".join(w.capitalize() for w in p.split()) for p in parts if p.strip()]


def parse_race_subraces(html):
    """Sezione 'Subraces': [{name, source, description, alternate_traits}].

    source dal primo <i> con 'pg.'; alternate_traits dalla frase regolare
    'have the X alternate racial trait(s)' (zero invenzioni: assente -> [])."""
    soup = BeautifulSoup(html, "html.parser")
    subs, current, parts, source = [], None, [], ""

    def flush():
        if current:
            desc = clean(" ".join(p for p in parts if p)).lstrip(",; ")
            m = _SUBRACE_ATTR_RE.search(desc)
            subs.append({"name": current, "source": source,
                         "description": desc,
                         "alternate_traits": _split_trait_names(m.group(1)) if m else []})

    for el in _iter_section(soup, lambda t: t.strip().lower() == "subraces"):
        name_attr = getattr(el, "name", None)
        if name_attr == "h3" and "framing" in (el.get("class") or []):
            flush()
            current, parts, source = clean(el.get_text()), [], ""
        elif name_attr == "b":
            continue  # il <b>Source</b> label non e' contenuto
        elif name_attr == "i":
            txt = clean(el.get_text())
            if current and not source and "pg." in txt:
                source = re.sub(r"\s*pg\.\s*\d+.*$", "", txt).strip()
        elif _section_text_nodes(el):
            if current:
                parts.append(clean(str(el)))
    flush()
    return subs
```

- [ ] **Step 4: Run test + apply + gate**

```bash
.venv/Scripts/python -m pytest tests/test_import_reference.py -q        # verde (fixture T1 subraces aggiornata se necessario: ora le sub hanno source/alternate_traits)
.venv/Scripts/python tools/import_reference.py --domain races --write
.venv/Scripts/python -c "
import json
r = json.load(open('data/reference/ogl/races.json', encoding='utf-8'))
subs = [s for e in r['entries'] for s in e['mechanics'].get('subraces', [])]
with_attr = sum(1 for s in subs if s['alternate_traits'])
print(f'subraces: {len(subs)}, con alternate_traits: {with_attr}')
"
.venv/Scripts/python tools/legal_filter.py                              # 0
.venv/Scripts/python -m pytest tests/ -q                                # verde
```

Nota: il test preesistente `test_parse_race_subraces_and_alternate_traits` va aggiornato per le nuove chiavi (source/​alternate_traits vuoti o coerenti con la fixture).

- [ ] **Step 5: Commit** `feat(tools): add source and trait attribution to subraces`

---

### Task 3: Features complete da ArchetypeDisplay (961 archetipi, fetch seriale)

**Files:**
- Modify: `tooling/Master-DD-Taverna/tools/import_archetypes.py` (`parse_archetype_features` + modalità `--details`)
- Test: `tooling/Master-DD-Taverna/tests/test_import_archetypes.py`

- [ ] **Step 1: Write the failing test**

Aggiungere a `tests/test_import_archetypes.py`:

```python
from tools.import_archetypes import parse_archetype_features

ARCHER_HTML = """
<html><body>
<h1 class="title"><img src="images\\PathfinderSocietySymbol.gif"/> Archer</h1><b>Source</b> <a href="http://paizo.com/x"><i>Advanced Player's Guide pg. 104</i></a><br />The archer is dedicated to the mastery of the bow.<br /><br /><b>Hawkeye (Ex)</b>:  At 2nd level, an archer gains a +1 bonus on Perception checks. These bonuses increase by +1 for every 4 levels beyond 2nd. This ability replaces bravery.<br /><br /><b>Trick Shot (Ex)</b>:  At 3rd level, an archer can choose a combat maneuver. This ability alters armor training.<br /><br /><b>Safe Shot (Ex)</b>:  At 9th level, an archer does not provoke. This ability replaces armor training 1 and weapon training 2.<br />
</body></html>
"""


def test_parse_archetype_features():
    feats = parse_archetype_features(ARCHER_HTML)
    assert [f["name"] for f in feats] == ["Hawkeye", "Trick Shot", "Safe Shot"]
    assert feats[0]["level"] == 2
    assert feats[0]["replaces"] == ["bravery"]
    assert feats[0]["alters"] == []
    assert feats[0]["text"].startswith("At 2nd level")
    assert feats[1]["alters"] == ["armor training"]
    assert feats[2]["replaces"] == ["armor training 1", "weapon training 2"]
    assert feats[2]["level"] == 9


def test_parse_archetype_features_no_level():
    html = ARCHER_HTML.replace("At 2nd level, an archer", "An archer")
    feats = parse_archetype_features(html)
    assert feats[0]["level"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_import_archetypes.py -k features -q`
Expected: FAIL — ImportError.

- [ ] **Step 3: Implement in `tools/import_archetypes.py`**

```python
_LEVEL_RE = re.compile(r"\bAt (\d+)(?:st|nd|rd|th) level")
_REPLACES_RE = re.compile(r"(?i)this ability (?:also )?replaces? (?:the )?([^.]+)\.")
_ALTERS_RE = re.compile(r"(?i)this ability (?:also )?alters? (?:the )?([^.]+)\.")
_FEAT_SUFFIX_RE = re.compile(r"\s*\((?:Ex|Su|Sp)\)\s*$")


def _split_feature_list(text):
    """'armor training 1 and weapon training 2' -> ['armor training 1', 'weapon training 2']."""
    text = re.sub(r"(?i)\s+class features?\.?$", "", text.strip())
    text = re.sub(r"(?i)\s+ability\.?$", "", text)
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", text)
    return [p.strip() for p in parts if p.strip()]


def parse_archetype_features(html):
    """Pagina ArchetypeDisplay: [{name, level, replaces, alters, text}].

    Feature = '<b>Nome (Ex|Su|Sp)</b>:' + prosa fino alla feature successiva.
    level = primo 'At Nth level'; replaces/alters dalle frasi 'This ability
    replaces/alters X'. Flavor introduttivo saltato (prima del primo <b>
    non-Source)."""
    from bs4 import BeautifulSoup, NavigableString
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1", class_="title")
    if not h1:
        return []
    container = h1.parent
    feats, current, parts = [], None, []

    def flush():
        if current:
            text = clean(" ".join(p for p in parts if p)).lstrip(": ")
            m = _LEVEL_RE.search(text)
            rep = _REPLACES_RE.search(text)
            alt = _ALTERS_RE.search(text)
            feats.append({
                "name": current,
                "level": int(m.group(1)) if m else None,
                "replaces": _split_feature_list(rep.group(1)) if rep else [],
                "alters": _split_feature_list(alt.group(1)) if alt else [],
                "text": sanitize_text(text, description=True)})

    for el in container.descendants:
        name_attr = getattr(el, "name", None)
        if name_attr == "b":
            t = clean(el.get_text())
            if t and t != "Source":
                flush()
                current, parts = _FEAT_SUFFIX_RE.sub("", t), []
            continue
        if isinstance(el, NavigableString) and el.parent.name not in (
                "b", "i", "a", "h1", "h2", "h3", "sup", "script", "style"):
            if current:
                parts.append(clean(str(el)))
    flush()
    return feats
```

Modalità `--details` in `main()`: per ogni entry (OGL + local), leggere `reference_urls[1]` (detail_url) via `fetch(url, delay=2.0, cache=True)` (o cache-only con `--offline`), fare `entry["mechanics"]["features"] = parse_archetype_features(html)`; conteggio features senza level nel report. Il re-import completo da indice non serve: aggiungere una modalità standalone che legge i due JSON esistenti, arricchisce in place e riscrive (manifest invariato: i count non cambiano).

- [ ] **Step 4: Warm-cache seriale (961 pagine, ~35 min, BACKGROUND)**

```bash
cd tooling/Master-DD-Taverna && .venv/Scripts/python -c "
import sys, json; sys.path.insert(0, '.')
from tools.reference_fetch import fetch, cache_path
ok = fail = 0
for path in ['data/reference/ogl/archetypes.json', 'data/reference/pi_local_only/archetypes_local.json']:
    for e in json.load(open(path, encoding='utf-8'))['entries']:
        url = e['reference_urls'][1]
        if cache_path(url).exists():
            ok += 1; continue
        try:
            fetch(url, delay=2.0, cache=True); ok += 1
        except Exception as exc:
            fail += 1; print('FALLITO', e['name'], str(exc)[:60])
print(f'{ok} ok, {fail} falliti')
"
```

Lanciare in background (timeout ≥ 2400s). Attesi ~961 ok.

- [ ] **Step 5: Apply + gate**

```bash
.venv/Scripts/python tools/import_archetypes.py --details --write --offline
.venv/Scripts/python tools/legal_filter.py   # 0
.venv/Scripts/python -m pytest tests/ -q     # verde
```

Expected: features sulla quasi totalità degli archetipi; report features senza level (atteso: capacità senza livello esplicito). Se legal >0: sanitize supplement + revert + re-apply.

- [ ] **Step 6: Commit** `feat(reference): add archetype features from detail pages`

---

### Task 4: Gate finali, doc, handoff

- [ ] **Step 1: Gate seriali**: pytest, validate_schemas, legal_filter, reindice `--include-local`, `python launch.py test` dalla root.
- [ ] **Step 2: IMPORT_PLAYBOOK §6.7** (FCO + subrazze meccaniche + archetype features) + commit/push.
- [ ] **Step 3: Handoff** (`sessione-2026-07-16/HANDOFF_ATTIVO.md`, `AVVIO_PROSSIMA_SESSIONE.md` coda) + sync `notebooklm-fonti/`.

---

## Self-Review

**Spec coverage:** FCO schema → Task 1 ✓; subraces source+attribuzione (zero invenzioni) → Task 2 ✓; features {name, level, replaces, alters, text} su 961 → Task 3 ✓; replaces di indice preservato (features è chiave aggiuntiva) ✓; sanitize + legal 0 ovunque ✓; gate/doc/handoff → Task 4 ✓.

**Placeholder scan:** nessun TBD; conteggi espressi come attese verificabili a runtime.

**Type consistency:** `parse_race_favored_class_options(html) -> list[{class, source, bonus}]`; `parse_race_subraces(html) -> list[{name, source, description, alternate_traits}]`; `parse_archetype_features(html) -> list[{name, level, replaces, alters, text}]` — identici in tool e test. `_iter_section`/`_section_text_nodes` riusati (Task razze); `sanitize_text` come sempre.
