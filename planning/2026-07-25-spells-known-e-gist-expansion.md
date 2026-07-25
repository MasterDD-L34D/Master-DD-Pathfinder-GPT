# Spell Lotto 1 — spells_known + espansione gist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chiudere i due gap spell decisi nel grilling 2026-07-25: (A) `spells_known` per i caster spontanei da pagine classe AoN in cache; (B) espansione spells.json 1035 → ~2800 dalla cache gist PathfinderSpellsJSON con triage PI. Tutto offline.

**Architecture:** Task 1 estende `parse_class` in `tools/import_reference.py` con il parse della tabella "Spells Known" (h2 + table) e rigenera classes.json. Task 2 crea `tools/expand_spells_gist.py` (nuovo dominio nel pattern parallelo-sicuro: non si registra in import_reference.DOMAINS) che appende le spell gist mancanti, sposta i nomi con identità PI in `pi_local_only/spells_local.json`, sanitizza la prosa e aggiorna manifest + report. Task 3 gate seriali + doc + handoff.

**Tech Stack:** Python 3, BeautifulSoup, pytest, venv `tooling/Master-DD-Taverna/.venv`. Nessuna nuova dipendenza.

**Spec (grilling 2026-07-25):** entry locali vincono sempre; gist solo per le mancanti; dedup per nome normalizzato (incluse forme invertite "X, Greater"); nomi con identità PI (possessivi divinità) → `spells_local.json`; prosa PI → sanitize word-boundary; provenienza in `notes`; fetch massivo AoN rinviato.

---

### Task 1: `spells_known` in parse_class

**Files:**
- Modify: `tooling/Master-DD-Taverna/tools/import_reference.py` (`parse_class`, riga ~285)
- Test: `tooling/Master-DD-Taverna/tests/test_import_reference.py`
- Modify (generato): `tooling/Master-DD-Taverna/data/reference/ogl/classes.json`

- [ ] **Step 1: Write the failing test**

In `tests/test_import_reference.py`, dopo `test_parse_class`, aggiungere:

```python
CLASS_KNOWN_HTML = """
<html><body>
<table><tr><td><b>Level</b></td><td><b>Base Attack Bonus</b></td><td><b>Fort Save</b></td><td><b>Ref Save</b></td><td><b>Will Save</b></td><td><b>Special</b></td><td><b>0</b></td><td><b>1st</b></td></tr>
<tr><td>1st</td><td>+0</td><td>+0</td><td>+2</td><td>+2</td><td>Cantrips</td><td>3</td><td>1</td></tr>
<tr><td>2nd</td><td>+1</td><td>+0</td><td>+3</td><td>+3</td><td>-</td><td>4</td><td>2</td></tr>
</table>
<h2>Spells Known</h2>
<table class="inner"><tr><td><b>Level</b></td><td><b>0</b></td><td><b>1st</b></td></tr>
<tr><td>1st</td><td>4</td><td>2</td></tr>
<tr><td>2nd</td><td>5</td><td>3</td></tr>
</table>
</body></html>
"""


def test_parse_class_spells_known():
    """La tabella 'Spells Known' (h2 + table) finisce in progression[].spells_known;
    NON deve inquinare spells_per_day (tabella distinta)."""
    entry = parse_class(CLASS_KNOWN_HTML, "Bard")
    prog = entry["mechanics"]["progression"]
    assert prog[0]["spells_known"] == {"0": "4", "1st": "2"}
    assert prog[1]["spells_known"] == {"0": "5", "1st": "3"}
    assert prog[0]["spells_per_day"] == {"0": "3", "1st": "1"}
    # entry preesistente senza tabella known: nessuna chiave
    no_known = parse_class(CLASS_HTML, "Barbarian")
    assert all("spells_known" not in row for row in no_known["mechanics"]["progression"])
    print("OK: parse_class spells_known")
```

