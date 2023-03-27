from enum import Enum


class ClusterAvailabilityScore(int, Enum):
    AVAILABLE = 4
    MODERATE = 3
    BUSY = 2
    VERY_BUSY = 1
