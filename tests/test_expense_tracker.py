"""Unit tests for CLI Expense Tracker."""

import csv
import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

import expense_tracker as et


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_data_file(tmp_path, monkeypatch):
    monkeypatch.setattr(et, "DATA_FILE", str(tmp_path / "expenses.json"))
    monkeypatch.setattr(et, "_USE_COLOR", False)  # disable ANSI codes in tests


def _run(*argv):
    return et.build_parser().parse_args(list(argv))


def _seed(amount=10000.0, category="Food", description="Test"):
    et.cmd_add(_run("add", str(amount), category, description))


# ── load / save ───────────────────────────────────────────────────────────────

def test_load_empty():
    assert et.load_expenses() == []


def test_save_and_load():
    expenses = [{"id": 1, "date": "2026-04-24", "amount": 10.0, "category": "Food", "description": ""}]
    et.save_expenses(expenses)
    assert et.load_expenses() == expenses


def test_load_corrupted_json(tmp_path, monkeypatch, capsys):
    f = tmp_path / "bad.json"
    f.write_text("NOT JSON")
    monkeypatch.setattr(et, "DATA_FILE", str(f))
    assert et.load_expenses() == []
    assert "corrupted" in capsys.readouterr().out


def test_next_id_empty():
    assert et.next_id([]) == 1


def test_next_id_existing():
    assert et.next_id([{"id": 3}, {"id": 7}, {"id": 2}]) == 8


# ── add ───────────────────────────────────────────────────────────────────────

def test_add_basic(capsys):
    et.cmd_add(_run("add", "25000", "Food", "Lunch"))
    expenses = et.load_expenses()
    assert len(expenses) == 1
    assert expenses[0]["amount"] == 25000.0
    assert expenses[0]["category"] == "Food"
    assert expenses[0]["description"] == "Lunch"
    assert "Added" in capsys.readouterr().out


def test_add_no_description():
    et.cmd_add(_run("add", "5000", "Transport"))
    assert et.load_expenses()[0]["description"] == ""


def test_add_category_capitalized():
    et.cmd_add(_run("add", "1000", "coffee"))
    assert et.load_expenses()[0]["category"] == "Coffee"


def test_add_negative_amount_exits():
    with pytest.raises(SystemExit):
        et.cmd_add(_run("add", "-100", "Food"))


def test_add_increments_id():
    for i in range(3):
        _seed()
    assert [e["id"] for e in et.load_expenses()] == [1, 2, 3]


# ── edit ──────────────────────────────────────────────────────────────────────

def test_edit_amount():
    _seed()
    et.cmd_edit(_run("edit", "1", "--amount", "99000"))
    assert et.load_expenses()[0]["amount"] == 99000.0


def test_edit_category():
    _seed()
    et.cmd_edit(_run("edit", "1", "--category", "transport"))
    assert et.load_expenses()[0]["category"] == "Transport"


def test_edit_description():
    _seed()
    et.cmd_edit(_run("edit", "1", "--description", "Updated"))
    assert et.load_expenses()[0]["description"] == "Updated"


def test_edit_missing_id_exits():
    with pytest.raises(SystemExit):
        et.cmd_edit(_run("edit", "999", "--amount", "1000"))


def test_edit_negative_amount_exits():
    _seed()
    with pytest.raises(SystemExit):
        et.cmd_edit(_run("edit", "1", "--amount", "-500"))


# ── delete ────────────────────────────────────────────────────────────────────

def test_delete_existing(capsys):
    _seed()
    et.cmd_delete(_run("delete", "1"))
    assert et.load_expenses() == []
    assert "Deleted" in capsys.readouterr().out


def test_delete_missing_exits():
    with pytest.raises(SystemExit):
        et.cmd_delete(_run("delete", "42"))


# ── list ──────────────────────────────────────────────────────────────────────

def test_list_empty(capsys):
    et.cmd_list(_run("list"))
    assert "No expenses" in capsys.readouterr().out


def test_list_all(capsys):
    _seed(category="Food")
    _seed(category="Transport")
    et.cmd_list(_run("list"))
    out = capsys.readouterr().out
    assert "Food" in out and "Transport" in out


def test_list_filter_category(capsys):
    _seed(category="Food")
    _seed(category="Transport")
    capsys.readouterr()  # discard seed output
    et.cmd_list(_run("list", "food"))
    out = capsys.readouterr().out
    assert "Food" in out and "Transport" not in out


