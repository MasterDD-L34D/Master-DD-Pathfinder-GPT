# Espansione dataset mostri (3659 pagine AoN) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Portare il dataset mostri da 199 a copertura completa AoN: 3083 Monsters + 89 MythicMonsters + 487 NPCs (indici `Monsters.aspx?Letter=All`, `MythicMonsters.aspx?Letter=All`, `NPCs.aspx?SubGroup=All`), in `pi_local_only/monsters_local.json` + `npcs_local.json` (kind separati, consumer Encounter_Designer vs Taverna_NPC).

**Architecture:** `tools/expand_monsters.py` (nuovo dominio parallelo-sicuro): `--fetch` (reference_fetch 2s, cache = resume gratis) → `--parse` (parsePage di PathfinderMonsterDatabase come libreria, con `class_hds`/`classname_map` iniettati) → `--convert` (riuso `convert_monsters` di import_monsters; split per `_kind`, tag mythic/npc, dedup per nome, manifest). Validazione: report + spot-check swarm + `validate_monsters.py` (CR-band) sul dataset espanso.

**Tech Stack:** Python 3, `reference_fetch`, PathfinderMonsterDatabase `main.py` (regex, tqdm: presenti). Nessuna nuova dipendenza.

**Spec (grilling 2026-07-25):** perimetro C (tutto: 3659 pagine); due file locali (mostri+mitici insieme, NPC a parte); fetch unico background ~2,5h con failures in report (mai bloccanti); dati sempre e solo `pi_local_only` (nessun triage PI per-entry: la destinazione intera è local-only).

**Stato al momento del piano:** fetch già lanciato in background (task `bash-dlpp4b6f`); `--fetch` e `--parse` implementati e verificati (10/10 pagine fresche parse ok, inclusa iniezione `class_hds`/`classname_map`).

---

### Task 1: `--convert` — split, tag, dedup, manifest

**Files:**
- Modify: `tooling/Master-DD-Taverna/tools/expand_monsters.py` (`cmd_convert` + `split_and_convert`)
- Test: `tooling/Master-DD-Taverna/tests/test_expand_monsters.py`

- [ ] **Step 1: Write the failing test**

Creare `tests/test_expand_monsters.py`:

```python
"""Test per tools/expand_monsters.py — split/convert del dataset espanso."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.expand_monsters import split_and_convert


def _obj(name, kind, cr=5):
    return {"title1": name, "title2": name, "CR": cr, "XP": 1600,
            "sources": [{"name": "Bestiary 2", "page": 42}],
            "alignment": {"raw": "NE", "cleaned": "NE"}, "size": "Medium",
            "type": "outsider", "HP": {"total": 45, "long": "5d10+15"},
            "AC": {"AC": 18, "touch": 12, "flat_footed": 16},
            "saves": {"fort": 6, "ref": 5, "will": 4},
            "desc_short": f"{name} short.", "_kind": kind}


def test_split_and_convert_kinds_tags_dedup():
    objects = {
        "u1": _obj("Alpha", "monsters"),
        "u2": _obj("Beta", "mythic"),
        "u3": _obj("Gamma", "npcs"),
        "u4": _obj("Alpha", "monsters"),  # duplicato: scartato (tiene il primo)
    }
    monsters, npcs = split_and_convert(objects)
    assert [e["name"] for e in monsters] == ["Alpha", "Beta"]
    assert [e["name"] for e in npcs] == ["Gamma"]
    beta = monsters[1]
    assert "mythic" in beta["tags"]
    assert "monster" in beta["tags"]
    assert "npc" in npcs[0]["tags"] and "monster" not in npcs[0]["tags"]
    # mechanics v2 preservati dal convert
    assert monsters[0]["mechanics"]["cr"] == 5
    assert monsters[0]["mechanics"]["type"] == "outsider"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tooling/Master-DD-Taverna && .venv/Scripts/python -m pytest tests/test_expand_monsters.py -q`
Expected: FAIL — ImportError (`split_and_convert` non esiste).

- [ ] **Step 3: Implement `split_and_convert` + `cmd_convert`**

In `tools/expand_monsters.py`:

