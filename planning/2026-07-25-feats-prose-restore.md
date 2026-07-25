# Ripristino prosa corrotta feats (75) + fix references Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chiudere il debito documentato nell'appendice di `reports/pi_feats_triage.md`: (1) ripristinare da fonte AoN la prosa corrotta dalla sanitize storica naive nelle 75 entry feats elencate ("elemental"→"ea bardental", "kundalini"→"kundaa druid", ...); (2) correggere i references "Archives of a deity of magic" → "Pathfinder PRD" in tutti i cataloghi OGL (ordine regole sanitize già fixato nel tool il 2026-07-19, i dati mai bonificati: 2755 feats + 970 spells + altri).

**Architecture:** Task 1 crea `tools/restore_feat_prose.py`: lista dei 75 nomi parsata dal report committato (fonte di verità), fetch seriale FeatDisplay (2s), parser della pagina (flavor + benefit = convenzione catalogo verificata sulle entry D), sanitize word-boundary del testo ripristinato, applicazione con report. Task 2 crea `tools/fix_reference_strings.py` per il replace deterministico dei references su tutti i cataloghi OGL. Task 3 gate seriali + doc + handoff.

**Tech Stack:** Python 3, BeautifulSoup, pytest, `tools/reference_fetch`, venv esistente. Nessuna nuova dipendenza.

**Vincoli di convenzione (verificati su `Elemental Channel` ripristinata nel lotto triage):** `description` = flavor + `"\n\n"` + testo Benefit (senza etichette, senza Special/Normal); `prerequisites` = lista da `split_prereq_string`; `references` = `["Pathfinder PRD: <name>"]`; `source`/`tags`/`source_id`/`reference_urls` invariati; `updated_at` = data restore.

---

### Task 1: `tools/restore_feat_prose.py` — ripristino 75 entry da FeatDisplay

**Files:**
- Create: `tooling/Master-DD-Taverna/tools/restore_feat_prose.py`
- Create: `tooling/Master-DD-Taverna/tests/test_restore_feat_prose.py`
- Modify (generato): `data/reference/ogl/feats.json`
- Create (committato): `reports/restore_feat_prose.md`

- [ ] **Step 1: Write the failing test**

Creare `tests/test_restore_feat_prose.py`:

```python
"""Test per tools/restore_feat_prose.py — ripristino prosa da FeatDisplay AoN."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.restore_feat_prose import (appendix_names, apply_restore,
                                      parse_feat_page)

# Markup ricalcato su FeatDisplay.aspx reale (cache Elemental Channel).
FEAT_HTML = """
<html><body>
<span id="MainContent_DataListTypes_LabelName_0"><h1 class="title"><img src="images\\PathfinderSocietySymbol.gif" title="PFS Legal"/> Elemental Channel</h1><b>Source</b> <a href="http://paizo.com/x" class="external-link"><i>PRPG Core Rulebook pg. 122</i></a><br />Choose one elemental subtype, such as air, earth, fire, or water.<br /><br /><b>Prerequisites</b>: Channel energy class feature.<br /><br /><b>Benefit</b>: Instead of its normal effect, you can choose to heal or harm outsiders of your chosen elemental subtype. The amount of damage is otherwise unchanged.<br /><br /><b>Special</b>: You can gain this feat multiple times.</span>
</body></html>
"""


def test_parse_feat_page():
    p = parse_feat_page(FEAT_HTML)
    assert p["name"] == "Elemental Channel"
    assert p["source"] == "PRPG Core Rulebook"
    assert p["flavor"] == "Choose one elemental subtype, such as air, earth, fire, or water."
    assert p["prerequisites"] == ["Channel energy class feature"]
    assert p["benefit"].startswith("Instead of its normal effect")
    assert "multiple times" not in p["benefit"]  # Special escluso


def test_apply_restore_entry_shape():
    entry = {"name": "Elemental Channel",
             "source": "PRPG Core Rulebook",
             "prerequisites": ["old corrupted"],
             "references": ["Archives of a deity of magic: Elemental Channel"],
             "description": "Choose one ea bardental subtype...",
             "tags": ["PRPG Core Rulebook"],
             "source_id": "prpg_core_rulebook:elemental_channel"}
    p = parse_feat_page(FEAT_HTML)
    out = apply_restore(entry, p)
    assert out["description"] == (
        "Choose one elemental subtype, such as air, earth, fire, or water.\n\n"
        + p["benefit"])
    assert out["prerequisites"] == ["Channel energy class feature"]
    assert out["references"] == ["Pathfinder PRD: Elemental Channel"]
    assert out["source"] == "PRPG Core Rulebook"  # invariato
    assert out["source_id"] == "prpg_core_rulebook:elemental_channel"  # invariato
    assert out["updated_at"]


def test_appendix_names_from_committed_report():
    names = appendix_names()
    assert len(names) == 75
    assert "Djinni Spin" in names and "Elemental Channel" not in names
```

