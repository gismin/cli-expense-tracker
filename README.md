# CLI Expense Tracker

A beginner Python project — a command-line expense tracker that reads and writes to a local JSON file.

## Features

- **Add** expenses with amount, category, and optional description
- **Edit** any field on an existing expense by ID (use `-` to keep a field unchanged)
- **List** all expenses or filter by category
- **Delete** expenses by ID
- **Summarize** spending grouped by category (all-time or by month)
- **Export** to CSV — opens directly in Excel and Google Sheets
- Color-coded amounts: green (< 50k) · yellow (< 200k) · red (≥ 200k)
- Stores data locally in `expenses.json`
- Handles all errors gracefully with `try/except`

## Usage

```bash
# Add an expense
python expense_tracker.py add 25000 Food "Nasi goreng"
python expense_tracker.py add 150000 Transport "Grab to office"

# Edit an expense — use '-' to keep a field unchanged
python expense_tracker.py edit 2 35000 - "Updated description"   # change amount + desc
python expense_tracker.py edit 2 - Coffee                        # change only category

# List all expenses
python expense_tracker.py list

# List by category
python expense_tracker.py list Food

# Summary (all-time)
python expense_tracker.py summary

# Summary for a specific month
python expense_tracker.py summary month 2026-04

# Export to CSV (default: expenses.csv)
python expense_tracker.py export
python expense_tracker.py export april.csv

# Delete an expense by ID
python expense_tracker.py delete 3

# Help
python expense_tracker.py help
```

## Sample Output

```
$ python expense_tracker.py list

  ID  Date          Category        Amount        Description
──────────────────────────────────────────────────────────────
   1  2026-04-22    Food             Rp  25000.00  Nasi goreng
   2  2026-04-22    Transport        Rp 150000.00  Grab to office
──────────────────────────────────────────────────────────────
                                Total  Rp 175000.00
```

```
$ python expense_tracker.py summary

All-time Summary

Category              Total
───────────────────────────────────
Transport             Rp 150000.00
Food                  Rp  25000.00
───────────────────────────────────
TOTAL                 Rp 175000.00
```

## Data Storage

Expenses are saved in `expenses.json` in the same directory as the script. The file is excluded from git (`.gitignore`) to keep personal finance data private.

## Requirements

- Python 3.10+ (uses `list[dict]` type hints)
- No external dependencies — standard library only

## Project Structure

```
CLI Expense Tracker/
├── expense_tracker.py   ← main application
├── expenses.json        ← data file (auto-created, git-ignored)
├── .gitignore
└── README.md
```

## What I Learned

- Reading and writing JSON files with `json.load` / `json.dump`
- Writing CSV files with the `csv` module (`utf-8-sig` BOM for Excel compatibility)
- Error handling with `try/except` for file I/O and user input
- Parsing command-line arguments from `sys.argv`
- ANSI escape codes for terminal colors (with graceful fallback on unsupported terminals)
- Organizing code into focused functions with a dispatch dict instead of `if/elif`
- Using `.gitignore` to protect personal data
