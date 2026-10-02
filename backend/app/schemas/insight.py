from pydantic import BaseModel


class Insight(BaseModel):
    icon: str  # trend-up | trend-down | trend-flat | piggy | category | growth | store | receipt
    tone: str  # positive | warning | neutral | info
    title: str
    detail: str