Nota: `CLASS_HTML` è la fixture Barbarian già presente nel file di test.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tooling/Master-DD-Taverna && .venv/Scripts/python -m pytest tests/test_import_reference.py::test_parse_class_spells_known -v`
Expected: FAIL — `KeyError: 'spells_known'`.

- [ ] **Step 3: Implement `parse_spells_known` e hook in parse_class**

In `tools/import_reference.py`, subito PRIMA di `parse_class`, aggiungere:

```python
def parse_spells_known(soup):
    """Tabella 'Spells Known' (h2 + <table> immediatamente successiva):
    {livello_int: {cerchio_str: valore_str}}. {} se la classe non ce l'ha."""
    for h2 in soup.find_all("h2"):
        if clean(h2.get_text()).lower() != "spells known":
            continue
        table = h2.find_next("table")
        if not table:
            return {}
        trs = table.find_all("tr")
        if not trs:
            return {}
        headers = [clean(c.get_text()) for c in trs[0].find_all(["th", "td"])]
        known = {}
        for tr in trs[1:]:
            cells = [clean(c.get_text()) for c in tr.find_all(["th", "td"])]
            if len(cells) != len(headers) or not any(cells):
                continue
            row = dict(zip(headers, cells))
            lvl = _parse_level(row.get("Level", ""))
            if not lvl:
                continue
            circles = {k: v for k, v in row.items()
                       if k != "Level" and v and v not in ("-", "—")}
            if circles:
                known[lvl] = circles
        return known
    return {}
