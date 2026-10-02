from app.services.classifier import classify_description

CATS = [
    {"name": "Food", "keywords": ["swiggy", "zomato"]},
    {"name": "Travel", "keywords": ["uber", "petrol"]},
    {"name": "Other", "keywords": []},
]


def test_known_keyword():
    assert classify_description("Swiggy order", CATS) == "Food"


def test_case_insensitive():
    assert classify_description("ZOMATO 123", CATS) == "Food"


def test_unknown_falls_back_to_other():
    assert classify_description("random transfer", CATS) == "Other"


def test_empty_description():
    assert classify_description("", CATS) == "Other"


def test_none_description():
    assert classify_description(None, CATS) == "Other"


def test_first_match_wins():
    # "uber eats" contains "uber" -> Travel (before Food keywords would match "eats"?)
    assert classify_description("uber eats", CATS) == "Travel"
