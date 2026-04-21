#!/usr/bin/env python3
"""CLI Expense Tracker — add, list, delete, and summarize expenses stored in JSON."""

import json
import os
import sys
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "expenses.json")


# ── Storage helpers ──────────────────────────────────────────────────────────

def load_expenses() -> list[dict]:
    """Load expenses from JSON file, returning empty list if file absent."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Expected a list at root of expenses.json")
            return data
    except json.JSONDecodeError as e:
        print(f"Error: expenses.json is corrupted ({e}). Starting fresh.")
        return []
    except (OSError, ValueError) as e:
        print(f"Error reading expenses: {e}")
        return []


def save_expenses(expenses: list[dict]) -> None:
    """Persist expenses list to JSON file."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(expenses, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Error saving expenses: {e}")
        sys.exit(1)


def next_id(expenses: list[dict]) -> int:
    return max((e["id"] for e in expenses), default=0) + 1


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_add(args: list[str]) -> None:
    """add <amount> <category> [description]"""
    if len(args) < 2:
        print("Usage: add <amount> <category> [description]")
        print("  e.g. add 12.50 Food 'Lunch at warung'")
        return

    try:
        amount = float(args[0])
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError as e:
        print(f"Error: invalid amount — {e}")
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
    print(f"Added  #{entry['id']:>3}  {entry['date']}  {entry['category']:<14}  Rp {entry['amount']:>10.2f}  {description}")


def cmd_list(args: list[str]) -> None:
    """list [category]"""
    expenses = load_expenses()
    if not expenses:
        print("No expenses recorded yet.")
        return

    if args:
        category = args[0].capitalize()
        expenses = [e for e in expenses if e["category"] == category]
        if not expenses:
            print(f"No expenses in category '{category}'.")
            return

    header = f"{'ID':>4}  {'Date':<12}  {'Category':<14}  {'Amount':>12}  Description"
    print(header)
    print("─" * len(header))
    for e in expenses:
        print(f"{e['id']:>4}  {e['date']:<12}  {e['category']:<14}  Rp {e['amount']:>9.2f}  {e.get('description', '')}")
    print("─" * len(header))
    total = sum(e["amount"] for e in expenses)
    print(f"{'Total':>33}  Rp {total:>9.2f}")


def cmd_delete(args: list[str]) -> None:
    """delete <id>"""
    if not args:
        print("Usage: delete <id>")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        print(f"Error: '{args[0]}' is not a valid ID")
        return

    expenses = load_expenses()
    original_len = len(expenses)
    expenses = [e for e in expenses if e["id"] != target_id]

    if len(expenses) == original_len:
        print(f"No expense found with ID {target_id}")
        return

    save_expenses(expenses)
    print(f"Deleted expense #{target_id}")


def cmd_summary(args: list[str]) -> None:
    """summary [month YYYY-MM]"""
    expenses = load_expenses()
    if not expenses:
        print("No expenses recorded yet.")
        return

    if args and args[0] == "month":
        if len(args) < 2:
            print("Usage: summary month YYYY-MM")
            return
        month = args[1]
        expenses = [e for e in expenses if e["date"].startswith(month)]
        if not expenses:
            print(f"No expenses in {month}.")
            return
        print(f"\nSummary for {month}")
    else:
        print("\nAll-time Summary")

    by_category: dict[str, float] = {}
    for e in expenses:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]

    print(f"\n{'Category':<20}  {'Total':>12}")
    print("─" * 35)
    for cat, total in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"{cat:<20}  Rp {total:>9.2f}")
    print("─" * 35)
    grand = sum(by_category.values())
    print(f"{'TOTAL':<20}  Rp {grand:>9.2f}\n")


def cmd_help(_: list[str]) -> None:
    print("""
CLI Expense Tracker
────────────────────────────────────────────
  add <amount> <category> [description]
      Record a new expense.

  list [category]
      Show all expenses, or filter by category.

  delete <id>
      Remove an expense by its ID.

  summary [month YYYY-MM]
      Totals grouped by category.
      Pass 'month YYYY-MM' to filter by month.

  help
      Show this message.

Examples:
  python expense_tracker.py add 25000 Food "Nasi goreng"
  python expense_tracker.py list
  python expense_tracker.py list Food
  python expense_tracker.py summary
  python expense_tracker.py summary month 2026-04
  python expense_tracker.py delete 3
""")


# ── Entry point ───────────────────────────────────────────────────────────────

COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "delete": cmd_delete,
    "summary": cmd_summary,
    "help": cmd_help,
}


def main() -> None:
    # Ensure UTF-8 output on Windows terminals
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        cmd_help([])
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Unknown command '{command}'. Run 'help' to see available commands.")
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
