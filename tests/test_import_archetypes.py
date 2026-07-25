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
