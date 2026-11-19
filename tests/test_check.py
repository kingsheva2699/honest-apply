import argparse
import json
from pathlib import Path

import pytest

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



@pytest.fixture
def exact_facts():
    return {"name": "Example", "experience": [
        {"id": "office", "company": "Example Co", "title": "Coordinator",
         "bullets": ["Scheduled 60 appointments per week.", "Handled invoices."]},
        {"id": "other", "company": "Other Co", "title": "Assistant",
         "bullets": ["Packed orders."]},
    ]}


@pytest.mark.parametrize("bullet", [
    "Scheduled 600 appointments per week.",
    "scheduled 60 appointments per week.",
    "Scheduled 60 appointments per week. ",
    "Packed orders.", True, False, 0.0, None, {}, [], -1, 2,
])
def test_inexact_or_invalid_selection_rejected(exact_facts, bullet):
    errors, _ = apply.check_spec({"bullets": {"office": [bullet]}}, exact_facts)
    assert errors
    with pytest.raises(ValueError):
        apply.resume_html({"bullets": {"office": [bullet]}}, exact_facts)


@pytest.mark.parametrize("bullets", [[], False, "", 0, {"office": None}, {"office": "Handled invoices."},
                                    {"office": 0}, {"office": {}}, {"missing": [0]}])
def test_invalid_selection_containers_rejected(exact_facts, bullets):
    assert apply.check_spec({"bullets": bullets}, exact_facts)[0]


@pytest.mark.parametrize("bullets", [{"office": [0, 1]}, {"office": ["Scheduled 60 appointments per week.", "Handled invoices."]}])
def test_exact_text_and_indices_render_identically(exact_facts, bullets):
    spec = {"bullets": bullets}
    assert apply.check_spec(spec, exact_facts)[0] == []
    assert apply.resume_html(spec, exact_facts) == apply.resume_html(
        {"bullets": {"office": [0, 1]}}, exact_facts)


@pytest.mark.parametrize("spec", [{}, {"bullets": None}, {"bullets": {}}, {"bullets": {"office": []}}])
def test_default_and_empty_selections_remain_supported(exact_facts, spec):
    assert apply.check_spec(spec, exact_facts)[0] == []
    result = apply.resume_html(spec, exact_facts)
    assert ("Scheduled 60 appointments" in result) == (spec.get("bullets") != {"office": []})


def test_legacy_threshold_cannot_enable_fuzzy_match(exact_facts):
    exact_facts["bullet_match_threshold"] = 0
    assert apply.check_spec({"bullets": {"office": ["Scheduled 600 appointments per week."]}}, exact_facts)[0]


@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("bullet", ["Scheduled 600 appointments per week.", True, -1, 2])
def test_build_blocks_invalid_selection_even_with_force(tmp_path, monkeypatch, exact_facts, force, bullet):
    monkeypatch.setattr(apply, "load_facts", lambda: exact_facts)
    monkeypatch.setattr(apply, "OUT", tmp_path / "out")
    monkeypatch.setattr(apply, "APPLIED", tmp_path / "applied.csv")
    path = tmp_path / "job.json"
    path.write_text(json.dumps({"company": "Example", "bullets": {"office": [bullet]}}))
    assert apply.cmd_build(argparse.Namespace(spec=[str(path)], force=force)) == 1
    assert not apply.OUT.exists()


def test_build_exact_selection_and_legacy_soft_override(tmp_path, monkeypatch, exact_facts):
    exact_facts["never_claim"] = ["certified"]
    monkeypatch.setattr(apply, "load_facts", lambda: exact_facts)
    monkeypatch.setattr(apply, "OUT", tmp_path / "out")
    monkeypatch.setattr(apply, "APPLIED", tmp_path / "applied.csv")
    monkeypatch.setattr(apply, "to_pdf", lambda *args: "")
    path = tmp_path / "job.json"
    path.write_text(json.dumps({"company": "Example", "headline": "Certified",
                               "bullets": {"office": [0]}, "letter": ["Example application."]}))
    assert apply.cmd_build(argparse.Namespace(spec=[str(path)], force=False)) == 1
    assert apply.cmd_build(argparse.Namespace(spec=[str(path)], force=True)) == 0
    assert "Scheduled 60 appointments per week." in (apply.OUT / "Example/resume.html").read_text()
