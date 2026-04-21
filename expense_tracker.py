#!/usr/bin/env python3
"""CLI Expense Tracker — add, list, edit, delete, summarize, and export expenses."""

import csv
import json
import os
import sys
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "expenses.json")


# ── Color helpers ─────────────────────────────────────────────────────────────

def _supports_color() -> bool:
    """True when the terminal can render ANSI escape codes."""
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        # Windows 10 1511+ supports ANSI in ConHost/WT; check via TERM or WT_SESSION
        return bool(os.environ.get("WT_SESSION") or os.environ.get("TERM"))
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_USE_COLOR = None  # resolved once at first call


def _color(text: str, code: str) -> str:
    global _USE_COLOR
    if _USE_COLOR is None:
        _USE_COLOR = _supports_color()
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:       return _color(text, "1")
def green(text: str) -> str:      return _color(text, "32")
def yellow(text: str) -> str:     return _color(text, "33")
def red(text: str) -> str:        return _color(text, "31")
def cyan(text: str) -> str:       return _color(text, "36")
def dim(text: str) -> str:        return _color(text, "2")


def amount_color(amount: float, text: str) -> str:
    """Color an amount string: green < 50k, yellow < 200k, red >= 200k."""
    if amount >= 200_000:
        return red(text)
    if amount >= 50_000:
        return yellow(text)
    return green(text)


# ── Storage helpers ──────────────────────────────────────────────────────────

def load_expenses() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Expected a list at root of expenses.json")
            return data
    except json.JSONDecodeError as e:
        print(red(f"Error: expenses.json is corrupted ({e}). Starting fresh."))
        return []
    except (OSError, ValueError) as e:
        print(red(f"Error reading expenses: {e}"))
        return []


def save_expenses(expenses: list[dict]) -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(expenses, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(red(f"Error saving expenses: {e}"))
        sys.exit(1)


def next_id(expenses: list[dict]) -> int:
    return max((e["id"] for e in expenses), default=0) + 1


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_add(args: list[str]) -> None:
    """add <amount> <category> [description]"""
    if len(args) < 2:
        print(f"Usage: add <amount> <category> [description]")
        print(f"  e.g. add 12.50 Food 'Lunch at warung'")
        return

    try:
        amount = float(args[0])
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError as e:
        print(red(f"Error: invalid amount — {e}"))
        return

    category = args[1].capitalize()
    description = " ".join(args[2:]) if len(args) > 2 else ""

    expenses = load_expenses()
    entry = {
        "id": next_id(expenses),
        "date": str(date.today()),
        "amount": round(amount, 2),
        "category": category,
        "description": description,
    }
    expenses.append(entry)
    save_expenses(expenses)

    amt_str = amount_color(entry["amount"], f"Rp {entry['amount']:>10.2f}")
    print(f"{green('Added')}  #{entry['id']:>3}  {entry['date']}  {cyan(entry['category']):<23}  {amt_str}  {dim(description)}")


def cmd_edit(args: list[str]) -> None:
    """edit <id> [amount] [category] [description]

    Fields to update are positional. Use '-' to keep a field unchanged.
      edit 2 35000 - "Updated description"
      edit 2 - Coffee
      edit 2 35000 Coffee "New description"
    """
    if len(args) < 2:
        print("Usage: edit <id> [amount|-] [category|-] [description|-]")
        print("  Use '-' to keep a field unchanged.")
        print("  e.g. edit 2 35000 - 'Fixed amount'")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        print(red(f"Error: '{args[0]}' is not a valid ID"))
        return

    expenses = load_expenses()
    target = next((e for e in expenses if e["id"] == target_id), None)
    if target is None:
        print(red(f"No expense found with ID {target_id}"))
        return

    # Parse each optional field; '-' means keep existing value
    new_amount = target["amount"]
    new_category = target["category"]
    new_description = target["description"]

    if len(args) > 1 and args[1] != "-":
        try:
            new_amount = float(args[1])
            if new_amount <= 0:
                raise ValueError("Amount must be positive")
            new_amount = round(new_amount, 2)
        except ValueError as e:
            print(red(f"Error: invalid amount — {e}"))
            return

    if len(args) > 2 and args[2] != "-":
        new_category = args[2].capitalize()

    if len(args) > 3 and args[3] != "-":
        new_description = " ".join(args[3:])

    target["amount"] = new_amount
    target["category"] = new_category
    target["description"] = new_description

    save_expenses(expenses)
    amt_str = amount_color(new_amount, f"Rp {new_amount:>10.2f}")
    print(f"{yellow('Updated')}  #{target_id:>3}  {target['date']}  {cyan(new_category):<23}  {amt_str}  {dim(new_description)}")


def cmd_list(args: list[str]) -> None:
    """list [category]"""
    expenses = load_expenses()
    if not expenses:
        print(dim("No expenses recorded yet."))
        return

    if args:
        category = args[0].capitalize()
        expenses = [e for e in expenses if e["category"] == category]
        if not expenses:
            print(dim(f"No expenses in category '{category}'."))
            return

    sep = "─" * 64
    header = f"{'ID':>4}  {'Date':<12}  {'Category':<14}  {'Amount':>12}  Description"
    print(bold(header))
    print(dim(sep))
    for e in expenses:
        amt_str = amount_color(e["amount"], f"Rp {e['amount']:>9.2f}")
        print(f"{e['id']:>4}  {e['date']:<12}  {cyan(e['category']):<23}  {amt_str}  {dim(e.get('description', ''))}")
    print(dim(sep))
    total = sum(e["amount"] for e in expenses)
    total_str = amount_color(total, f"Rp {total:>9.2f}")
    print(f"{bold('Total'):>38}  {total_str}")


def cmd_delete(args: list[str]) -> None:
    """delete <id>"""
    if not args:
        print("Usage: delete <id>")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        print(red(f"Error: '{args[0]}' is not a valid ID"))
        return

    expenses = load_expenses()
    original_len = len(expenses)
    expenses = [e for e in expenses if e["id"] != target_id]

    if len(expenses) == original_len:
        print(red(f"No expense found with ID {target_id}"))
        return

    save_expenses(expenses)
    print(red(f"Deleted") + f" expense #{target_id}")


def cmd_summary(args: list[str]) -> None:
    """summary [month YYYY-MM]"""
    expenses = load_expenses()
    if not expenses:
        print(dim("No expenses recorded yet."))
        return

    if args and args[0] == "month":
        if len(args) < 2:
            print("Usage: summary month YYYY-MM")
            return
        month = args[1]
        expenses = [e for e in expenses if e["date"].startswith(month)]
        if not expenses:
            print(dim(f"No expenses in {month}."))
            return
        print(f"\n{bold(f'Summary for {month}')}")
    else:
        print(f"\n{bold('All-time Summary')}")

    by_category: dict[str, float] = {}
    for e in expenses:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]

    sep = "─" * 36
    col_header = f"{'Category':<20}  {'Total':>12}"
    print(f"\n{bold(col_header)}")
    print(dim(sep))
    for cat, total in sorted(by_category.items(), key=lambda x: -x[1]):
        amt_str = amount_color(total, f"Rp {total:>9.2f}")
        print(f"{cyan(cat):<29}  {amt_str}")
    print(dim(sep))
    grand = sum(by_category.values())
    grand_str = amount_color(grand, f"Rp {grand:>9.2f}")
    print(f"{bold('TOTAL'):<20}  {' ' * 9}{grand_str}\n")


