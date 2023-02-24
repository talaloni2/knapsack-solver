from uuid import uuid4


def get_random_string() -> str:
    return str(uuid4())
