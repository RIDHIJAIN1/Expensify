"""Rule-based transaction classifier.

Deterministic keyword matching: scan the transaction description for each
category's keywords; first match wins. Falls back to "Other" when nothing
matches. Deliberately chosen over ML/LLM for transparency, testability, and
data privacy (no third-party calls).
"""

DEFAULT_CATEGORIES = [
    {
        "name": "Food",
        "color": "#f97316",
        "keywords": [
            "swiggy", "zomato", "bigbasket", "blinkit", "zepto", "instamart",
            "dominos", "mcdonalds", "kfc", "starbucks", "restaurant", "cafe",
            "grocery", "food", "pizza", "biryani", "hotel", "bakery", "dunzo",
        ],
    },
    {
        "name": "Travel",
        "color": "#3b82f6",
        "keywords": [
            "uber", "ola", "rapido", "irctc", "makemytrip", "cleartrip", "petrol",
            "fuel", "airport", "train", "bus", "metro", "cab", "flight",
            "indianoil", "bharat petroleum", "hp petrol", "shell", "toll", "parking",
        ],
    },
    {
        "name": "Utilities",
        "color": "#10b981",
        "keywords": [
            "electricity", "bses", "airtel", "jio", "vodafone", "idea", "wifi",
            "broadband", "water", "gas", "bill", "recharge", "dth", "dish tv",
            "mobile", "internet", "postpaid", "prepaid", "tatasky",
        ],
    },
    {
        "name": "Housing",
        "color": "#0ea5e9",
        "keywords": ["rent", "maintenance", "society", "lease", "housing", "landlord"],
    },
    {
        "name": "Shopping",
        "color": "#8b5cf6",
        "keywords": [
            "amazon", "flipkart", "myntra", "ajio", "meesho", "snapdeal", "nykaa",
            "lifestyle", "shoppersstop", "mall", "decathlon", "shopping",
        ],
    },
    {
        "name": "Entertainment",
        "color": "#ec4899",
        "keywords": [
            "netflix", "prime video", "amazon prime", "hotstar", "spotify",
            "youtube", "bookmyshow", "pvr", "inox", "movie", "cinema",
            "playstation", "steam", "disney", "game",
        ],
    },
    {
        "name": "Healthcare",
        "color": "#ef4444",
        "keywords": [
            "pharmacy", "apollo", "medplus", "netmeds", "pharmeasy", "hospital",
            "doctor", "medicine", "medical", "diagnostic", "lab", "dental",
            "clinic", "health", "1mg", "gym", "cult", "fitness", "yoga",
        ],
    },
    {
        "name": "Income",
        "color": "#22c55e",
        "keywords": [
            "salary", "interest", "refund", "dividend", "cashback", "reimbursement",
        ],
    },
    {"name": "Other", "color": "#6b7280", "keywords": []},
]


def classify_description(description: str, category_keywords: list[dict]) -> str:
    """Return the category name for a description, falling back to "Other".

    `category_keywords` is a list of {"name": str, "keywords": list[str]},
    iterated in order; first keyword match wins. "Other" is never matched by
    keyword and is returned only as the fallback.
    """
    desc = (description or "").lower()
    for cat in category_keywords:
        if cat.get("name") == "Other":
            continue
        for kw in cat.get("keywords", []):
            kw = (kw or "").strip().lower()
            if kw and kw in desc:
                return cat["name"]
    return "Other"


def learned_keyword(description: str) -> str | None:
    """Derive a keyword from a merchant description the user just re-categorized.

    Uses up to the first three words so "Indian Oil Petrol" becomes a single
    learnable phrase rather than a too-generic first word.
    """
    text = " ".join((description or "").lower().split())
    if not text:
        return None
    keyword = " ".join(text.split(" ")[:3]).strip(" -_.,")
    return keyword if len(keyword) >= 3 else None