```

Poi in `parse_class`, subito dopo la riga `mech["progression"].append(entry)` (riga ~387) aggiungere il merge — attenzione: va DENTRO il loop ma il parse della tabella va fatto UNA volta. Forma concreta: subito prima di `desc = (f"{class_name}: ...` (riga ~388) inserire:

```python
    known = parse_spells_known(soup)
    for entry in mech["progression"]:
        if entry["level"] in known:
            entry["spells_known"] = known[entry["level"]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_import_reference.py -v`
Expected: tutto verde (nuovo test + nessuna regressione: la fixture CLASS_HTML non ha h2 Spells Known).

- [ ] **Step 5: Rigenerare classes.json e verificare copertura**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python tools/import_reference.py --domain classes
.venv/Scripts/python -c "
import json
c = json.load(open('data/reference/ogl/classes.json', encoding='utf-8'))
for e in c['entries']:
    sk = sum(1 for l in e['mechanics'].get('progression', []) if l.get('spells_known'))
    if sk:
        print(f\"{e['name']:12s} spells_known su {sk}/20 livelli\")
"
```

Expected: Bard, Sorcerer, Bloodrager, Inquisitor, Medium, Hunter (e solo caster spontanei) con `spells_known` su ~17-20 livelli. Se una di queste 6 manca, investigare la pagina in cache prima di procedere. (`--domain classes` = nome esatto del comando: verificare con `--help` se diverso; le pagine sono tutte in cache, nessun fetch di rete.)

- [ ] **Step 6: Commit**

```bash
cd tooling/Master-DD-Taverna
git add tools/import_reference.py tests/test_import_reference.py data/reference/ogl/classes.json planning/2026-07-25-spells-known-e-gist-expansion.md
git commit -m "feat(reference): parse spells known tables for spontaneous casters"
```

---

### Task 2: `tools/expand_spells_gist.py` — espansione + triage PI

**Files:**
- Create: `tooling/Master-DD-Taverna/tools/expand_spells_gist.py`
- Create: `tooling/Master-DD-Taverna/tests/test_expand_spells_gist.py`
- Modify (generati): `data/reference/ogl/spells.json`, `data/reference/pi_local_only/spells_local.json` (NON committato), `data/reference/manifest.json`
- Create (committato): `reports/expand_spells_gist.md`

- [ ] **Step 1: Write the failing test**

Creare `tests/test_expand_spells_gist.py`:

```python
"""Test per tools/expand_spells_gist.py — espansione spells da cache gist."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.expand_spells_gist import (gist_to_entry, is_pi_name,
                                      new_gist_records)

GIST_SAMPLE = {
    "name": "Ablative Sphere",
    "source": "Ultimate Magic",
    "school": "abjuration",
    "spell_level": "sorcerer/wizard 3",
    "casting_time": "1 standard action",
    "components": "V, S, M (a crystalline sphere worth 10 gp)",
    "range": "personal",
    "duration": "1 minute per level (D)",
    "saving_throw": "",
    "targets": "you",
    "description": "An immobile, crystalline globe surrounds you.",
}


def test_gist_to_entry_builds_catalog_shape():
    e = gist_to_entry(GIST_SAMPLE)
    assert e["name"] == "Ablative Sphere"
    assert e["source"] == "Ultimate Magic"
    assert e["source_id"] == "pathfinder_srd:ablative_sphere"
    assert e["prerequisites"] == []
    assert "school:abjuration" in e["tags"]
    assert "slot:3" in e["tags"]
    assert "class:sorcerer" in e["tags"] and "class:wizard" in e["tags"]
    assert e["reference_urls"] == [
        "https://aonprd.com/SpellDisplay.aspx?ItemName=Ablative%20Sphere"]
    mech = e["mechanics"]
    assert mech["school"] == "abjuration"
    assert mech["spell_level"] == {"sorcerer/wizard": 3}
    assert mech["targets"] == "you"
    assert "saving_throw" not in mech  # campo gist vuoto -> omesso
    assert "gist" in e["notes"].lower()


def test_new_gist_records_skips_existing_and_inverted():
    local_names = ["Acid Arrow", "Greater Invisibility"]
    gist = [
        {"name": "Acid Arrow"},                     # gia' presente
        {"name": "Invisibility, Greater"},          # forma invertita di una locale
        {"name": "Ablative Sphere"},                # nuova
    ]
    nuovi = new_gist_records(local_names, gist)
    assert [g["name"] for g in nuovi] == ["Ablative Sphere"]


def test_is_pi_name_flags_deity_possessive():
    assert is_pi_name("Abadar's Truthtelling")
    assert is_pi_name("Iomedae's Sword")
    assert not is_pi_name("Ablative Sphere")
    assert not is_pi_name("Fireball")


def test_description_sanitized_word_boundary():
    g = dict(GIST_SAMPLE)
    g["description"] = "This spell is common on Golarion. The globe protects you."
    e = gist_to_entry(g)
    assert "Golarion" not in e["description"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_expand_spells_gist.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.expand_spells_gist'`.

- [ ] **Step 3: Implement `tools/expand_spells_gist.py`**

Creare il file:

```python
#!/usr/bin/env python3
"""Espande spells.json con le spell della cache gist PathfinderSpellsJSON
assenti dal catalogo (expansion offline, Lotto 1 spell 2026-07-25).

Policy (spec grilling 2026-07-25):
- le entry locali esistenti VINCONO sempre: il gist aggiunge solo le mancanti;
- dedup per nome esatto/normalizzato e forma invertita "X, Greater" (stessa
  logica di enrich_spells._gist_entry);
- nomi con identita' PI (word-boundary su PI_WORDS di legal_filter, es.
  possessivi di divinita') -> pi_local_only/spells_local.json (verbatim);
- prosa con PI -> sanitize word-boundary (sanitize_reference_pi) solo su
  description; gate finale legal_filter = 0;
- provenienza dichiarata in notes + references; manifest aggiornato
  (files.spells + catalogs spells/spells_local).

Default: dry-run (report a video). --write applica e scrive file + report.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.enrich_reference import normalize_name
from tools.enrich_spells import CACHE_DIR, load_gist_cache, parse_spell_level
from tools.legal_filter import PI_WORDS
from tools.reference_lib import OGL_DIR, slug, source_id
from tools.sanitize_reference_pi import sanitize_text

import re

ROOT = Path(__file__).resolve().parents[1]
SPELLS_PATH = OGL_DIR / "spells.json"
LOCAL_PATH = ROOT / "data" / "reference" / "pi_local_only" / "spells_local.json"
MANIFEST_PATH = ROOT / "data" / "reference" / "manifest.json"
REPORT_PATH = ROOT / "reports" / "expand_spells_gist.md"

_PI_NAME_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(PI_WORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE)

_INVERTIBLE_PREFIXES = ("Greater", "Lesser", "Mass")


def is_pi_name(name: str) -> bool:
    """True se il nome contiene un termine PI (word-boundary)."""
    return bool(_PI_NAME_RE.search(name))


def _variants(name: str) -> list[str]:
    """Nome + forma invertita per prefissi Greater/Lesser/Mass."""
    out = [name]
    for prefix in _INVERTIBLE_PREFIXES:
        if name.startswith(prefix + " "):
            out.append(f"{name[len(prefix) + 1:]}, {prefix}")
            break
    return out


def new_gist_records(local_names: list[str], gist_records: list[dict]) -> list[dict]:
    """Record gist il cui nome NON copre nessuna entry locale (esatto,
    normalizzato, invertito in entrambe le direzioni)."""
    local_exact = set(local_names)
    local_norm = {normalize_name(n) for n in local_names}
    nuovi = []
    for g in gist_records:
        name = g.get("name", "")
        if not name:
            continue
        cands = set()
        for v in _variants(name):
            cands.add(v)
            cands.add(normalize_name(v))
        if cands & local_exact or cands & local_norm:
            continue
        nuovi.append(g)
    return nuovi


def _tags_for(name: str, mech: dict) -> list[str]:
    tags = ["spell", slug(name).replace("_", "-")]
    if mech.get("school"):
        tags.append(f"school:{mech['school']}")
    levels = mech.get("spell_level") or {}
    if levels:
        tags.append(f"slot:{min(levels.values())}")
        for cls_key in levels:
            for cls in cls_key.split("/"):
                tags.append(f"class:{cls.strip()}")
    return tags


def gist_to_entry(g: dict) -> dict:
    """Record gist -> entry catalogo spells (description sanitizzata)."""
    mech = {}
    for key in ("school", "casting_time", "components", "range",
                "duration", "saving_throw", "targets"):
        value = g.get(key)
        if isinstance(value, str) and value.strip():
            mech[key] = value.strip()
    levels = parse_spell_level(g.get("spell_level") or "")
    if levels:
        mech["spell_level"] = levels
    return {
        "name": g["name"],
        "source": g.get("source") or "Pathfinder SRD",
        "source_id": source_id("pathfinder_srd", g["name"]),
        "prerequisites": [],
        "tags": _tags_for(g["name"], mech),
        "references": [f"PathfinderSpellsJSON gist: {g['name']}"],
        "reference_urls": [
            "https://aonprd.com/SpellDisplay.aspx?ItemName="
            + g["name"].replace(" ", "%20").replace("'", "%27")],
        "description": sanitize_text(g.get("description") or ""),
        "mechanics": mech,
        "notes": ("Aggiunta da cache gist PathfinderSpellsJSON (expansion "
                  "2026-07-25): assente dal catalogo storico."),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="scrive spells.json/spells_local.json/manifest + report")
    args = ap.parse_args(argv)

    catalog = json.loads(SPELLS_PATH.read_text(encoding="utf-8"))
    entries = catalog["entries"]
    gist = load_gist_cache(CACHE_DIR)
    if not gist:
        sys.exit("ERRORE: cache gist assente")
    records = list(gist.exact.values())
    nuovi = new_gist_records([e["name"] for e in entries], records)

    local_entries, ogl_entries = [], []
    for g in nuovi:
        entry = gist_to_entry(g)
        (local_entries if is_pi_name(entry["name"]) else ogl_entries).append(entry)

    print(f"gist: {len(records)} record; nuovi: {len(nuovi)} "
          f"(OGL {len(ogl_entries)}, PI->local {len(local_entries)})")
    if not args.write:
        print("Dry-run: nessuna modifica (usa --write)")
        for e in local_entries[:20]:
            print(f"  PI local: {e['name']}")
        return 0

    entries.extend(ogl_entries)
    catalog["entries"] = entries
    SPELLS_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    local_catalog = {
        "_license": "OGL-1.0a",
        "_source": ("PathfinderSpellsJSON gist / Archives of Nethys "
                    "(local only, not redistributed)"),
        "entries": local_entries,
    }
    LOCAL_PATH.write_text(json.dumps(local_catalog, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    manifest["files"]["spells"]["entries"] = len(entries)
    for c in manifest["catalogs"]:
        if c["kind"] == "spells":
            c["entries"] = len(entries)
            c["last_verified"] = today
    manifest["catalogs"] = [c for c in manifest["catalogs"] if c["kind"] != "spells_local"]
    manifest["catalogs"].append({
        "file": "pi_local_only/spells_local.json",
        "kind": "spells_local",
        "source": "PathfinderSpellsJSON gist / Archives of Nethys (aonprd.com)",
        "license": "OGL-1.0a",
        "is_ogc": False,
        "is_pi": False,
        "cup_allowed": False,
        "local_only": True,
        "entries": len(local_entries),
        "notes": ("Spell con Product Identity nel nome (possessivi di divinita' "
                  "e simili), separate dal catalogo OGL con la policy 2026-07-25 "
                  "(reports/expand_spells_gist.md). NON redistribuire. Generato da "
                  "tools/expand_spells_gist.py; indicizza con index_rag.py --include-local."),
        "last_verified": today,
    })
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    lines = [
        "# Expansion spells da cache gist (2026-07-25)", "",
        f"- Record gist: {len(records)}",
        f"- Nuove (non in catalogo): {len(nuovi)}",
        f"- Aggiunte a spells.json (OGL): {len(ogl_entries)} (totale {len(entries)})",
        f"- Spostate in spells_local.json (nome PI): {len(local_entries)}",
        "", "## Nomi PI spostati in locale", "",
    ]
    lines += [f"- {e['name']}" for e in local_entries]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scritto: {SPELLS_PATH} ({len(entries)} entry)")
    print(f"Scritto: {LOCAL_PATH} ({len(local_entries)} entry, NON committare)")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Nota implementativa: se `sanitize_text` ha una firma diversa (es. richiede il set di regole), adattare la chiamata in `gist_to_entry` copiando l'uso fatto in `apply_pi_feats_policy.py` (regole description-only). Se `gist.exact` espone i record con chiavi diverse, usare `load_gist_cache` com'è (già testato in enrich_spells).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_expand_spells_gist.py -v`
Expected: 4 passed. Se `test_description_sanitized_word_boundary` fallisce perché "Golarion" usa un replacement che lo mantiene parzialmente, verificare il replacement reale in `sanitize_reference_pi.REPLACEMENTS` e correggere l'assert di conseguenza (il gate vero è legal_filter = 0).

- [ ] **Step 5: Dry-run sui dati reali**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python tools/expand_spells_gist.py
```

Expected: `gist: 2827 record; nuovi: ~1809 (OGL ~17xx, PI->local ~xx)`. Ispezionare la lista dei nomi PI: devono essere possessivi di divinità/nomi propri Golarion, nessun falso positivo evidente (se ci sono falsi positivi, fermarsi e valutare eccezioni come da playbook).

- [ ] **Step 6: Apply + gate legal**

```bash
.venv/Scripts/python tools/expand_spells_gist.py --write
.venv/Scripts/python tools/legal_filter.py
```

Expected: legal_filter **0 violazioni**. Se >0: i residui indicano parole PI non coperte da sanitize → valutare supplemento REPLACEMENTS (come fatto per traits) prima di procedere. Verificare anche che `git status` NON elenchi `data/reference/pi_local_only/spells_local.json` (gitignored).

- [ ] **Step 7: Commit**

```bash
cd tooling/Master-DD-Taverna
git add tools/expand_spells_gist.py tests/test_expand_spells_gist.py \
  data/reference/ogl/spells.json data/reference/manifest.json reports/expand_spells_gist.md
git commit -m "feat(reference): expand spells catalog from gist cache with pi triage"
```

---

### Task 3: Gate seriali, documentazione, handoff

**Files:**
- Modify: `tooling/Master-DD-Taverna/docs/IMPORT_PLAYBOOK.md` (nota §6.3)

- [ ] **Step 1: Suite completa + schemi**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -m pytest tests/ -q
.venv/Scripts/python tools/validate_schemas.py
.venv/Scripts/python tools/legal_filter.py
```

Expected: pytest verde (340 + nuovi, 1 skipped); schemi OK (manifest allineato ai count reali); legal 0. Nota: `test_manifest_counts` confronta manifest↔disco: se fallisce, il manifest non è stato aggiornato correttamente nel Task 2.

- [ ] **Step 2: Reindice RAG**

```bash
.venv/Scripts/python tools/index_rag.py --include-local
```

Expected: ri-encode dei chunk spells cambiati/aggiunti (~1800 nuovi chunk) + spells_local (kind nuovo in catalogs[]: l'indexer lo raccoglie automaticamente con --include-local). Chunk totali attesi: ~6709 + ~1800.

- [ ] **Step 3: Spot check retrieval**

```bash
.venv/Scripts/python -c "
import json
s = json.load(open('data/reference/ogl/spells.json', encoding='utf-8'))
names = {e['name'] for e in s['entries']}
assert 'Ablative Sphere' in names, 'nuova spell assente'
assert len(names) == len(s['entries']), 'duplicati per nome!'
print('spells.json:', len(s['entries']), 'entry, duplicati: 0')
"
```

Expected: nessuna assertion. (Il check duplicati è essenziale: collisioni di forma invertita passate dal filtro creerebbero doppioni.)

- [ ] **Step 4: `python launch.py test` dalla root**

Expected: `TUTTE LE VERIFICHE OK`.

- [ ] **Step 5: Nota in `docs/IMPORT_PLAYBOOK.md`**

Aggiungere dopo la §6.2:

```markdown
## 6.3 Spell lotto 1 (2026-07-25)

`classes.json`: `mechanics.progression[].spells_known` per i caster spontanei (parse tabella "Spells Known" delle pagine classe in cache; rigenerare con `import_reference.py --domain classes`). `spells.json` espanso da cache gist PathfinderSpellsJSON (offline, entry locali vincenti, dedup per nome normalizzato+invertito): `tools/expand_spells_gist.py` (dry-run default, `--write` applica). Nomi con identità PI → `pi_local_only/spells_local.json` (non committato, kind `spells_local` nel manifest); prosa sanitizzata word-boundary. Report: `reports/expand_spells_gist.md`. Fetch massivo AoN per spell oltre il gist = lotto futuro, solo se emergono lacune concrete. Segue il lotto 2 (archetipi, piano a parte).
```

- [ ] **Step 6: Commit finale + push**

```bash
cd tooling/Master-DD-Taverna
git add docs/IMPORT_PLAYBOOK.md
git commit -m "docs(reference): document spells known and gist expansion"
git push origin main
```

- [ ] **Step 7: Handoff**

Aggiornare `sessione-2026-07-16/HANDOFF_ATTIVO.md` (tabella stato + voce completati + follow-up: lotto 2 archetipi con piano dedicato) e sincronizzare `notebooklm-fonti/HANDOFF_ATTIVO.md` con `cp`.

---

## Self-Review

**Spec coverage:**
- A. spells_known caster spontanei → Task 1 ✓ (parse dove la tabella esiste; nessuna chiave altrove)
- B. espansione da gist, entry locali vincenti, dedup normalizzato+invertito → Task 2 (`new_gist_records`) ✓
- Nomi PI → local / prosa → sanitize / legal_filter 0 → Task 2 Steps 3, 5, 6 ✓
- Provenienza in notes → `gist_to_entry` ✓
- Manifest/counts, validate_schemas, reindex, launch.py, commit/push, handoff → Task 2 Step 3 (manifest) + Task 3 ✓
- Fetch massivo rinviato → nota §6.3 ✓

**Placeholder scan:** il piano contiene due "nota implementativa" esplicite (firma `sanitize_text`, replacement "Golarion", nome comando `--domain classes`): sono punti di verifica con istruzione concreta di adattamento, non lavoro rimandato. Nessun TBD.

**Type consistency:** `gist_to_entry(dict) -> dict`, `new_gist_records(list[str], list[dict]) -> list[dict]`, `is_pi_name(str) -> bool`, `parse_spells_known(soup) -> dict[int, dict]` — identici in tool e test. `load_gist_cache`/`CACHE_DIR`/`parse_spell_level` riusati da `enrich_spells` (import verificato: esistono). `normalize_name` da `enrich_reference`, `sanitize_text` da `sanitize_reference_pi`, `PI_WORDS` da `legal_filter`, `source_id`/`slug`/`OGL_DIR` da `reference_lib` — tutti esistenti.
