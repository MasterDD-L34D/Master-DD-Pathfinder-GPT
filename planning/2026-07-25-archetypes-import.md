# Archetipi Lotto 2 — import da indici AoN per classe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Importare gli archetipi delle 24 classi del catalogo in `archetypes.json` (schema standard, oggi 15 entry legacy senza mechanics), da indici AoN `Archetypes.aspx?Class=<Classe>`: tabella curata Name/Replaces/Summary con marcatori razziali `(X Only)`. Triage PI come da policy.

**Architecture:** Task 1 crea `tools/import_archetypes.py` con `parse_archetypes` (parse tabella, nuovo dominio nel pattern parallelo-sicuro: nessuna modifica a import_reference) + entry builder + triage PI (nomi PI → `pi_local_only/archetypes_local.json`, prosa sanitizzata). Task 2 warm-cache seriale (24 pagine, cortesia 2s; Fighter già in cache) + import + report di validazione. Task 3 gate seriali + doc + handoff.

**Tech Stack:** Python 3, BeautifulSoup, pytest, `tools/reference_fetch` (cache + delay), venv esistente. Nessuna nuova dipendenza.

**Spec (grilling 2026-07-25 + adattamento confermato):** solo le 24 pagine indice (niente ~1000 pagine dettaglio: `alters`/feature complete = lotto futuro se il builder le richiede); `mechanics: {class, replaces[], race_req[]|null}`; `race_req` dai marcatori `(X Only)` nella tabella (copre anche razze non-core; cross-ref pagine razza superfluo); `archetypes.json` riscritta in schema standard (le 15 legacy non hanno consumer diretti); nomi con identità PI → local; prosa → sanitize; provenienza onesta (source = AoN, la tabella indice non riporta il libro). **Deviazione dal processo ibrido, concordata**: la review swarm per classe è sostituita da report di validazione deterministico + spot check (il parsing è estrazione tabellare uniforme, non più parsing fragile per-pagina).

---

### Task 1: `tools/import_archetypes.py` — parse + build + triage PI

**Files:**
- Create: `tooling/Master-DD-Taverna/tools/import_archetypes.py`
- Create: `tooling/Master-DD-Taverna/tests/test_import_archetypes.py`

- [ ] **Step 1: Write the failing test**

Creare `tests/test_import_archetypes.py`:

```python
"""Test per tools/import_archetypes.py — parse indici archetipi AoN."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.import_archetypes import parse_archetypes, archetype_entry

# Markup ricalcato sulla pagina reale Archetypes.aspx?Class=Fighter
# (cache 2026-07-25): header <td><b>Name</b>..., celle con <a> + <img> PFS.
FIGHTER_HTML = """
<html><body>
<h1 class="title">Fighter Archetypes</h1>
<table>
<tr><td><b>Name</b></td><td><b>Replaces</b></td><td><b>Summary</b></td></tr>
<tr><td><a href="ArchetypeDisplay.aspx?FixedName=Fighter Aerial Assaulter"><img src="images\\PathfinderSocietySymbol.gif" title="PFS Legal"/> Aerial Assaulter</a></td><td>Class Skills; Bravery; Armor Mastery, Weapon Mastery</td><td>Aerial assaulters leap to great heights.</td></tr>
<tr><td><a href="ArchetypeDisplay.aspx?FixedName=Fighter Airborne Ambusher">Airborne Ambusher</a></td><td>Weapon/Armor Proficiency; Weapon Training 1-4 (Strix Only)</td><td>Driven by suspicion, strix guard their territories.</td></tr>
</table>
</body></html>
"""


def test_parse_archetypes_table():
    rows = parse_archetypes(FIGHTER_HTML)
    assert len(rows) == 2
    r0 = rows[0]
    assert r0["name"] == "Aerial Assaulter"
    assert r0["replaces"] == ["Class Skills", "Bravery", "Armor Mastery, Weapon Mastery"]
    assert r0["race_req"] is None
    assert r0["summary"] == "Aerial assaulters leap to great heights."
    assert r0["detail_url"] == ("https://aonprd.com/ArchetypeDisplay.aspx"
                                "?FixedName=Fighter%20Aerial%20Assaulter")
    r1 = rows[1]
    assert r1["race_req"] == ["Strix"]
    # il marcatore razziale e' rimosso dagli item replaces
    assert r1["replaces"] == ["Weapon/Armor Proficiency", "Weapon Training 1-4"]


def test_parse_archetypes_no_table():
    assert parse_archetypes("<html><body><p>nessuna tabella</p></body></html>") == []


def test_archetype_entry_catalog_shape():
    row = {"name": "Aerial Assaulter",
           "replaces": ["Class Skills", "Bravery"],
           "race_req": None,
           "summary": "Aerial assaulters leap to great heights.",
           "detail_url": "https://aonprd.com/ArchetypeDisplay.aspx?FixedName=Fighter%20Aerial%20Assaulter"}
    e = archetype_entry(row, "Fighter")
    assert e["name"] == "Aerial Assaulter"
    assert e["source_id"] == "archetype:fighter_aerial_assaulter"
    assert e["prerequisites"] == []
    assert "archetype" in e["tags"] and "fighter" in e["tags"]
    assert e["mechanics"] == {"class": "Fighter",
                              "replaces": ["Class Skills", "Bravery"],
                              "race_req": None}
    assert e["reference_urls"][0] == "https://aonprd.com/Archetypes.aspx?Class=Fighter"
    assert e["reference_urls"][1] == row["detail_url"]
    assert e["description"] == row["summary"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tooling/Master-DD-Taverna && .venv/Scripts/python -m pytest tests/test_import_archetypes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.import_archetypes'`.

