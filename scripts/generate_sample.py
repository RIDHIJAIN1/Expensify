"""Generate a realistic Indian bank-statement CSV (Jun-Oct 2026).

Writes to the repo root and to frontend/public/ so it can be downloaded
from the running app. Deterministic (fixed seed) so the data is stable.
"""
import random
from datetime import date, timedelta

random.seed(42)

START = date(2026, 1, 1)
END = date(2026, 10, 2)

MERCHANTS = [
    ("Swiggy", "Food", "UPI", 180, 750),
    ("Zomato", "Food", "UPI", 150, 820),
    ("BigBasket", "Food", "UPI", 900, 3200),
    ("Zepto", "Food", "UPI", 200, 900),
    ("Blinkit", "Food", "UPI", 150, 800),
    ("Starbucks", "Food", "CARD", 250, 650),
    ("Uber", "Travel", "UPI", 90, 480),
    ("Ola", "Travel", "UPI", 80, 420),
    ("Indian Oil Petrol", "Travel", "CARD", 1200, 2500),
    ("IRCTC", "Travel", "UPI", 400, 1800),
    ("Amazon", "Shopping", "CARD", 400, 5500),
    ("Flipkart", "Shopping", "CARD", 500, 4200),
    ("Myntra", "Shopping", "UPI", 600, 3000),
    ("Meesho", "Shopping", "UPI", 250, 1400),
    ("PVR Cinemas", "Entertainment", "UPI", 400, 900),
    ("BookMyShow", "Entertainment", "UPI", 300, 800),
    ("Spotify", "Entertainment", "UPI", 119, 199),
    ("Apollo Pharmacy", "Healthcare", "CARD", 200, 1600),
    ("PharmEasy", "Healthcare", "UPI", 300, 1800),
    ("Cult.fit", "Other", "UPI", 1499, 1499),
]

rows = []
seq = 1000
month_cursor = START

while month_cursor <= END:
    y, m = month_cursor.year, month_cursor.month

    def add(d, desc, amount, typ, ref_prefix):
        global seq
        seq += 1
        rows.append((d, desc, amount, typ, f"{ref_prefix}-{seq}"))

    # recurring
    add(date(y, m, 1), "Salary", 75000.00, "CREDIT", "NEFT")
    add(date(y, m, 2), "Rent", 18000.00, "DEBIT", "UPI")
    add(date(y, m, 5), "Electricity Bill", round(random.uniform(1400, 2600), 2), "DEBIT", "UPI")
    add(date(y, m, 7), "Netflix", 649.00, "DEBIT", "UPI")
    add(date(y, m, 8), "Airtel Recharge", 599.00, "DEBIT", "UPI")
    add(date(y, m, 10), "Cult.fit Gym", 1499.00, "DEBIT", "UPI")
    add(date(y, m, 26), "Interest Credit", round(random.uniform(80, 420), 2), "CREDIT", "BANK")

    # random spends spread through the month
    for _ in range(random.randint(7, 11)):
        day = random.randint(1, 28)
        d = date(y, m, day)
        if d > END:
            continue
        desc, _cat, prefix, lo, hi = random.choice(MERCHANTS)
        amount = round(random.uniform(lo, hi), 2)
        add(d, desc, amount, "DEBIT", prefix)

    # occasional refund
    if random.random() < 0.5:
        add(date(y, m, random.randint(12, 24)), "Refund - Amazon", round(random.uniform(200, 1500), 2), "CREDIT", "NEFT")

    if m == 12:
        month_cursor = date(y + 1, 1, 1)
    else:
        month_cursor = date(y, m + 1, 1)

rows.sort(key=lambda r: r[0])

lines = ["Date,Description,Amount,Type,Reference"]
for d, desc, amount, typ, ref in rows:
    lines.append(f"{d.isoformat()},{desc},{amount:.2f},{typ},{ref}")

content = "\n".join(lines) + "\n"

for path in ["sample_statement.csv", "frontend/public/sample_statement.csv"]:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)

print(f"wrote {len(rows)} transactions to sample_statement.csv and frontend/public/")
