from datetime import datetime


class TimeService:
    # noinspection PyMethodMayBeStatic
    def now(self):
        return datetime.now()