- [ ] **Step 3: Implement `tools/import_archetypes.py`**

Creare il file:

```python
#!/usr/bin/env python3
"""Importa gli archetipi delle classi del catalogo dagli indici AoN
(Archetypes.aspx?Class=<Classe>): tabella curata Name/Replaces/Summary con
marcatori razziali '(X Only)'. Lotto 2 archetipi 2026-07-25.

Policy (spec grilling 2026-07-25, adattamento tabella-indice confermato):
- solo le pagine indice (24 classi di classes.json); i dettagli per-capacita'
  (alters/level/testo completo da ArchetypeDisplay) sono lotto futuro;
- race_req dai marcatori '(X Only)' nella tabella (copre razze non-core);
- archetypes.json riscritto in schema standard (header preservato);
- nomi con identita' PI -> pi_local_only/archetypes_local.json (verbatim);
  description sanitizzata (description=True); gate legal_filter = 0;
- manifest aggiornato (files.archetypes + catalogs archetypes/archetypes_local).

Default: dry-run. --write applica. --offline usa solo la cache (no rete).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.expand_spells_gist import is_pi_name
from tools.reference_fetch import fetch
from tools.reference_lib import OGL_DIR, clean, slug, source_id
from tools.sanitize_reference_pi import sanitize_text

ROOT = Path(__file__).resolve().parents[1]
ARCHETYPES_PATH = OGL_DIR / "archetypes.json"
CLASSES_PATH = OGL_DIR / "classes.json"
LOCAL_PATH = ROOT / "data" / "reference" / "pi_local_only" / "archetypes_local.json"
MANIFEST_PATH = ROOT / "data" / "reference" / "manifest.json"
REPORT_PATH = ROOT / "reports" / "import_archetypes.md"
BASE = "https://aonprd.com/"

_RACE_ONLY_RE = re.compile(r"\(([^()]+?)\s+[Oo]nly\)")


def parse_archetypes(html: str) -> list[dict]:
    """Tabella Name/Replaces/Summary -> [{name, replaces, race_req, summary, detail_url}]."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        if not trs:
            continue
        headers = [clean(c.get_text()) for c in trs[0].find_all(["th", "td"])]
        if headers[:3] != ["Name", "Replaces", "Summary"]:
            continue
        rows = []
        for tr in trs[1:]:
            cells = tr.find_all(["th", "td"], recursive=False)
            if len(cells) != 3:
                continue
            name = clean(cells[0].get_text())
            link = cells[0].find("a")
            detail_url = None
            if link and link.get("href"):
                href = link["href"]
                if not href.startswith("http"):
                    href = BASE + href
                detail_url = href.replace(" ", "%20")
            raw_replaces = clean(cells[1].get_text())
            summary = clean(cells[2].get_text())
            blob = f"{raw_replaces} {summary}"
            race_req = sorted(set(_RACE_ONLY_RE.findall(blob))) or None
            replaces = [r.strip() for r in
                        _RACE_ONLY_RE.sub("", raw_replaces).split(";")
                        if r.strip()]
            rows.append({"name": name, "replaces": replaces,
                         "race_req": race_req, "summary": summary,
                         "detail_url": detail_url})
        return rows
    return []


def archetype_entry(row: dict, class_name: str) -> dict:
    """Riga parsata -> entry catalogo standard (description sanitizzata)."""
    tags = ["archetype", slug(class_name), slug(row["name"]).replace("_", "-")]
    if row["race_req"]:
        tags += [f"race:{slug(r)}" for r in row["race_req"]]
    return {
        "name": row["name"],
        "source": "Archives of Nethys (aonprd.com)",
        "source_id": source_id("archetype", f"{class_name} {row['name']}"),
        "prerequisites": [],
        "tags": tags,
        "references": [f"AoN: {class_name} Archetypes"],
        "reference_urls": ([f"{BASE}Archetypes.aspx?Class={class_name.replace(' ', '%20')}"]
                           + ([row["detail_url"]] if row["detail_url"] else [])),
        "description": sanitize_text(row["summary"], description=True),
        "mechanics": {"class": class_name,
                      "replaces": row["replaces"],
                      "race_req": row["race_req"]},
    }


def catalog_classes() -> list[str]:
    data = json.loads(CLASSES_PATH.read_text(encoding="utf-8"))
    return [e["name"] for e in data["entries"]]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--offline", action="store_true",
                    help="fallisce se una pagina non e' in cache (nessuna rete)")
    args = ap.parse_args(argv)

    classes = catalog_classes()
    all_entries, local_entries, report = [], [], []
    for cls in classes:
        url = f"{BASE}Archetypes.aspx?Class={cls.replace(' ', '%20')}"
        try:
            html = fetch(url, delay=2.0, cache=True) if not args.offline else fetch(url, delay=0, cache=True)
        except Exception as exc:  # rete giu' o pagina assente
            report.append(f"- **{cls}**: FETCH FALLITO ({exc})")
            continue
        rows = parse_archetypes(html)
        n_racial = sum(1 for r in rows if r["race_req"])
        n_zero = sum(1 for r in rows if not r["replaces"])
        report.append(f"- **{cls}**: {len(rows)} archetipi "
                      f"({n_racial} razziali, {n_zero} senza replaces)")
        for row in rows:
            entry = archetype_entry(row, cls)
            (local_entries if is_pi_name(entry["name"]) else all_entries).append(entry)

    total = len(all_entries) + len(local_entries)
    print(f"classi: {len(classes)}; archetipi: {total} "
          f"(OGL {len(all_entries)}, PI->local {len(local_entries)})")
    print("\n".join(report))
    if not args.write:
        print("Dry-run: nessuna modifica (usa --write)")
        for e in local_entries[:20]:
            print(f"  PI local: {e['mechanics']['class']} / {e['name']}")
        return 0

    catalog = json.loads(ARCHETYPES_PATH.read_text(encoding="utf-8"))
    catalog["entries"] = all_entries
    ARCHETYPES_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    local_catalog = {
        "_license": "OGL-1.0a",
        "_source": "Archives of Nethys (local only, not redistributed)",
        "entries": local_entries,
    }
    LOCAL_PATH.write_text(json.dumps(local_catalog, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    manifest["files"]["archetypes"]["entries"] = len(all_entries)
    for c in manifest["catalogs"]:
        if c["kind"] == "archetypes":
            c["entries"] = len(all_entries)
            c["last_verified"] = today
            c["notes"] = ("Archetipi da indici AoN per classe (tabella "
                          "Name/Replaces/Summary): mechanics {class, replaces, "
                          "race_req}. Rigenerare con tools/import_archetypes.py.")
    manifest["catalogs"] = [c for c in manifest["catalogs"] if c["kind"] != "archetypes_local"]
    if local_entries:
        manifest["catalogs"].append({
            "file": "pi_local_only/archetypes_local.json",
            "kind": "archetypes_local",
            "source": "Archives of Nethys (aonprd.com)",
            "license": "OGL-1.0a",
            "is_ogc": False, "is_pi": False, "cup_allowed": False,
            "local_only": True,
            "entries": len(local_entries),
            "notes": ("Archetipi con Product Identity nel nome, separati dal "
                      "catalogo OGL (policy 2026-07-25). NON redistribuire."),
            "last_verified": today,
        })
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    lines = ["# Import archetipi da indici AoN (2026-07-25)", "",
             f"- Classi: {len(classes)}",
             f"- Archetipi totali: {total}",
             f"- OGL (archetypes.json): {len(all_entries)}",
             f"- PI -> archetypes_local.json: {len(local_entries)}", "",
             "## Conteggi per classe", ""] + report + [
             "", "## Nomi PI spostati in locale", ""]
    lines += [f"- {e['mechanics']['class']} / {e['name']}" for e in local_entries]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scritto: {ARCHETYPES_PATH} ({len(all_entries)} entry)")
    print(f"Scritto: {LOCAL_PATH} ({len(local_entries)} entry, NON committare)")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Nota implementativa: `fetch(url, delay=0, cache=True)` in modalità `--offline` solleva se il file non è in cache (verificare il comportamento di `reference_fetch.fetch` con `cache=True` e miss: se scarica comunque, sostituire la lettura diretta di `cache_path(url)` con `sys.exit` su miss).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_import_archetypes.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd tooling/Master-DD-Taverna
git add tools/import_archetypes.py tests/test_import_archetypes.py planning/2026-07-25-archetypes-import.md
git commit -m "feat(tools): add archetype index importer with pi triage"
```

