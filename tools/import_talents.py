#!/usr/bin/env python3
"""Importa i talenti selezionabili per classe (sotto-cataloghi) dalle pagine
dedicate AoN in un nuovo catalogo data/reference/ogl/talents.json.
Lotto C2 task 2 (2026-07-26, planning/2026-07-26-talent-subcatalogs.md).

Pool importati (7 richiesti + sotto-pool distinti trovati in fonte):
- rage power (Barbarian): la pagina indice BarbarianRagePowers.aspx elenca
  solo le categorie; le entry sono nelle 6 sottopagine ?Type=Offensive|
  Defensive|Misc|Blood|Elemental|Totem -> mechanics.category. La pagina
  include anche l'intro 'Skald Rage Powers' (lo skald usa la STESSA lista):
  nessun pool separato, class resta 'Barbarian'.
- mercy (Paladin): sezioni h2 'Nth-Level Mercies' -> mechanics.level.
- rogue talent (Rogue): h1 'Rogue Talents' + h1 'Advanced Rogue Talents'
  -> pool separato 'advanced rogue talent' (decisione piano); h2 'Sneak
  Attack Talents'/'Other Talents' -> mechanics.category.
- discovery (Alchemist): h2 per categoria (bomb/extract/...) ->
  mechanics.category; h1 'Grand Discoveries' -> pool 'grand discovery'.
- hex (Witch): h1 'Hexes'/'Major Hexes'/'Grand Hexes' -> pool
  'hex'/'major hex'/'grand hex' (distinzioni di fonte, selezionabili a
  livelli diversi).
- deed (Swashbuckler): h2 'Nth-level Deeds' -> mechanics.level; h1 'Deeds
  of Renown' -> mechanics.category 'renowned'.
- ki power (Monk (Unchained)): sezione 'Ki Powers (Su)' DENTRO la pagina
  ClassDisplay (entry '<i>Nome (Su)</i>:' inline); le class features della
  pagina NON vengono re-importate.
- ninja trick + advanced (Ninja), slayer talent + advanced (Slayer):
  stesse convenzioni dei rogue (h1 -> pool, h2 'Sneak Attack/Other
  Talents' -> category). Lotto C4-bis follow-up 2026-07-26.
- social talent / vigilante talent (Vigilante): pagina unica a 3 sezioni
  h1; la sotto-lista 'Vigilante Talents - Hidden Strike' resta nel pool
  'vigilante talent' con category 'hidden strike' (override esplicito
  h1_categories); category ridondante col pool (h2 = nome del pool) ->
  None.

Policy (allineata ai lotti precedenti):
- markup a tabella 'MainContent_DataList*': entry '<b|i>Nome (Ex|Su|Sp)</b|i>
  (<a>Fonte pg. N</a>): testo<hr />' — suffisso (Ex)/(Su)/(Sp) tolto dal nome
  (mechanics.kind), '*' finale AoN (marchio 'non PFS core') tolto dal nome;
  tabelle annidate nella riga (es. DC per settlement size) ESCLUSE dalla
  description (assenza onesta: il dato tabellare resta via reference_url,
  niente serializzazione inline — fix 2026-07-26);
- source = titolo libro del link per-entry (senza 'pg. N'; attribution
  onesta, policy 6.1.1 playbook); description = testo dopo '):', sanitizzato
  PI (description=True);
- nessun campo inventato: nessuna pagina ha etichette 'Prerequisite(s):'
  -> prerequisites sempre [] (i vincoli restano in prosa nella description);
- nomi con identita' PI (is_pi_name) -> pi_local_only/talents_local.json
  (verbatim); description sanitize nel catalogo OGL; gate legal_filter = 0;
- dedup per (pool, name): prima occorrenza vince, duplicati contati
  (in fonte non ce ne sono dentro lo stesso pool);
- manifest aggiornato (files.talents + catalogs talents/talents_local).

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
from tools.reference_fetch import cache_path, fetch
from tools.reference_lib import OGL_DIR, clean, slug, source_id, write_catalog
from tools.sanitize_reference_pi import sanitize_text

ROOT = Path(__file__).resolve().parents[1]
TALENTS_PATH = OGL_DIR / "talents.json"
LOCAL_PATH = ROOT / "data" / "reference" / "pi_local_only" / "talents_local.json"
MANIFEST_PATH = ROOT / "data" / "reference" / "manifest.json"
REPORT_PATH = ROOT / "reports" / "import_talents.md"
BASE = "https://aonprd.com/"

# Configurazione pool: pagine tabellari (parser parse_talent_tables) tranne
# ki power (parser dedicato parse_ki_powers sulla pagina classe).
POOLS = [
    {"pool": "rage power", "cls": "Barbarian",
     "ref": "AoN: Rage Powers (Barbarian)",
     "pages": [(f"{BASE}BarbarianRagePowers.aspx?Type={t}", cat)
               for t, cat in [("Offensive", "offensive"),
                              ("Defensive", "defensive"),
                              ("Misc", "miscellaneous"),
                              ("Blood", "blood"),
                              ("Elemental", "elemental"),
                              ("Totem", "totem")]]},
    {"pool": "mercy", "cls": "Paladin",
     "ref": "AoN: Mercies (Paladin)",
     "pages": [(f"{BASE}PaladinMercies.aspx", None)]},
    {"pool": "rogue talent", "cls": "Rogue",
     "ref": "AoN: Rogue Talents (Rogue)",
     "h1_pools": {"Rogue Talents": "rogue talent",
                  "Advanced Rogue Talents": "advanced rogue talent"},
     "pages": [(f"{BASE}RogueTalents.aspx", None)]},
    {"pool": "discovery", "cls": "Alchemist",
     "ref": "AoN: Discoveries (Alchemist)",
     "h1_pools": {"Alchemist Discoveries": "discovery",
                  "Grand Discoveries": "grand discovery"},
     "pages": [(f"{BASE}AlchemistDiscoveries.aspx", None)]},
    {"pool": "hex", "cls": "Witch",
     "ref": "AoN: Hexes (Witch)",
     "h1_pools": {"Hexes": "hex", "Major Hexes": "major hex",
                  "Grand Hexes": "grand hex"},
     "pages": [(f"{BASE}WitchHexes.aspx", None)]},
    {"pool": "deed", "cls": "Swashbuckler",
     "ref": "AoN: Deeds (Swashbuckler)",
     "pages": [(f"{BASE}SwashbucklerDeeds.aspx", None)]},
    {"pool": "ki power", "cls": "Monk (Unchained)",
     "ref": "AoN: Ki Powers (Monk Unchained)",
     "parser": "ki",
     "pages": [(f"{BASE}ClassDisplay.aspx?ItemName=Monk%20(Unchained)", None)]},
    # Lotto C4-bis follow-up (2026-07-26): pool delle 5 classi residue C4.
    # Stesse convenzioni dei pool rogue: h1 -> pool, h2 -> category
    # ('Sneak Attack Talents'/'Other Talents'). Ninja/slayer hanno la
    # variante 'advanced' (livello 10+) come pool distinto.
    {"pool": "ninja trick", "cls": "Ninja",
     "ref": "AoN: Ninja Tricks (Ninja)",
     "h1_pools": {"Ninja Tricks": "ninja trick",
                  "Advanced Ninja Tricks": "advanced ninja trick"},
     "pages": [(f"{BASE}NinjaTricks.aspx", None)]},
    {"pool": "slayer talent", "cls": "Slayer",
     "ref": "AoN: Slayer Talents (Slayer)",
     "h1_pools": {"Slayer Talents": "slayer talent",
                  "Advanced Slayer Talents": "advanced slayer talent"},
     "pages": [(f"{BASE}SlayerTalents.aspx", None)]},
    # Vigilante: la pagina unica contiene social talents, vigilante talents
    # e la sotto-lista 'Hidden Strike' (category esplicita via h1_categories:
    # il titolo h2 non e' normalizzabile con le regole generiche).
    {"pool": "vigilante talent", "cls": "Vigilante",
     "ref": "AoN: Vigilante Talents (Vigilante)",
     "h1_pools": {"Social Talents": "social talent",
                  "Vigilante Talents": "vigilante talent",
                  "Vigilante Talents - Hidden Strike": "vigilante talent"},
     "h1_categories": {"Vigilante Talents - Hidden Strike": "hidden strike"},
     "pages": [(f"{BASE}VigilanteTalents.aspx", None)]},
]

_KIND_RE = re.compile(r"^(.*?)(?:\s*\((Ex|Su|Sp)\))?$")
_LEVEL_RE = re.compile(r"(\d+)(?:st|nd|rd|th)-level", re.I)
_CATEGORY_SUFFIX_RE = re.compile(
    r"(?i)\s+(?:talents|discoveries|rage powers|deeds|mercies)$")
_PAGE_RE = re.compile(r"\s*pg\.\s*\d+.*$")
_SPACE_PUNCT_RE = re.compile(r"\s+([.,;:!?])")


def _clean_rule_text(text):
    """Normalizza il testo regola accumulato per frammenti: whitespace via
    clean + niente spazio prima della punteggiatura (artefatto del join tra
    NavigableString e tag inline, es. 'dimension door .' -> 'dimension door.')."""
    return _SPACE_PUNCT_RE.sub(r"\1", clean(text))


def _split_name_kind(raw):
    """'Animal Fury (Ex)' -> ('Animal Fury', 'Ex'); '*' finale AoN tolto
    (marchio non-PFS, non fa parte del nome)."""
    raw = clean(raw).rstrip("*").strip()
    m = _KIND_RE.match(raw)
    return m.group(1).strip(), m.group(2)


def _category_from_h2(h2_text):
    """'Sneak Attack Talents' -> 'sneak attack'; 'Swashbuckler Renowned
    Deeds' -> 'renowned' (eccezione: il prefisso di classe va tolto).
    Le sezioni di livello ('3rd-Level Mercies') non sono categorie:
    l'informazione va in mechanics.level."""
    if not h2_text or _LEVEL_RE.search(h2_text):
        return None
    # Sezioni che duplicano il pool (es. 'Grand Discoveries') non aggiungono
    # informazione: niente category ridondante.
    if h2_text.strip().lower() in ("grand discoveries",):
        return None
    cat = _CATEGORY_SUFFIX_RE.sub("", h2_text)
    cat = re.sub(r"(?i)^swashbuckler\s+", "", cat)
    return cat.strip().lower() or None