Nota: `Elemental Channel` NON è nella lista dei 75 (era categoria D, già ripristinata); `Djinni Spin` sì.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tooling/Master-DD-Taverna && .venv/Scripts/python -m pytest tests/test_restore_feat_prose.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.restore_feat_prose'`.

- [ ] **Step 3: Implement `tools/restore_feat_prose.py`**

Creare il file:

```python
#!/usr/bin/env python3
"""Ripristina la prosa corrotta dalla sanitize storica naive nelle 75 entry
feats dell'appendice di reports/pi_feats_triage.md (lotto 2026-07-25).

Fonte: pagine FeatDisplay AoN (fetch seriale 2s via reference_fetch, cache).
Convenzione catalogo (verificata sulle D del triage): description =
flavor + "\\n\\n" + Benefit (no etichette/Special); prerequisites da
split_prereq_string; references = ["Pathfinder PRD: <name>"]; source/tags/
source_id/reference_urls invariati; updated_at = oggi. Il testo ripristinato
e' sanitizzato (description=True) per riapplicare il masking PI sanctioned.

Default: dry-run. --write applica e scrive feats.json + report.
--offline: solo cache (fallisce su miss).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.reference_fetch import cache_path, fetch
from tools.reference_lib import OGL_DIR, clean, split_prereq_string
from tools.sanitize_reference_pi import sanitize_text

ROOT = Path(__file__).resolve().parents[1]
FEATS_PATH = OGL_DIR / "feats.json"
REPORT_SRC = ROOT / "reports" / "pi_feats_triage.md"
REPORT_PATH = ROOT / "reports" / "restore_feat_prose.md"
BASE = "https://aonprd.com/FeatDisplay.aspx?ItemName="

_LABEL_RE = re.compile(r"^(Prerequisites?|Benefit|Normal|Special|Note)s?\s*:\s*", re.I)


def appendix_names() -> list[str]:
    """I 75 nomi dall'appendice del report triage (fonte di verita' committata)."""
    text = REPORT_SRC.read_text(encoding="utf-8")
    m = re.search(r"<details><summary>Elenco entry \(nomi\)</summary>\s*(.*?)\s*</details>",
                  text, re.S)
    if not m:
        sys.exit("ERRORE: appendice non trovata in " + str(REPORT_SRC))
    return [n.strip() for n in m.group(1).split(",") if n.strip()]


def parse_feat_page(html: str) -> dict:
    """Pagina FeatDisplay -> {name, source, flavor, prerequisites, benefit}."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1", class_="title")
    if not h1:
        raise ValueError("h1.title non trovato (pagina non FeatDisplay?)")
    name = clean(h1.get_text())
    span = h1.parent
    source = ""
    src_b = span.find("b", string=lambda s: s and s.strip() == "Source")
    if src_b and src_b.find_next("i"):
        source = clean(src_b.find_next("i").get_text())
        source = re.sub(r"\s*pg\.\s*\d+.*$", "", source).strip()
    # Segmenti di testo separati da <br>, con le etichette <b> come delimitatori.
    segments = []
    for piece in span.stripped_strings:
        segments.append(clean(piece))
    flavor_parts, benefit_parts, prereq_text = [], [], ""
    mode = "flavor"
    skip_labels = {"Source"}
    for seg in segments:
        if seg == name or seg in skip_labels or seg.startswith("Source "):
            continue
        m = _LABEL_RE.match(seg)
        label = m.group(1).lower() if m else None
        if label and label.startswith("prerequisite"):
            mode = "prereq"
            seg = _LABEL_RE.sub("", seg)
        elif label == "benefit":
            mode = "benefit"
            seg = _LABEL_RE.sub("", seg)
        elif label in ("normal", "special", "note"):
            mode = "skip"
            continue
        if not seg or seg == name or re.match(r"^pg\.\s*\d+", seg):
            continue
        if mode == "flavor":
            if seg != source and "pg." not in seg:
                flavor_parts.append(seg)
        elif mode == "prereq":
            prereq_text += (" " if prereq_text else "") + seg
            mode = "flavor" if False else "prereq_done"
        elif mode == "benefit":
            benefit_parts.append(seg)
    return {"name": name, "source": source,
            "flavor": clean(" ".join(flavor_parts)),
            "prerequisites": split_prereq_string(prereq_text) if prereq_text else [],
            "benefit": clean(" ".join(benefit_parts))}


def apply_restore(entry: dict, page: dict) -> dict:
    """Aggiorna l'entry con i dati della pagina (convenzione catalogo)."""
    out = dict(entry)
    desc = page["flavor"] + "\n\n" + page["benefit"] if page["flavor"] else page["benefit"]
    out["description"] = sanitize_text(desc, description=True)
    out["prerequisites"] = page["prerequisites"]
    out["references"] = [f"Pathfinder PRD: {entry['name']}"]
    out["updated_at"] = date.today().isoformat() + "T00:00:00Z"
    return out


def _fetch_page(name: str, offline: bool) -> str:
    url = BASE + name.replace(" ", "%20").replace("'", "%27")
    if offline:
        path = cache_path(url)
        if not path.exists():
            raise FileNotFoundError(url)
        return path.read_text(encoding="utf-8", errors="replace")
    return fetch(url, delay=2.0, cache=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args(argv)

    names = appendix_names()
    catalog = json.loads(FEATS_PATH.read_text(encoding="utf-8"))
    by_name = {e["name"]: e for e in catalog["entries"]}
    missing = [n for n in names if n not in by_name]
    if missing:
        sys.exit(f"ERRORE: nomi appendice assenti dal catalogo: {missing}")

    restored, failures, src_mismatch = [], [], []
    for name in names:
        try:
            page = parse_feat_page(_fetch_page(name, args.offline))
        except Exception as exc:
            failures.append(f"- **{name}**: {exc}")
            continue
        entry = by_name[name]
        if page["source"] and entry.get("source") and page["source"] != entry["source"]:
            src_mismatch.append(f"- **{name}**: catalogo `{entry['source']}` vs pagina `{page['source']}`")
        if args.write:
            entry.update(apply_restore(entry, page))
        restored.append(name)

    print(f"nomi: {len(names)}; ripristinati: {len(restored)}; falliti: {len(failures)}")
    for line in failures:
        print(line)
    for line in src_mismatch:
        print(line)
    if not args.write:
        print("Dry-run: nessuna modifica (usa --write)")
        return 0

    FEATS_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    lines = ["# Ripristino prosa feats (2026-07-25)", "",
             f"- Entry in appendice: {len(names)}",
             f"- Ripristinate: {len(restored)}",
             f"- Fallite (404/parse): {len(failures)}", "",
             "## Fallite", ""] + (failures or ["(nessuna)"]) + [
             "", "## Mismatch source catalogo/pagina (non bloccanti)", ""] + (src_mismatch or ["(nessuno)"])
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scritto: {FEATS_PATH}; report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Nota implementativa: `split_prereq_string` è in `tools/reference_lib.py` (riusato dall'import feats). Se la gestione della modalità prereq risulta fragile su pagine con etichette multiple, verificare su 3 pagine reali in cache prima del run completo (Elemental Channel e Tattoo Attunement sono già in cache per confronto).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_restore_feat_prose.py -v`
Expected: 3 passed.