---

### Task 2: Warm-cache seriale + import + report di validazione

**Files:**
- Modify (generati): `data/reference/ogl/archetypes.json`, `data/reference/pi_local_only/archetypes_local.json` (NON committato), `data/reference/manifest.json`
- Create (committato): `reports/import_archetypes.md`

- [ ] **Step 1: Warm-cache seriale**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -c "
import sys; sys.path.insert(0, '.')
from tools.reference_fetch import fetch
from tools.import_archetypes import catalog_classes
for cls in catalog_classes():
    url = f'https://aonprd.com/Archetypes.aspx?Class={cls.replace(\" \", \"%20\")}'
    try:
        html = fetch(url, delay=2.0, cache=True)
        print(f'{cls:15s} {len(html):7d} bytes')
    except Exception as exc:
        print(f'{cls:15s} FALLITO: {exc}')
"
```

Expected: 24 righe con byte > 0 (Fighter istantaneo, già in cache; le altre ~23 pagine × 2s ≈ 46s). Se qualche classe FALLISCE (rete o nome URL diverso, es. classi con spazi): annotare, verificare il nome URL esatto sulla pagina classe in cache (link `Archetypes.aspx?Class=` nella pagina ClassDisplay, come fatto per Fighter) e correggere la mappa URL nel tool prima di procedere.

- [ ] **Step 2: Dry-run**

```bash
.venv/Scripts/python tools/import_archetypes.py
```

Expected: conteggi per classe > 0 per la quasi totalità (stima 800-1200 totali); lista PI-local coerente (nomi con divinità/etnie Golarion, es. "Aldori Defender" se "Aldori" è in PI_WORDS). Classi con 0 archetipi: plausibile per alcune (verificare a campione sulla pagina che la tabella manchi davvero, non un parse fallito — il report le elenca).

- [ ] **Step 3: Apply + gate legal**

```bash
.venv/Scripts/python tools/import_archetypes.py --write
.venv/Scripts/python tools/legal_filter.py
```

Expected: legal_filter **0 violazioni**. Se residui nelle summary: supplemento DESCRIPTION_ONLY in `sanitize_reference_pi.py` + revert (`git checkout -- data/reference/ogl/archetypes.json data/reference/manifest.json`) + re-apply, come fatto per le spell.

- [ ] **Step 4: Validazione (sostitutiva della review swarm)**

```bash
.venv/Scripts/python -c "
import json
a = json.load(open('data/reference/ogl/archetypes.json', encoding='utf-8'))
es = a['entries']
names = [(e['mechanics']['class'], e['name']) for e in es]
assert len(set(names)) == len(names), 'duplicati (classe, nome)!'
sids = [e['source_id'] for e in es]
assert len(set(sids)) == len(sids), 'source_id duplicati!'
racial = [e for e in es if e['mechanics']['race_req']]
zero = [e for e in es if not e['mechanics']['replaces']]
print(f'{len(es)} entry; razziali: {len(racial)}; zero-replaces: {len(zero)}')
"
```

Expected: nessuna assertion. Poi **spot check manuale di 3 classi** (Fighter + 1 core caster + 1 non-core): 3-5 entry a campione confrontate con la tabella nella pagina in cache (nome, replaces, summary). I conteggi per classe nel report devono essere coerenti col contenuto delle pagine (il report è committato: `reports/import_archetypes.md`).

- [ ] **Step 5: Commit**

```bash
cd tooling/Master-DD-Taverna
git add data/reference/ogl/archetypes.json data/reference/manifest.json reports/import_archetypes.md
git commit -m "feat(reference): import archetypes for all 24 catalog classes"
```

---

### Task 3: Gate seriali, documentazione, handoff

**Files:**
- Modify: `tooling/Master-DD-Taverna/docs/IMPORT_PLAYBOOK.md` (nota §6.4)

- [ ] **Step 1: Suite completa + schemi**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python -m pytest tests/ -q
.venv/Scripts/python tools/validate_schemas.py
.venv/Scripts/python tools/legal_filter.py
```

