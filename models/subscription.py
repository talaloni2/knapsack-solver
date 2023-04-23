from enum import Enum


class SubscriptionType(str, Enum):
    STANDARD = "Basic"
    PREMIUM = "Premium"


class SubscriptionScore(int, Enum):
    STANDARD = 1
    PREMIUM = 2
