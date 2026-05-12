from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    category_id: int
    category_name: str
    category_description: str
    creation_date: Optional[datetime] = None
    color: Optional[str] = None
    active: Optional[bool] = True

class CategoryGetAllResponseModel(BaseModel):
    total_categories: int
    pagination_use: int
    categories: List[CategoryBase]
    
class CategoryCreateModel(BaseModel):
    category_name: str
    category_description: Optional[str] = None
    color: Optional[str] = None
    active: Optional[bool] = True