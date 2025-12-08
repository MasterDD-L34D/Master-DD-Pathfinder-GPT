import json
from pathlib import Path

from tools.generate_build_db import review_local_database


def test_review_local_database_reports_status(tmp_path):
    build_dir = tmp_path / "builds"
    build_dir.mkdir()

    valid_payload = json.loads(Path("src/data/builds/alchemist.json").read_text(encoding="utf-8"))
    (build_dir / "valid.json").write_text(json.dumps(valid_payload), encoding="utf-8")
    (build_dir / "invalid.json").write_text(json.dumps({"build_state": {}}), encoding="utf-8")

    module_dir = tmp_path / "modules"
    module_dir.mkdir()
    module_file = module_dir / "sample.txt"
    module_file.write_text("contenuto", encoding="utf-8")

    module_index_path = tmp_path / "module_index.json"
    module_index_path.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "module": "sample.txt",
                        "file": str(module_file),
                        "meta": {
                            "name": "sample.txt",
                            "size_bytes": module_file.stat().st_size,
                            "suffix": ".txt",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    output_report = tmp_path / "review.json"
    report = review_local_database(
        build_dir,
        module_dir,
        module_index_path=module_index_path,
        strict=False,
        output_path=output_report,
    )

    assert output_report.is_file()
    assert report["builds"]["total"] == 2
    assert report["builds"]["valid"] == 1
    assert report["builds"]["invalid"] == 1
    assert report["modules"]["valid"] == 1
    assert report["modules"]["invalid"] == 0
