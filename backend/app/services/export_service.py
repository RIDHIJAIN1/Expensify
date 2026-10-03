import csv
import io
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models import Transaction, User


def _filtered(
    db: Session,
    user: User,
    date_from: date | None,
    date_to: date | None,
    category_id: int | None,
    type_: str | None,
):
    q = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == user.id)
    )
    if date_from:
        q = q.filter(Transaction.date >= date_from)
    if date_to:
        q = q.filter(Transaction.date <= date_to)
    if category_id is not None:
        q = q.filter(Transaction.category_id == category_id)
    if type_:
        q = q.filter(Transaction.type == type_.upper())
    return q.order_by(Transaction.date.desc(), Transaction.id.desc()).all()


def _category_totals(rows) -> tuple[dict[str, float], dict[str, int]]:
    cat_totals: dict[str, float] = {}
    cat_count: dict[str, int] = {}
    for t in rows:
        if t.type != "DEBIT":
            continue
        name = t.category.name if t.category else "Uncategorized"
        cat_totals[name] = cat_totals.get(name, 0) + float(t.amount)
        cat_count[name] = cat_count.get(name, 0) + 1
    return cat_totals, cat_count


def build_csv(
    db: Session,
    user: User,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    type_: str | None = None,
) -> str:
    rows = _filtered(db, user, date_from, date_to, category_id, type_)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Description", "Amount", "Type", "Reference", "Category"])
    for t in rows:
        writer.writerow([
            t.date.isoformat(),
            t.description,
            f"{t.amount:.2f}",
            t.type,
            t.reference or "",
            t.category.name if t.category else "Uncategorized",
        ])
    return buffer.getvalue()


def _summary_section(
    story, styles, total_income: Decimal, total_spent: Decimal, date_from, date_to
) -> None:
    from reportlab.platypus import Paragraph, Spacer

    story.append(Paragraph("Expense Classification Report", styles["Title"]))
    period = f"{date_from or 'beginning'} → {date_to or 'now'}"
    story.append(Paragraph(f"Period: {period}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Total Income: ₹{total_income:.2f}", styles["Heading2"]))
    story.append(Paragraph(f"Total Spent: ₹{total_spent:.2f}", styles["Heading2"]))
    story.append(Paragraph(f"Net: ₹{total_income - total_spent:.2f}", styles["Heading2"]))
    story.append(Spacer(1, 16))


def _category_section(story, styles, cat_totals: dict, cat_count: dict) -> None:
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    story.append(Paragraph("Spending by Category", styles["Heading2"]))
    data = [["Category", "Transactions", "Total"]]
    for name in sorted(cat_totals, key=lambda n: -cat_totals[n]):
        data.append([name, str(cat_count[name]), f"₹{cat_totals[name]:.2f}"])
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    story.append(table)
    story.append(Spacer(1, 16))


def _transactions_section(story, styles, rows) -> None:
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    story.append(Paragraph("Recent Transactions (top 30)", styles["Heading2"]))
    data = [["Date", "Description", "Type", "Amount", "Category"]]
    for t in rows[:30]:
        data.append([
            t.date.isoformat(), t.description[:40], t.type, f"₹{t.amount:.2f}",
            t.category.name if t.category else "Uncategorized",
        ])
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)


def build_pdf(
    db: Session, user: User, date_from: date | None = None, date_to: date | None = None
) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate

    rows = _filtered(db, user, date_from, date_to, None, None)
    total_income = sum((t.amount for t in rows if t.type == "CREDIT"), Decimal("0"))
    total_spent = sum((t.amount for t in rows if t.type == "DEBIT"), Decimal("0"))
    cat_totals, cat_count = _category_totals(rows)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="Expense Report")
    styles = getSampleStyleSheet()
    story: list = []
    _summary_section(story, styles, total_income, total_spent, date_from, date_to)
    _category_section(story, styles, cat_totals, cat_count)
    _transactions_section(story, styles, rows)

    doc.build(story)
    return buffer.getvalue()