Expected: pytest verde (348 + nuovi, 1 skipped); schemi OK; legal 0.

- [ ] **Step 2: Reindice RAG**

```bash
.venv/Scripts/python tools/index_rag.py --include-local
```

Expected: ri-encode dei chunk archetypes (kind già in catalogs[]; i 15 legacy escono, i nuovi entrano) + archetypes_local se presente. Chunk totali: ~8517 − 15 + nuovi.

- [ ] **Step 3: `python launch.py test` dalla root**

Expected: `TUTTE LE VERIFICHE OK`.

- [ ] **Step 4: Nota in `docs/IMPORT_PLAYBOOK.md`**

Aggiungere dopo la §6.3:

```markdown
## 6.4 Archetipi (2026-07-25)

`archetypes.json` riscritta in schema standard dagli indici AoN `Archetypes.aspx?Class=<Classe>` (tabella curata Name/Replaces/Summary): `mechanics {class, replaces[], race_req[]|null}` con `race_req` dai marcatori `(X Only)` (copre anche razze non-core). `tools/import_archetypes.py` (dry-run default, `--write` applica; fetch seriale 2s via reference_fetch, 24 pagine). Nomi PI → `pi_local_only/archetypes_local.json`; summary sanitizzate. Dettagli per-capacità (alters/level/testo completo da ArchetypeDisplay) = lotto futuro se richiesti dal builder. Report: `reports/import_archetypes.md`.
```

