from enum import Enum


class AcceptResult(str, Enum):
    ACCEPT_SUCCESS = "accept_success"
    CLAIM_FAILED = "claim_failed"
    SOLUTION_NOT_EXISTS = "solution_not_exists"


class RejectResult(str, Enum):
    REJECT_SUCCESS = "reject_success"
    CLAIM_FAILED = "claim_failed"
    SUGGESTION_NOT_EXISTS = "suggestion_not_exists"