```python
def split_and_convert(objects: dict) -> tuple[list, list]:
    """{url: pageObject con _kind} -> (monster_entries, npc_entries).

    monsters+mythic insieme (tag 'mythic' sui mitici), npc a parte (tag 'npc'
    al posto di 'monster'); dedup per nome (tiene il primo, ordine URL)."""
    from tools.import_monsters import convert_monsters
    seen = set()
    monsters, npcs = [], []
    for kind_target, kind_list in (("monsters", monsters), ("npcs", npcs)):
        items = [(url, obj) for url, obj in objects.items()
                 if (obj.get("_kind") in ("monsters", "mythic")) == (kind_target == "monsters")]
        for e in convert_monsters(items):
            if e["name"] in seen:
                continue
            seen.add(e["name"])
            src_kind = next(obj["_kind"] for u, obj in items if obj.get("title1") == e["name"])
            if kind_target == "npcs":
                e["tags"] = ["npc" if t == "monster" else t for t in e["tags"]]
            elif src_kind == "mythic":
                e["tags"] = e["tags"] + ["mythic"]
            kind_list.append(e)
    return monsters, npcs


def cmd_convert(write: bool) -> int:
    from datetime import date
    objects = json.loads(EXPANDED_JSON.read_text(encoding="utf-8"))
    monsters, npcs = split_and_convert(objects)
    print(f"convert: {len(monsters)} mostri (+mitici), {len(npcs)} npc")
    if not write:
        print("Dry-run: nessuna modifica (usa --write)")
        return 0
    for path, entries in ((LOCAL_DIR / "monsters_local.json", monsters),
                          (LOCAL_DIR / "npcs_local.json", npcs)):
        path.write_text(json.dumps({
            "_license": "OGL-1.0a",
            "_source": "Archives of Nethys via PathfinderMonsterDatabase (local only, not redistributed)",
            "entries": entries,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"scritto {path} ({len(entries)} entry, NON committare)")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    for c in manifest["catalogs"]:
        if c["kind"] == "monsters":
            c["entries"] = len(monsters)
            c["last_verified"] = today
    manifest["catalogs"] = [c for c in manifest["catalogs"] if c["kind"] != "npcs_local"]
    manifest["catalogs"].append({
        "file": "pi_local_only/npcs_local.json", "kind": "npcs_local",
        "source": "Archives of Nethys (aonprd.com)", "license": "OGL-1.0a",
        "is_ogc": False, "is_pi": False, "cup_allowed": False, "local_only": True,
        "entries": len(npcs),
        "notes": "NPC da NPCs.aspx AoN (espansione 2026-07-25). NON redistribuire.",
        "last_verified": today})
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print("manifest aggiornato (monsters + npcs_local)")
    return 0
```

E collegare in `main()`: `if args.convert: return cmd_convert(args.write)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_expand_monsters.py -q`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
cd tooling/Master-DD-Taverna
git add tools/expand_monsters.py tests/test_expand_monsters.py planning/2026-07-25-monsters-expansion.md
git commit -m "feat(tools): add monster expansion fetch parse convert pipeline"
```

---

### Task 2: Parse + convert sul dataset completo (a fetch completato)

- [ ] **Step 1: Verifica fetch** (notifica automatica): atteso `fetch: 3659/3659 ok` (o fallimenti documentati).
- [ ] **Step 2: Parse**

```bash
cd tooling/Master-DD-Taverna
.venv/Scripts/python tools/expand_monsters.py --parse
```

Expected: `parse: ~3650 ok, <failures>` con `data/expanded/failures.txt` per i falliti (atteso: qualche pagina anomala, pattern broken_urls storico). Se failures > 50: ispezionare prima di procedere.

- [ ] **Step 3: Convert (dry-run) + spot check**

```bash
.venv/Scripts/python tools/expand_monsters.py --convert
```

Expected: ~3100 mostri + ~480 NPC. Spot check 3 entry (1 mostro storico dei 199, 1 mitico, 1 NPC).

- [ ] **Step 4: Convert --write + spot check CR-band**

```bash
.venv/Scripts/python tools/expand_monsters.py --convert --write
.venv/Scripts/python tools/validate_monsters.py
```

Expected: catalogo rigenerato; report CR-band su ~3100 mostri (rilievi plausibili, stessa distribuzione qualitativa del campione 199).

- [ ] **Step 5: Commit (solo manifest)**

```bash
cd tooling/Master-DD-Taverna
git add data/reference/manifest.json
git commit -m "feat(reference): expand monster dataset to full aon coverage"
```

Nota: `monsters_local.json`/`npcs_local.json` restano gitignored (nessun dato committato).

---

### Task 3: Validazione swarm + gate + handoff

- [ ] **Step 1: Spot-check swarm**: 4 subagent explore × 5 mostri nuovi casuali ciascuno (semi diversi: A-C, D-L, M-R, S-Z + 1 NPC per agente): confronto entry vs pagina in cache (CR, HP, AC, type, 1 attacco). Output: conforme/anomalia.
- [ ] **Step 2: Gate seriali**: pytest, validate_schemas, legal_filter, reindice `--include-local` (~3600 nuovi chunk), `python launch.py test`.
- [ ] **Step 3: IMPORT_PLAYBOOK §6.8 + commit/push + handoff + sync notebooklm-fonti.**

---

## Self-Review

**Spec coverage:** perimetro C → index_urls 3 fonti ✓; due file separati + tag mythic/npc → split_and_convert ✓; resume via cache → --fetch ✓; failures non bloccanti → --parse ✓; pi_local_only integrale → convert scrive solo lì, commit solo manifest ✓; validazione swarm + CR-band → Task 3 ✓.

**Placeholder scan:** nessun TBD; i conteggi sono attese verificabili.

**Type consistency:** `index_urls() -> dict[str, list[str]]`; `split_and_convert(dict) -> tuple[list, list]`; `cmd_convert(write: bool) -> int` — identici in tool e test. `convert_monsters` riusato da import_monsters (firma invariata, i 199 restano coperti).
