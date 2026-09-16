from pydantic import BaseModel


class FoodOut(BaseModel):
    id: str
    name: str
    serving_size: float
    serving_unit: str
    calories_per_serving: float
    protein_g: float
    carbs_g: float
    fat_g: float
