import json
from pathlib import Path

import apply

ROOT = Path(__file__).resolve().parents[1]
FACTS = apply.yaml.safe_load((ROOT / "profile/facts.example.yaml").read_text())


def spec(name):
    return json.loads((ROOT / "jobs" / name).read_text())


def test_good_example_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(apply, "APPLIED", tmp_path / "applied.csv")
    errors, _ = apply.check_spec(spec("example_harbourview.json"), FACTS)
    assert errors == []


def test_negation_is_allowed():
    s = {"company": "X Clinic", "letter": ["I'm applying to X Clinic. I am not a certified dental assistant."]}
    errors, _ = apply.check_spec(s, FACTS)
    assert errors == []


def test_false_claims_blocked(tmp_path, monkeypatch):
    applied = tmp_path / "applied.csv"
    applied.write_text("date,company,title,source,category,status,status_date,note\n"
                       "2026-10-01,Harbourview Physiotherapy,Clinic Coordinator,,,applied,2026-10-01,\n")
    monkeypatch.setattr(apply, "APPLIED", applied)
    errors, _ = apply.check_spec(spec("example_bad.json"), FACTS)
    text = " ".join(errors)
    assert "certified dental assistant" in text and "quickbooks" in text and "fluent french" in text
    assert "not in your fact bank" in text
    assert "Harbourview Physiotherapy" in text


def test_bullet_index_and_unknown_id():
    errors, _ = apply.check_spec({"company": "Y", "bullets": {"brightsmile": [0, 99], "ghost": [0]}}, FACTS)
    assert any("out of range" in e for e in errors)
    assert any('unknown experience id "ghost"' in e for e in errors)
