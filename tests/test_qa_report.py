import importlib.util
import json
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/qa_report.py"
spec = importlib.util.spec_from_file_location("qa_report", MODULE_PATH)
qa_report = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = qa_report
spec.loader.exec_module(qa_report)

RigQAReport = qa_report.RigQAReport
save_qa_report = qa_report.save_qa_report


def test_save_qa_report_writes_expected_json_fields(tmp_path):
    report = RigQAReport(
        mesh_count=2,
        vertex_count=128,
        bone_count=17,
        unweighted_vertices=3,
        over_limit_vertices=4,
        warnings=("Missing preview",),
        errors=("No export path",),
    )
    output_path = tmp_path / "qa_report.json"

    save_qa_report(report, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload == {
        "mesh_count": 2,
        "vertex_count": 128,
        "bone_count": 17,
        "unweighted_vertices": 3,
        "over_limit_vertices": 4,
        "warnings": ["Missing preview"],
        "errors": ["No export path"],
    }
