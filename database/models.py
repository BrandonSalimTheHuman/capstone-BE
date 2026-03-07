from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Store(Base):
    __tablename__ = "stores"
    
    store_id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    
    prices = relationship("Price", back_populates="store")
    store_lists = relationship("StoreList", back_populates="store")

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, index=True)
    size = Column(String, nullable=False)
    description = Column(String, nullable=True)
    image = Column(String, nullable=True)
    
    prices = relationship("Price", back_populates="product")
    store_list_items = relationship("StoreListItem", back_populates="product")

class Price(Base):
    __tablename__ = "prices"
    
    price_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.store_id"), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    unit_price = Column(String, nullable=True)
    date_recorded = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_special = Column(Boolean, default=False, nullable=False)
    special_type = Column(String, nullable=True)
    special_buy_quantity = Column(Integer, nullable=True)
    special_buy_price = Column(DECIMAL(10, 2), nullable=True)
    
    product = relationship("Product", back_populates="prices")
    store = relationship("Store", back_populates="prices")
    
class PriceHistory(Base):
    __tablename__ = "price_history"
    
    history_id = Column(Integer, primary_key=True, index=True)
    price_id = Column(Integer, ForeignKey("prices.price_id"), nullable=False)
    old_price = Column(DECIMAL(10, 2), nullable=False)
    new_price = Column(DECIMAL(10, 2), nullable=False)
    change_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    price = relationship("Price")
    
# shopping list
class ParentList(Base):
    __tablename__ = "parent_lists"

    parent_list_id = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, nullable=False, index=True)
    list_name      = Column(String, nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)

    store_lists = relationship("StoreList", back_populates="parent_list", cascade="all, delete-orphan") 


class StoreList(Base):
    __tablename__ = "store_lists"

    store_list_id  = Column(Integer, primary_key=True, index=True)
    parent_list_id = Column(Integer, ForeignKey("parent_lists.parent_list_id"), nullable=False)
    store_id       = Column(Integer, ForeignKey("stores.store_id"), nullable=False)

    parent_list = relationship("ParentList", back_populates="store_lists")
    store       = relationship("Store", back_populates="store_lists")
    items       = relationship("StoreListItem", back_populates="store_list", cascade="all, delete-orphan")


class StoreListItem(Base):
    __tablename__ = "store_list_items"

    list_item_id  = Column(Integer, primary_key=True, index=True)
    store_list_id = Column(Integer, ForeignKey("store_lists.store_list_id"), nullable=False)
    product_id    = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity      = Column(Integer, nullable=False, default=1)
    is_checked    = Column(Boolean, nullable=False, default=False)

    store_list = relationship("StoreList", back_populates="items")
    product    = relationship("Product", back_populates="store_list_items")
    
    