from models.base_model import BaseModel


class KnapsackItem(BaseModel):
    id: str
    volume: int
    value: int