def cmd_export(args: list[str]) -> None:
    """export [filename.csv]

    Exports all expenses to a CSV file (default: expenses.csv).
    Opens cleanly in Excel and Google Sheets.
    """
    filename = args[0] if args else "expenses.csv"
    if not filename.endswith(".csv"):
        filename += ".csv"

    output_path = os.path.join(os.path.dirname(__file__), filename)
    expenses = load_expenses()

    if not expenses:
        print(dim("No expenses to export."))
        return

    try:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            # utf-8-sig writes the BOM that Excel needs to detect UTF-8 correctly
            writer = csv.DictWriter(f, fieldnames=["id", "date", "amount", "category", "description"])
            writer.writeheader()
            writer.writerows(expenses)
    except OSError as e:
        print(red(f"Error writing CSV: {e}"))
        return

    print(f"{green('Exported')} {len(expenses)} expense(s) → {bold(filename)}")


def cmd_help(_: list[str]) -> None:
    print(f"""
{bold('CLI Expense Tracker')}
{'─' * 44}
  {cyan('add')} <amount> <category> [description]
      Record a new expense.

  {cyan('edit')} <id> [amount|-] [category|-] [description|-]
      Update a field on an existing expense.
      Use '-' to keep a field unchanged.

  {cyan('list')} [category]
      Show all expenses, or filter by category.

  {cyan('delete')} <id>
      Remove an expense by its ID.

  {cyan('summary')} [month YYYY-MM]
      Totals grouped by category.

  {cyan('export')} [filename.csv]
      Export all expenses to CSV (default: expenses.csv).

  {cyan('help')}
      Show this message.

{bold('Examples:')}
  python expense_tracker.py add 25000 Food "Nasi goreng"
  python expense_tracker.py edit 2 35000 - "Fixed amount"
  python expense_tracker.py list
  python expense_tracker.py list Food
  python expense_tracker.py summary month 2026-04
  python expense_tracker.py export april.csv
  python expense_tracker.py delete 3

{dim('Amount colors: green < 50k  |  yellow < 200k  |  red >= 200k')}
""")


# ── Entry point ───────────────────────────────────────────────────────────────

COMMANDS = {
    "add": cmd_add,
    "edit": cmd_edit,
    "list": cmd_list,
    "delete": cmd_delete,
    "summary": cmd_summary,
    "export": cmd_export,
    "help": cmd_help,
}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        cmd_help([])
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    handler = COMMANDS.get(command)
    if handler is None:
        print(red(f"Unknown command '{command}'.") + " Run 'help' to see available commands.")
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
