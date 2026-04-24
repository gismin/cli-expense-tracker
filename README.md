# CLI Expense Tracker

A Python CLI project — a command-line expense tracker that reads and writes to a local JSON file.

## Features

- **Add** expenses with amount, category, and optional description
- **Edit** any field on an existing expense with named flags (`--amount`, `--category`, `--description`)
- **List** all expenses, or filter by category and/or month
- **Search** expenses by keyword (matches description or category)
- **Delete** expenses by ID
- **Summarize** spending grouped by category — all-time or filtered by month, with average per entry
- **Export** to CSV — opens directly in Excel and Google Sheets
- **Import** from a CSV file (complements export for backup/restore)
- Color-coded amounts: green (< 50k) · yellow (< 200k) · red (≥ 200k)
- Proper `argparse` CLI with subcommands and built-in `--help` for every command
- Stores data locally in `expenses.json`
- 31 unit tests, zero external dependencies

## Installation (optional)

Install as a command so you can run `expense-tracker` from anywhere:

```bash
pip install -e .
expense-tracker --help
```

Or just run the script directly:

```bash
python expense_tracker.py --help
```

## Usage

```bash
# Add an expense
python expense_tracker.py add 25000 Food "Nasi goreng"
python expense_tracker.py add 150000 Transport "Grab to office"

# Edit with named flags — only specify what you want to change
python expense_tracker.py edit 2 --amount 35000
python expense_tracker.py edit 2 --category Coffee
python expense_tracker.py edit 2 --amount 35000 --description "Updated"

# List all expenses
python expense_tracker.py list

# List by category
python expense_tracker.py list Food

# List by month
python expense_tracker.py list --month 2026-04

# Search by keyword (description or category)
python expense_tracker.py search goreng
python expense_tracker.py search transport

# Summary (all-time)
python expense_tracker.py summary

# Summary for a specific month
python expense_tracker.py summary --month 2026-04

# Export to CSV (default: expenses.csv)
python expense_tracker.py export
python expense_tracker.py export april.csv

# Import from a CSV
python expense_tracker.py import april.csv

# Delete an expense by ID
python expense_tracker.py delete 3
```

## Sample Output

```
$ python expense_tracker.py list

  ID  Date          Category              Amount  Description
────────────────────────────────────────────────────────────────────
   1  2026-04-22    Food             Rp  25000.00  Nasi goreng
   2  2026-04-22    Transport        Rp 150000.00  Grab to office
────────────────────────────────────────────────────────────────────
                         Total  Rp 175000.00
```

```
$ python expense_tracker.py summary --month 2026-04

Summary for 2026-04

Category              Total
────────────────────────────────────
Transport             Rp 150000.00
Food                  Rp  25000.00
────────────────────────────────────
TOTAL                  Rp 175000.00
avg/entry              Rp  87500.00
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Data Storage

Expenses are saved in `expenses.json` in the same directory as the script. The file is excluded from git (`.gitignore`) to keep personal finance data private.

## Requirements

- Python 3.10+ (uses `list[dict]` type hints)
- No runtime dependencies — standard library only
- `pytest` for running tests (dev dependency)

## Project Structure

```
cli-expense-tracker/
├── expense_tracker.py   ← main application
├── pyproject.toml       ← packaging config (pip install -e .)
├── tests/
│   └── test_expense_tracker.py  ← 31 unit tests
├── expenses.json        ← data file (auto-created, git-ignored)
├── .gitignore
└── README.md
```

## What I Learned

- Reading and writing JSON files with `json.load` / `json.dump`
- Writing CSV files with the `csv` module (`utf-8-sig` BOM for Excel compatibility)
- Error handling with `try/except` for file I/O and user input
- Building a proper CLI with `argparse` subcommands (instead of manual `sys.argv` parsing)
- ANSI escape codes for terminal colors (with graceful fallback on unsupported terminals)
- Packaging a Python script with `pyproject.toml` so it's installable via `pip`
- Writing unit tests with `pytest` — fixtures, `monkeypatch`, `capsys`, `tmp_path`
- Organizing code into focused functions with a dispatch dict instead of `if/elif`
- Using `.gitignore` to protect personal data