- [ ] **Step 5: Commit finale + push**

```bash
cd tooling/Master-DD-Taverna
git add docs/IMPORT_PLAYBOOK.md
git commit -m "docs(reference): document archetypes index import"
git push origin main
```

- [ ] **Step 6: Handoff**

Aggiornare `sessione-2026-07-16/HANDOFF_ATTIVO.md` (stato + completati; follow-up aggiornati: dettagli ArchetypeDisplay, espansione mostri, fetch spell AoN se lacune) e sincronizzare `notebooklm-fonti/HANDOFF_ATTIVO.md` con `cp`.

---

## Self-Review

**Spec coverage:**
- 24 classi, solo pagine indice → Task 2 Step 1-2 ✓
- `mechanics {class, replaces, race_req}` + marcatori `(X Only)` → Task 1 (`parse_archetypes`) ✓
- archetypes.json schema standard, legacy sostituite → Task 2 Step 3 (riscrittura con header preservato) ✓
- Nomi PI → local / prosa → sanitize / legal 0 → Task 1 (`is_pi_name`, `sanitize_text`) + Task 2 Step 3 ✓
- alters/dettagli = lotto futuro → nota §6.4 ✓
- Validazione sostitutiva review swarm (concordata) → Task 2 Step 4 ✓
- Gate/manifest/reindice/launch.py/handoff → Task 3 ✓

**Placeholder scan:** una nota implementativa (`--offline` comportamento cache-miss di `reference_fetch`) con istruzione concreta di fix; conteggi espressi come stime verificabili a runtime. Nessun TBD.

**Type consistency:** `parse_archetypes(str) -> list[dict]` con chiavi `name/replaces/race_req/summary/detail_url`; `archetype_entry(dict, str) -> dict`; `catalog_classes() -> list[str]` — identici in tool e test. `is_pi_name` riusata da `expand_spells_gist`, `fetch` da `reference_fetch`, `clean/slug/source_id/OGL_DIR` da `reference_lib`, `sanitize_text` da `sanitize_reference_pi` — tutti esistenti e verificati nei lotti precedenti.
