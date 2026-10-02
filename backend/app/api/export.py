import csv
import io
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Transaction, User

router = APIRouter(prefix="/api/export", tags=["export"])


def _filtered(db: Session, user: User, date_from, date_to, category_id, type_):
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


@router.get("/csv")
def export_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    type: str | None = None,
):
    rows = _filtered(db, user, date_from, date_to, category_id, type)
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
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/pdf")
def export_pdf(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    date_from: date | None = None,
    date_to: date | None = None,
):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    rows = _filtered(db, user, date_from, date_to, None, None)

    total_income = sum((t.amount for t in rows if t.type == "CREDIT"), Decimal("0"))
    total_spent = sum((t.amount for t in rows if t.type == "DEBIT"), Decimal("0"))

    # category totals (debit)
    cat_totals: dict[str, float] = {}
    cat_count: dict[str, int] = {}
    for t in rows:
        if t.type != "DEBIT":
            continue
        name = t.category.name if t.category else "Uncategorized"
        cat_totals[name] = cat_totals.get(name, 0) + float(t.amount)
        cat_count[name] = cat_count.get(name, 0) + 1

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="Expense Report")
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Expense Classification Report", styles["Title"]))
    period = f"{date_from or 'beginning'} → {date_to or 'now'}"
    story.append(Paragraph(f"Period: {period}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Total Income: ₹{total_income:.2f}", styles["Heading2"]))
    story.append(Paragraph(f"Total Spent: ₹{total_spent:.2f}", styles["Heading2"]))
    story.append(Paragraph(f"Net: ₹{total_income - total_spent:.2f}", styles["Heading2"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Spending by Category", styles["Heading2"]))
    cat_data = [["Category", "Transactions", "Total"]]
    for name in sorted(cat_totals, key=lambda n: -cat_totals[n]):
        cat_data.append([name, str(cat_count[name]), f"₹{cat_totals[name]:.2f}"])
    cat_table = Table(cat_data)
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Recent Transactions (top 30)", styles["Heading2"]))
    tx_data = [["Date", "Description", "Type", "Amount", "Category"]]
    for t in rows[:30]:
        tx_data.append([
            t.date.isoformat(), t.description[:40], t.type, f"₹{t.amount:.2f}",
            t.category.name if t.category else "Uncategorized",
        ])
    tx_table = Table(tx_data)
    tx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    story.append(tx_table)

    doc.build(story)
    return Response(
        buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"},
    )
