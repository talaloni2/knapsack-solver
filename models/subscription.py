from enum import Enum


class SubscriptionType(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"


class SubscriptionScore(int, Enum):
    STANDARD = 1
    PREMIUM = 2
