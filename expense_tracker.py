#!/usr/bin/env python3
"""CLI Expense Tracker — add, list, search, edit, delete, summarize, and export expenses."""

import argparse
import csv
import json
import os
import sys
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "expenses.json")


# ── Color helpers ─────────────────────────────────────────────────────────────

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        return bool(os.environ.get("WT_SESSION") or os.environ.get("TERM"))
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_USE_COLOR: bool | None = None


def _color(text: str, code: str) -> str:
    global _USE_COLOR
    if _USE_COLOR is None:
        _USE_COLOR = _supports_color()
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:   return _color(text, "1")
def green(text: str) -> str:  return _color(text, "32")
def yellow(text: str) -> str: return _color(text, "33")
def red(text: str) -> str:    return _color(text, "31")
def cyan(text: str) -> str:   return _color(text, "36")
def dim(text: str) -> str:    return _color(text, "2")


def amount_color(amount: float, text: str) -> str:
    """Color an amount: green < 50k, yellow < 200k, red >= 200k."""
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


def _print_table(expenses: list[dict]) -> None:
    sep = "─" * 68
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


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_add(args: argparse.Namespace) -> None:
    if args.amount <= 0:
        print(red("Error: amount must be positive"))
        sys.exit(1)

    expenses = load_expenses()
    entry = {
        "id": next_id(expenses),
        "date": str(date.today()),
        "amount": round(args.amount, 2),
        "category": args.category.capitalize(),
        "description": args.description or "",
    }
    expenses.append(entry)
    save_expenses(expenses)

    amt_str = amount_color(entry["amount"], f"Rp {entry['amount']:>10.2f}")
    print(f"{green('Added')}  #{entry['id']:>3}  {entry['date']}  {cyan(entry['category']):<23}  {amt_str}  {dim(entry['description'])}")


def cmd_edit(args: argparse.Namespace) -> None:
    expenses = load_expenses()
    target = next((e for e in expenses if e["id"] == args.id), None)
    if target is None:
        print(red(f"No expense found with ID {args.id}"))
        sys.exit(1)

    if args.amount is not None:
        if args.amount <= 0:
            print(red("Error: amount must be positive"))
            sys.exit(1)
        target["amount"] = round(args.amount, 2)
    if args.category is not None:
        target["category"] = args.category.capitalize()
    if args.description is not None:
        target["description"] = args.description

    save_expenses(expenses)
    amt_str = amount_color(target["amount"], f"Rp {target['amount']:>10.2f}")
    print(f"{yellow('Updated')}  #{target['id']:>3}  {target['date']}  {cyan(target['category']):<23}  {amt_str}  {dim(target['description'])}")


def cmd_list(args: argparse.Namespace) -> None:
    expenses = load_expenses()
    if not expenses:
        print(dim("No expenses recorded yet."))
        return

    if args.category:
        expenses = [e for e in expenses if e["category"] == args.category.capitalize()]
        if not expenses:
            print(dim(f"No expenses in category '{args.category}'."))
            return

    if args.month:
        expenses = [e for e in expenses if e["date"].startswith(args.month)]
        if not expenses:
            print(dim(f"No expenses in {args.month}."))
            return

    sort_key = args.sort or "date"
    reverse = sort_key == "amount"
    expenses = sorted(expenses, key=lambda e: e[sort_key], reverse=reverse)

    if args.limit:
        expenses = expenses[: args.limit]

    _print_table(expenses)


def cmd_search(args: argparse.Namespace) -> None:
    expenses = load_expenses()
    keyword = args.keyword.lower()
    matches = [
        e for e in expenses
        if keyword in e.get("description", "").lower()
        or keyword in e["category"].lower()
    ]
    if not matches:
        print(dim(f"No expenses matching '{args.keyword}'."))
        return
    _print_table(matches)


def cmd_delete(args: argparse.Namespace) -> None:
    expenses = load_expenses()
    original_len = len(expenses)
    expenses = [e for e in expenses if e["id"] != args.id]

    if len(expenses) == original_len:
        print(red(f"No expense found with ID {args.id}"))
        sys.exit(1)

    save_expenses(expenses)
    print(red("Deleted") + f" expense #{args.id}")


def cmd_summary(args: argparse.Namespace) -> None:
    expenses = load_expenses()
    if not expenses:
        print(dim("No expenses recorded yet."))
        return

    if args.month:
        expenses = [e for e in expenses if e["date"].startswith(args.month)]
        if not expenses:
            print(dim(f"No expenses in {args.month}."))
            return
        print(f"\n{bold(f'Summary for {args.month}')}")
    else:
        print(f"\n{bold('All-time Summary')}")

    by_category: dict[str, float] = {}
    for e in expenses:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]

    sep = "─" * 36
    print(f"\n{bold('Category'):<20}  {bold('Total'):>12}")
    print(dim(sep))
    for cat, total in sorted(by_category.items(), key=lambda x: -x[1]):
        amt_str = amount_color(total, f"Rp {total:>9.2f}")
        print(f"{cyan(cat):<29}  {amt_str}")
    print(dim(sep))
    grand = sum(by_category.values())
    count = len(expenses)
    avg = grand / count if count else 0
    grand_str = amount_color(grand, f"Rp {grand:>9.2f}")
    avg_str = amount_color(avg, f"Rp {avg:>9.2f}")
    print(f"{bold('TOTAL'):<20}  {' ' * 9}{grand_str}")
    print(f"{dim('avg/entry'):<20}  {' ' * 9}{dim(avg_str)}\n")