- [ ] **Step 5: Warm-cache seriale (75 pagine)**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -c "
import sys; sys.path.insert(0, '.')
from tools.reference_fetch import fetch
from tools.restore_feat_prose import appendix_names, BASE
ok = fail = 0
for n in appendix_names():
    url = BASE + n.replace(' ', '%20').replace(chr(39), '%27')
    try:
        fetch(url, delay=2.0, cache=True); ok += 1
    except Exception as exc:
        fail += 1; print('FALLITO', n, exc)
print(f'cache: {ok} ok, {fail} falliti')
"
```

Expected: ~75 ok in ~3 minuti. Nomi con 404 (es. grafie non AoN come "Aspiringnoble") restano nei falliti: vanno nel report e la entry resta com'è (nessuna scrittura per loro).

- [ ] **Step 6: Apply + verifiche**

```bash
.venv/Scripts/python tools/restore_feat_prose.py --write
.venv/Scripts/python -c "
import json, re
f = json.load(open('data/reference/ogl/feats.json', encoding='utf-8'))
art = re.compile(r'[a-z](ea bard|a bard|a druid|a paladin|a wizard|a rogue|a cleric|a ranger|a monk|a barbarian)|(ea bard|a bard|a druid|a paladin|a wizard|a rogue|a cleric|a ranger|a monk|a barbarian)[a-z]', re.I)
bad = [(e['name']) for e in f['entries'] if art.search(e.get('description',''))]
print('description con artifact residui:', len(bad), bad[:10])
"
.venv/Scripts/python tools/legal_filter.py
```

Expected: 0 artifact residui (esclusi i falliti documentati nel report); legal_filter **0 violazioni** (se >0: il testo AoN grezzo contiene PI non coperto → supplemento DESCRIPTION_ONLY + revert + re-apply, come nei lotti precedenti). **Spot check manuale di 3 entry** (es. Djinni Spin, Scorching Weapons, Chakra Adept): description coerente con la pagina, nessun "ea bardental"/"kundaa druid".

- [ ] **Step 7: Commit**

```bash
cd tooling/Master-DD-Taverna
git add tools/restore_feat_prose.py tests/test_restore_feat_prose.py \
  data/reference/ogl/feats.json reports/restore_feat_prose.md \
  planning/2026-07-25-feats-prose-restore.md