def test_list_filter_month(capsys):
    _seed(category="Food")
    expenses = et.load_expenses()
    expenses[0]["date"] = "2025-01-15"
    et.save_expenses(expenses)
    et.cmd_list(_run("list", "--month", "2025-01"))
    assert "2025-01-15" in capsys.readouterr().out


# ── list sort / limit ────────────────────────────────────────────────────────

def test_list_sort_by_amount():
    _seed(amount=5000, category="Food")
    _seed(amount=50000, category="Transport")
    _seed(amount=1000, category="Coffee")
    expenses_after_sort = []
    original_print = et._print_table

    def capture(rows):
        expenses_after_sort.extend(rows)
    et._print_table = capture
    try:
        et.cmd_list(_run("list", "--sort", "amount"))
    finally:
        et._print_table = original_print

    amounts = [e["amount"] for e in expenses_after_sort]
    assert amounts == sorted(amounts, reverse=True)


def test_list_sort_by_category():
    _seed(category="Transport")
    _seed(category="Food")
    _seed(category="Coffee")
    captured = []

    def capture(rows):
        captured.extend(rows)
    et._print_table, orig = capture, et._print_table
    try:
        et.cmd_list(_run("list", "--sort", "category"))
    finally:
        et._print_table = orig

    cats = [e["category"] for e in captured]
    assert cats == sorted(cats)


def test_list_limit():
    for i in range(5):
        _seed(amount=(i + 1) * 1000)
    captured = []

    def capture(rows):
        captured.extend(rows)
    et._print_table, orig = capture, et._print_table
    try:
        et.cmd_list(_run("list", "--limit", "3"))
    finally:
        et._print_table = orig

    assert len(captured) == 3


# ── search ────────────────────────────────────────────────────────────────────

def test_search_by_description(capsys):
    _seed(description="Nasi goreng")
    _seed(description="Grab ride")
    capsys.readouterr()
    et.cmd_search(_run("search", "goreng"))
    out = capsys.readouterr().out
    assert "Nasi goreng" in out and "Grab ride" not in out


def test_search_by_category(capsys):
    _seed(category="Coffee")
    _seed(category="Food")
    capsys.readouterr()
    et.cmd_search(_run("search", "coffee"))
    out = capsys.readouterr().out
    assert "Coffee" in out and "Food" not in out


def test_search_no_match(capsys):
    _seed(description="Nasi goreng")
    et.cmd_search(_run("search", "pizza"))
    assert "No expenses matching" in capsys.readouterr().out


# ── summary ───────────────────────────────────────────────────────────────────

def test_summary_empty(capsys):
    et.cmd_summary(_run("summary"))
    assert "No expenses" in capsys.readouterr().out


def test_summary_groups_by_category(capsys):
    _seed(amount=10000, category="Food")
    _seed(amount=50000, category="Transport")
    et.cmd_summary(_run("summary"))
    out = capsys.readouterr().out
    assert "Food" in out and "Transport" in out


def test_summary_month_filter(capsys):
    _seed()
    expenses = et.load_expenses()
    expenses[0]["date"] = "2025-03-10"
    et.save_expenses(expenses)
    et.cmd_summary(_run("summary", "--month", "2025-03"))
    assert "2025-03" in capsys.readouterr().out


# ── export / import ───────────────────────────────────────────────────────────

def test_export_creates_csv(tmp_path, monkeypatch):
    _seed(amount=15000, category="Food", description="Lunch")
    csv_path = str(tmp_path / "out.csv")
    et.cmd_export(_run("export", csv_path))
    assert os.path.exists(csv_path)
    content = open(csv_path, encoding="utf-8-sig").read()
    assert "Food" in content and "15000" in content


def test_export_empty(capsys):
    et.cmd_export(_run("export"))
    assert "No expenses" in capsys.readouterr().out


def test_import_roundtrip(tmp_path, capsys):
    _seed(amount=25000, category="Food", description="Lunch")
    csv_path = str(tmp_path / "backup.csv")
    et.cmd_export(_run("export", csv_path))
    et.save_expenses([])
    capsys.readouterr()  # discard seed/export output
    et.cmd_import(_run("import", csv_path))
    restored = et.load_expenses()
    assert len(restored) == 1
    assert restored[0]["amount"] == 25000.0
    assert restored[0]["category"] == "Food"
    assert "Imported 1" in capsys.readouterr().out


def test_import_missing_file_exits():
    with pytest.raises(SystemExit):
        et.cmd_import(_run("import", "/nonexistent/path.csv"))
