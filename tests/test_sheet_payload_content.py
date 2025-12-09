import json
from pathlib import Path


BUILD_DIR = Path("src/data/builds")


def _load_sheet(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    export = payload.get("export") or {}
    return export.get("sheet_payload") or {}


def test_skills_equip_ledger_sections_are_populated():
    for build_file in BUILD_DIR.glob("*.json"):
        sheet = _load_sheet(build_file)
        skills = sheet.get("skills") or []
        equip = sheet.get("equipaggiamento") or []
        ledger = sheet.get("ledger") or {}
        ledger_mov = sheet.get("ledger_movimenti") or ledger.get("movimenti") or []

        assert skills, f"Skills mancanti in {build_file.name}"
        assert equip, f"Equipaggiamento mancante in {build_file.name}"
        assert ledger_mov, f"Movimenti ledger mancanti in {build_file.name}"

        sheet_md = sheet.get("sheet_markdown", "")
        assert skills[0].get("nome") in sheet_md
        assert equip[0] in sheet_md
        assert str(ledger_mov[0].get("oggetto")) in sheet_md