def parse_talent_tables(html, h1_pools=None, page_category=None,
                        h1_categories=None):
    """Pagine a tabella AoN -> [{name, kind, source, text, pool, category, level}].

    Struttura reale (cache 2026-07-26): sezioni h1/h2.title; tabelle
    id='MainContent_DataList*'; ogni riga e' uno span LabelName con
    '<b|i>Nome (kind)</b|i> (<a>Fonte pg. N</a>): testo<hr />' (il nome e'
    <b> in alcune pagine, <i> in altre; puo' contenere l'img PFS).
    pool: da h1_pools (mappa titolo h1 -> pool) o None se la pagina e'
    single-pool (lo decide il chiamante). category: da page_category
    (sottopagine rage), da h1_categories (override esplicito per sezioni
    non normalizzabili, es. 'Vigilante Talents - Hidden Strike') o dal
    titolo h2; category uguale al pool (ridondante, es. h2 'Social
    Talents' nel pool 'social talent') -> None. level: dal titolo h2
    'Nth-level'."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    h1_cur = h2_cur = None

    def _section_or_datalist(t):
        if t.name in ("h1", "h2"):
            return True
        # Solo le DataList: le tabelle annidate nelle righe (table.inner)
        # non entrano nel walk (vengono decomposed durante il parse righe).
        return (t.name == "table"
                and str(t.get("id") or "").startswith("MainContent_DataList"))

    for el in soup.find_all(_section_or_datalist):
        if el.name in ("h1", "h2"):
            if "title" not in (el.get("class") or []):
                continue
            if el.name == "h1":
                h1_cur, h2_cur = clean(el.get_text()), None
            else:
                h2_cur = clean(el.get_text())
            continue
        pool = h1_pools.get(h1_cur) if h1_pools else None
        if h1_pools and pool is None:
            continue  # sezione h1 fuori scope (non inventare pool)
        category = (page_category or (h1_categories or {}).get(h1_cur)
                    or _category_from_h2(h2_cur))
        if category and pool and category in pool:
            category = None  # categoria ridondante col pool (es. 'social')
        m_lvl = _LEVEL_RE.search(h2_cur or "")
        level = int(m_lvl.group(1)) if m_lvl else None
        for span in el.find_all("span", id=re.compile(r"LabelName")):
            name_el = span.find(["b", "i"])
            if not name_el:
                continue
            name, kind = _split_name_kind(name_el.get_text())
            src_a = name_el.find_next("a")
            source = None
            if src_a:
                source = _PAGE_RE.sub("", clean(src_a.get_text())).strip() or None
            # Tabelle annidate nella riga (es. DC per settlement size di
            # Black Market Connections): escluse dalla description (assenza
            # onesta — il dato tabellare resta via reference_url), NON
            # serializzate inline. La soup e' locale alla chiamata.
            for tbl in span.find_all("table"):
                tbl.decompose()
            full = _clean_rule_text(span.get_text(" "))
            # Il testo regola inizia dopo la chiusura '(Fonte):'; il primo
            # '):' e' quello del blocco fonte (il nome non contiene '):').
            text = full.split("):", 1)[1].strip() if "):" in full else ""
            if name:
                entries.append({"name": name, "kind": kind, "source": source,
                                "text": text, "pool": pool,
                                "category": category, "level": level})
    return entries


def parse_ki_powers(html):
    """Sezione 'Ki Powers (Su)' della pagina ClassDisplay Monk (Unchained).

    Le entry sono '<i>Nome (Su)</i>: testo' inline dopo il bold di sezione
    '<b>Ki Powers (Su)</b>:'; la sezione finisce al bold della class feature
    successiva ('Style Strike (Ex)'). Discriminante entry: <i> il cui
    next_sibling testuale inizia per ':' (gli <i> di enfasi/spell nel testo
    non hanno ':' dopo). Niente campo source per-entry nella sezione:
    source=None -> fallback di pagina deciso dal chiamante."""
    from bs4 import BeautifulSoup, NavigableString
    soup = BeautifulSoup(html, "html.parser")
    marker = next((b for b in soup.find_all("b")
                   if clean(b.get_text()) == "Ki Powers (Su)"), None)
    if marker is None:
        return []

    def follower_colon(el):
        sib = el.next_sibling
        return (isinstance(sib, NavigableString)
                and str(sib).lstrip().startswith(":"))

    entries, current, parts = [], None, []
    marker_ids = set()

    def flush():
        if current is not None:
            text = _clean_rule_text(" ".join(parts)).lstrip(":").strip()
            name, kind = _split_name_kind(current)
            if name and text:
                entries.append({"name": name, "kind": kind, "source": None,
                                "text": text, "pool": "ki power",
                                "category": None, "level": None})

    # next_elements (NON find_all_next, che yields solo Tag): servono anche i
    # NavigableString per accumulare il testo oltre i tag inline — fix
    # 2026-07-26 (9 ki power troncati al primo <i> di spell citata).
    for el in marker.next_elements:
        nm = getattr(el, "name", None)
        if nm == "b" and follower_colon(el):
            break  # class feature successiva: fine sezione
        if nm == "i" and follower_colon(el):
            flush()
            current = clean(el.get_text())
            marker_ids.add(id(el))
            parts = []
            continue
        if isinstance(el, NavigableString) and current is not None:
            p = el.parent
            if p.name in ("b", "a", "script", "style", "sup", "h1", "h2", "h3"):
                continue
            if p.name == "i" and id(p) in marker_ids:
                continue  # il nome dell'entry non finisce nel testo
            parts.append(str(el))
    flush()
    return entries


def talent_entry(row, pool, cls, ref, page_url):
    """Riga parsata -> entry catalogo standard (description sanitizzata)."""
    tags = ["talent", pool.replace(" ", "-"), slug(cls).replace("_", "-"),
            slug(row["name"]).replace("_", "-")]
    mechanics = {"class": cls, "pool": pool, "kind": row["kind"]}
    if row.get("category"):
        mechanics["category"] = row["category"]
    if row.get("level") is not None:
        mechanics["level"] = row["level"]
    return {
        "name": row["name"],
        "source": row["source"] or "Archives of Nethys (aonprd.com)",
        "source_id": source_id("talent", f"{pool} {row['name']}"),
        "prerequisites": [],
        "tags": tags,
        "references": [ref],
        "reference_urls": [page_url],
        "description": sanitize_text(row["text"], description=True),
        "mechanics": mechanics,
    }


def _fetch_page(url, offline):
    """HTML della pagina; in --offline solo cache (mai rete)."""
    if offline:
        path = cache_path(url)
        if not path.exists():
            raise FileNotFoundError(f"non in cache: {url}")
        return path.read_text(encoding="utf-8", errors="replace")
    return fetch(url, delay=2.0, cache=True)


def collect_entries(offline):
    """Fetch + parse di tutti i pool -> (entries, stats_per_pool, anomalies)."""
    entries, anomalies = [], []
    for spec in POOLS:
        for url, page_category in spec["pages"]:
            try:
                html = _fetch_page(url, offline)
            except Exception as exc:  # rete giu' o pagina assente
                anomalies.append(f"- **{spec['pool']}** ({url}): FETCH FALLITO ({exc})")
                continue
            if spec.get("parser") == "ki":
                rows = parse_ki_powers(html)
            else:
                rows = parse_talent_tables(html, spec.get("h1_pools"),
                                           page_category,
                                           spec.get("h1_categories"))
                for row in rows:
                    row["pool"] = row["pool"] or spec["pool"]
            if not rows:
                anomalies.append(f"- **{spec['pool']}** ({url}): 0 entry parsate")
            for row in rows:
                if row["source"] is None and spec.get("parser") != "ki":
                    anomalies.append(
                        f"- **{spec['pool']} / {row['name']}**: fonte per-entry assente")
                entries.append(talent_entry(row, row["pool"], spec["cls"],
                                            spec["ref"], url))
    # Dedup per (pool, name): prima occorrenza vince.
    seen, deduped, dupes = set(), [], 0
    for e in entries:
        key = (e["mechanics"]["pool"], e["name"].lower())
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        deduped.append(e)
    return deduped, dupes, anomalies


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--offline", action="store_true",
                    help="fallisce se una pagina non e' in cache (nessuna rete)")
    args = ap.parse_args(argv)

    entries, dupes, anomalies = collect_entries(args.offline)
    all_entries, local_entries = [], []
    for e in entries:
        (local_entries if is_pi_name(e["name"]) else all_entries).append(e)

    by_pool = {}
    for e in all_entries:
        by_pool[e["mechanics"]["pool"]] = by_pool.get(e["mechanics"]["pool"], 0) + 1
    zero_text = sum(1 for e in all_entries + local_entries
                    if not e["description"])
    total = len(all_entries) + len(local_entries)
    print(f"talenti: {total} (OGL {len(all_entries)}, PI->local {len(local_entries)}); "
          f"duplicati scartati: {dupes}; senza testo: {zero_text}")
    for pool in sorted(by_pool):
        print(f"  {pool}: {by_pool[pool]}")
    if anomalies:
        print(f"anomalie: {len(anomalies)}")
        for line in anomalies[:30]:
            print(line)
    if not args.write:
        print("Dry-run: nessuna modifica (usa --write)")
        for e in local_entries[:20]:
            print(f"  PI local: {e['mechanics']['pool']} / {e['name']}")
        return 0

    write_catalog(TALENTS_PATH, all_entries)
    local_catalog = {
        "_license": "OGL-1.0a",
        "_source": "Archives of Nethys (local only, not redistributed)",
        "entries": local_entries,
    }
    LOCAL_PATH.write_text(json.dumps(local_catalog, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    manifest["files"]["talents"] = {"path": "ogl/talents.json",
                                    "entries": len(all_entries)}
    manifest["catalogs"] = [c for c in manifest["catalogs"]
                            if c["kind"] not in ("talents", "talents_local")]
    manifest["catalogs"].append({
        "file": "ogl/talents.json",
        "kind": "talents",
        "source": "Archives of Nethys (aonprd.com)",
        "license": "OGL-1.0a",
        "is_ogc": True, "is_pi": False, "cup_allowed": False,
        "entries": len(all_entries),
        "notes": ("Talenti selezionabili per classe da pagine dedicate AoN "
                  "(rage power/Barbarian, mercy/Paladin, rogue talent + "
                  "advanced/Rogue, discovery + grand/Alchemist, hex/major/"
                  "grand/Witch, deed/Swashbuckler, ki power/Monk Unchained, "
                  "ninja trick + advanced/Ninja, slayer talent + advanced/"
                  "Slayer, social + vigilante talent/Vigilante): "
                  "mechanics {class, pool, kind, category?, level?}. "
                  "Rigenerare con tools/import_talents.py."),
        "last_verified": today,
    })
    if local_entries:
        manifest["catalogs"].append({
            "file": "pi_local_only/talents_local.json",
            "kind": "talents_local",
            "source": "Archives of Nethys (aonprd.com)",
            "license": "OGL-1.0a",
            "is_ogc": False, "is_pi": False, "cup_allowed": False,
            "local_only": True,
            "entries": len(local_entries),
            "notes": ("Talenti con Product Identity nel nome, separati dal "
                      "catalogo OGL (policy 2026-07-26). NON redistribuire."),
            "last_verified": today,
        })
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    lines = ["# Import talenti (sotto-cataloghi per classe) da AoN (2026-07-26)", "",
             f"- Talenti totali: {total}",
             f"- OGL (talents.json): {len(all_entries)}",
             f"- PI -> talents_local.json: {len(local_entries)}",
             f"- Duplicati (pool, name) scartati: {dupes}",
             f"- Entry senza testo: {zero_text}", "",
             "## Conteggi per pool (OGL)", ""]
    lines += [f"- **{pool}**: {by_pool[pool]}" for pool in sorted(by_pool)]
    lines += ["", "## Anomalie", ""] + (anomalies or ["- (nessuna)"])
    lines += ["", "## Fix post-review (2026-07-26, seconda passata)", "",
              "- 9 ki power troncati ai tag `<i>` inline (spell citate nel "
              "testo): il walk ora usa `next_elements` (find_all_next yields "
              "solo Tag, quindi i NavigableString non venivano mai "
              "accumulati). Discriminante entry invariato: `<i>` con "
              "next_sibling che inizia per ':'.",
              "- 3 rogue talent (Black Market Connections, Rumormonger, "
              "Quick Disguise) con `<table class=\"inner\">` appiattita in "
              "coda alla description: tabelle annidate escluse dal testo "
              "(assenza onesta — dato tabellare via reference_url).",
              "- Cleanup punteggiatura del join per frammenti "
              "('dimension door .' -> 'dimension door.') su entrambi i parser.",
              "- Scan finale: 0 description con finale non "
              "'.', '!', '?', '”', '\"', ')'.", ""]
    lines += ["## Nomi PI spostati in locale", ""]
    lines += [f"- {e['mechanics']['pool']} / {e['name']}" for e in local_entries]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scritto: {TALENTS_PATH} ({len(all_entries)} entry)")
    print(f"Scritto: {LOCAL_PATH} ({len(local_entries)} entry, NON committare)")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