def cmd_export(args: argparse.Namespace) -> None:
    filename = args.filename or "expenses.csv"
    if not filename.endswith(".csv"):
        filename += ".csv"

    output_path = os.path.join(os.path.dirname(__file__), filename)
    expenses = load_expenses()

    if not expenses:
        print(dim("No expenses to export."))
        return

    try:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "date", "amount", "category", "description"])
            writer.writeheader()
            writer.writerows(expenses)
    except OSError as e:
        print(red(f"Error writing CSV: {e}"))
        sys.exit(1)

    print(f"{green('Exported')} {len(expenses)} expense(s) → {bold(filename)}")


def cmd_import(args: argparse.Namespace) -> None:
    """Import expenses from a CSV file (must match the export format)."""
    if not os.path.exists(args.filename):
        print(red(f"File not found: {args.filename}"))
        sys.exit(1)

    try:
        with open(args.filename, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except OSError as e:
        print(red(f"Error reading CSV: {e}"))
        sys.exit(1)

    if not rows:
        print(dim("CSV file is empty — nothing to import."))
        return

    expenses = load_expenses()
    imported = 0
    skipped = 0

    for row in rows:
        try:
            entry = {
                "id": next_id(expenses),
                "date": row["date"],
                "amount": round(float(row["amount"]), 2),
                "category": row["category"].capitalize(),
                "description": row.get("description", ""),
            }
        except (KeyError, ValueError) as e:
            print(yellow(f"Skipping invalid row: {e}"))
            skipped += 1
            continue

        expenses.append(entry)
        imported += 1

    save_expenses(expenses)
    print(f"{green('Imported')} {imported} expense(s)" + (f" ({skipped} skipped)" if skipped else ""))


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense-tracker",
        description="CLI Expense Tracker — track spending from the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Amount colors: green < 50k  |  yellow < 200k  |  red >= 200k",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # add
    p_add = sub.add_parser("add", help="record a new expense")
    p_add.add_argument("amount", type=float, help="expense amount (e.g. 25000)")
    p_add.add_argument("category", help="category label (e.g. Food)")
    p_add.add_argument("description", nargs="?", default="", help="optional description")

    # edit
    p_edit = sub.add_parser("edit", help="update an existing expense by ID")
    p_edit.add_argument("id", type=int, help="expense ID to edit")
    p_edit.add_argument("--amount", "-a", type=float, help="new amount")
    p_edit.add_argument("--category", "-c", help="new category")
    p_edit.add_argument("--description", "-d", help="new description")

    # list
    p_list = sub.add_parser("list", help="show expenses (optionally filtered and sorted)")
    p_list.add_argument("category", nargs="?", help="filter by category")
    p_list.add_argument("--month", "-m", metavar="YYYY-MM", help="filter by month")
    p_list.add_argument(
        "--sort", "-s",
        choices=["date", "amount", "category"],
        help="sort by field (default: date; amount sorts highest first)",
    )
    p_list.add_argument("--limit", "-n", type=int, metavar="N", help="show only the first N rows")

    # search
    p_search = sub.add_parser("search", help="search expenses by keyword")
    p_search.add_argument("keyword", help="keyword to search in description or category")

    # delete
    p_del = sub.add_parser("delete", help="remove an expense by ID")
    p_del.add_argument("id", type=int, help="expense ID to delete")

    # summary
    p_sum = sub.add_parser("summary", help="totals grouped by category")
    p_sum.add_argument("--month", "-m", metavar="YYYY-MM", help="limit to a specific month")

    # export
    p_exp = sub.add_parser("export", help="export all expenses to CSV")
    p_exp.add_argument("filename", nargs="?", help="output filename (default: expenses.csv)")

    # import
    p_imp = sub.add_parser("import", help="import expenses from a CSV file")
    p_imp.add_argument("filename", help="CSV file to import")

    return parser


HANDLERS = {
    "add": cmd_add,
    "edit": cmd_edit,
    "list": cmd_list,
    "search": cmd_search,
    "delete": cmd_delete,
    "summary": cmd_summary,
    "export": cmd_export,
    "import": cmd_import,
}


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()
    HANDLERS[args.command](args)


if __name__ == "__main__":
    main()
