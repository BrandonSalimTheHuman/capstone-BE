from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Store 
class StoreBase(BaseModel):
    store_name: str
    url: str
    
class StoreCreate(StoreBase):
    pass 

class StoreUpdate(BaseModel):
    store_name: Optional[str] = None
    url: Optional[str] = None
    
class Store(StoreBase):
    store_id: int

    model_config = ConfigDict(from_attributes=True)
  
# Product  
class ProductBase(BaseModel):
    product_name: str
    size: str
    description: Optional[str] = None
    image: Optional[str] = None

class ProductCreate(ProductBase):
    pass    

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    size: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    
class Product(ProductBase):
    product_id: int

    model_config = ConfigDict(from_attributes=True)

# Price   
class PriceBase(BaseModel):
    product_id: int
    store_id: int
    price: Decimal
    unit_price: Optional[str] = None
    date_recorded: Optional[datetime] = None
    is_special: Optional[bool] = False
    special_type: Optional[str] = None
    special_buy_quantity: Optional[int] = None
    special_buy_price: Optional[Decimal] = None
    
class PriceCreate(PriceBase):
    pass    

class Price(PriceBase):
    price_id: int

    model_config = ConfigDict(from_attributes=True)
    
class PriceUpdate(BaseModel):
    product_id: Optional[int] = None
    store_id: Optional[int] = None
    price: Optional[Decimal] = None
    unit_price: Optional[str] = None
    date_recorded: Optional[datetime] = None
    is_special: Optional[bool] = None
    special_type: Optional[str] = None
    special_buy_quantity: Optional[int] = None
    special_buy_price: Optional[Decimal] = None
    
# StoreListItem
class StoreListItemBase(BaseModel):
    product_id: int
    quantity: int = 1
    is_checked: bool = False

class StoreListItemCreate(StoreListItemBase):
    pass

class StoreListItemUpdate(BaseModel):
    quantity: Optional[int] = None
    is_checked: Optional[bool] = None

class StoreListItem(StoreListItemBase):
    list_item_id: int
    store_list_id: int
    model_config = ConfigDict(from_attributes=True)


# StoreList
class StoreListBase(BaseModel):
    store_id: int

class StoreListCreate(StoreListBase):
    pass

class StoreList(StoreListBase):
    store_list_id: int
    parent_list_id: int
    items: List[StoreListItem] = []
    model_config = ConfigDict(from_attributes=True)


# ParentList
class ParentListBase(BaseModel):
    user_id: int
    list_name: str

class ParentListCreate(ParentListBase):
    pass

class ParentListUpdate(BaseModel):
    list_name: Optional[str] = None

class ParentList(ParentListBase):
    parent_list_id: int
    created_at: datetime
    store_lists: List[StoreList] = []
    model_config = ConfigDict(from_attributes=True)