git commit -m "fix(reference): restore corrupted feat prose from aon source"
```

---

### Task 2: `tools/fix_reference_strings.py` — references "Archives of a deity of magic"

**Files:**
- Create: `tooling/Master-DD-Taverna/tools/fix_reference_strings.py`
- Create: `tooling/Master-DD-Taverna/tests/test_fix_reference_strings.py`
- Modify (generati): `data/reference/ogl/*.json` (tutti i cataloghi con references corrotte)

- [ ] **Step 1: Write the failing test**

Creare `tests/test_fix_reference_strings.py`:

```python
"""Test per tools/fix_reference_strings.py — bonifica references sanitize-order."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.fix_reference_strings import fix_entry


def test_fix_entry_replaces_corrupted_reference():
    e = {"name": "X", "references": ["Archives of a deity of magic: X",
                                     "d20PFSRD: X"]}
    out, n = fix_entry(e)
    assert out["references"] == ["Pathfinder PRD: X", "d20PFSRD: X"]
    assert n == 1


def test_fix_entry_idempotent_and_untouched():
    e = {"name": "X", "references": ["Pathfinder PRD: X"]}
    out, n = fix_entry(e)
    assert out["references"] == ["Pathfinder PRD: X"]
    assert n == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_fix_reference_strings.py -v`
Expected: FAIL — ModuleNotFoundError.

- [ ] **Step 3: Implement `tools/fix_reference_strings.py`**

Creare il file:

```python
#!/usr/bin/env python3
"""Sostituisce 'Archives of a deity of magic' -> 'Pathfinder PRD' nei
references di tutti i cataloghi OGL (artifact dell'ordine regole sanitize
pre-2026-07-19: 'Nethys' -> 'a deity of magic' scattava prima della regola
frase 'Archives of Nethys' -> 'Pathfinder PRD'; tool gia' fixato, dati mai
bonificati — appendice di reports/pi_feats_triage.md).

Default: dry-run (conteggi). --write applica.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.reference_lib import OGL_DIR

OLD = "Archives of a deity of magic"
NEW = "Pathfinder PRD"


def fix_entry(entry: dict) -> tuple[dict, int]:
    """Entry con references bonificati + n. sostituzioni."""
    refs = entry.get("references")
    if not isinstance(refs, list):
        return entry, 0
    n = sum(1 for r in refs if isinstance(r, str) and OLD in r)
    if not n:
        return entry, 0
    out = dict(entry)
    out["references"] = [r.replace(OLD, NEW) if isinstance(r, str) else r for r in refs]
    return out, n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    total_entries = total_subs = 0
    for path in sorted(OGL_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("entries")
        if not isinstance(entries, list):
            continue
        subs = 0
        new_entries = []
        for e in entries:
            out, n = fix_entry(e)
            new_entries.append(out)
            subs += n
        if not subs:
            continue
        total_entries += sum(1 for e in entries if "OLD_MARKER" != "" and any(
            OLD in r for r in e.get("references", []) if isinstance(r, str)))
        total_subs += subs
        print(f"{path.name}: {subs} references bonificati")
        if args.write:
            data["entries"] = new_entries
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"totale: {total_subs} sostituzioni")
    if not args.write:
        print("Dry-run: nessuna modifica (usa --write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test + apply**

```bash
.venv/Scripts/python -m pytest tests/test_fix_reference_strings.py -v   # 2 passed
.venv/Scripts/python tools/fix_reference_strings.py                     # dry-run
.venv/Scripts/python tools/fix_reference_strings.py --write
.venv/Scripts/python -c "
import json, glob
n = sum(json.dumps(json.load(open(p, encoding='utf-8'))).count('Archives of a deity of magic') for p in glob.glob('data/reference/ogl/*.json'))
print('residui:', n)
"
```

Expected: dry-run ~3725+ sostituzioni (2755 feats + 970 spells + eventuali altri); residui 0.

- [ ] **Step 5: Commit**

```bash
cd tooling/Master-DD-Taverna
git add tools/fix_reference_strings.py tests/test_fix_reference_strings.py data/reference/ogl/
git commit -m "fix(reference): clean sanitize-order artifact in catalog references"
```

---

### Task 3: Gate seriali, documentazione, handoff

- [ ] **Step 1: Suite completa + schemi + legal**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -m pytest tests/ -q
.venv/Scripts/python tools/validate_schemas.py
.venv/Scripts/python tools/legal_filter.py
```

Expected: verde (348+nuovi, 1 skipped); schemi OK; legal 0.

- [ ] **Step 2: Reindice RAG + launch.py test**

```bash
.venv/Scripts/python tools/index_rag.py --include-local
cd ../.. && python launch.py test
```

Expected: ri-encode chunk feats/spells cambiati; `TUTTE LE VERIFICHE OK`.

- [ ] **Step 3: Nota in `docs/IMPORT_PLAYBOOK.md`**

Aggiungere dopo la §6.4:

```markdown
## 6.5 Ripristino prosa feats + bonifica references (2026-07-25)

Chiuso il debito dell'appendice di `reports/pi_feats_triage.md`: 75 entry feats con prosa corrotta dalla sanitize storica naive ripristinate da FeatDisplay AoN (`tools/restore_feat_prose.py`, dry-run/`--write`/`--offline`; lista nomi parsata dal report committato; description = flavor + Benefit, sanitize sanctioned riapplicata; report `reports/restore_feat_prose.md`). References "Archives of a deity of magic" → "Pathfinder PRD" bonificati su tutti i cataloghi OGL (`tools/fix_reference_strings.py`).
```

- [ ] **Step 4: Commit finale + push + handoff**

```bash
cd tooling/Master-DD-Taverna
git add docs/IMPORT_PLAYBOOK.md
git commit -m "docs(reference): document feat prose restore and references cleanup"
git push origin main
```

Aggiornare `sessione-2026-07-16/HANDOFF_ATTIVO.md` (lotto 4+5 chiuso: segnalazione pathmaster-dd `875c946` + WORKFLOW §4 `6e90c09`; ripristino prosa) e sincronizzare `notebooklm-fonti/`. Aggiornare anche `AVVIO_PROSSIMA_SESSIONE.md` §5.0 (rimuovere i punti chiusi).

---

## Self-Review

**Spec coverage:**
- 75 entry ripristinate da fonte con convenzione catalogo → Task 1 ✓ (fonte di verità = report committato, convenzione = entry D verificata)
- References "Archives of a deity of magic" → Task 2 ✓ (tutti i cataloghi OGL)
- Sanitize riapplicata + legal 0 + spot check → Task 1 Step 6 ✓
- Gate/manifest? (feats count invariato: nessun update manifest necessario — i count non cambiano) /reindice/launch.py/doc/handoff → Task 3 ✓
- Segnalazione pathmaster-dd → già eseguita fuori piano (commit `875c946` + WORKFLOW §4 `6e90c09`)

**Placeholder scan:** una nota implementativa (robustezza parser prereq) con verifica concreta indicata; nessun TBD.

**Type consistency:** `appendix_names() -> list[str]`, `parse_feat_page(str) -> dict` (chiavi name/source/flavor/prerequisites/benefit), `apply_restore(dict, dict) -> dict`, `fix_entry(dict) -> tuple[dict, int]` — identici in tool e test. `split_prereq_string`/`clean`/`OGL_DIR` da `reference_lib`, `cache_path`/`fetch` da `reference_fetch`, `sanitize_text` da `sanitize_reference_pi` — tutti esistenti.
