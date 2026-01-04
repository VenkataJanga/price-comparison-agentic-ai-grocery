from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class GroceryItem(BaseModel):
    id: str = Field(..., description="UI/Client-side item id")
    itemname: str = Field(..., description="Item name, e.g., Milk")
    brand: Optional[str] = Field(default=None, description="Preferred brand if any")
    quantity: float = Field(..., gt=0, description="Quantity numeric value")
    unit: str = Field(..., min_length=1, description="Unit, e.g., kg, g, L, ml, pcs")
    allow_substitution: bool = Field(default=True, description="Allow closest equivalent if exact match not found")
