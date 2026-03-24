from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import models
from database.schemas import schemas

# STORE CRUD 

def create_store(db: Session, store: schemas.StoreCreate) -> models.Store:
    db_store = models.Store(**store.model_dump())
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store

def get_store(db: Session, store_id: int) -> Optional[models.Store]:
    return db.query(models.Store).filter(models.Store.store_id == store_id).first()

def get_store_by_name(db: Session, store_name: str) -> Optional[models.Store]:
    return db.query(models.Store).filter(models.Store.store_name == store_name).first()

def get_stores(db: Session, skip: int = 0, limit: int = 100) -> List[models.Store]:
    return db.query(models.Store).offset(skip).limit(limit).all()

def update_store(db: Session, store_id: int, store_update: schemas.StoreUpdate) -> Optional[models.Store]:
    db_store = get_store(db, store_id)
    if db_store is None:
        return None
    
    update_data = store_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_store, field, value)
    
    db.commit()
    db.refresh(db_store)
    return db_store

def delete_store(db: Session, store_id: int) -> bool:
    db_store = get_store(db, store_id)
    if db_store is None:
        return False
    
    db.delete(db_store)
    db.commit()
    return True

#  PRODUCT CRUD 

def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.product_id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[models.Product]:
    return db.query(models.Product).offset(skip).limit(limit).all()

def search_products(db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[models.Product]:
    return db.query(models.Product).filter(
        models.Product.product_name.ilike(f"%{search_term}%")
    ).offset(skip).limit(limit).all()

def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate) -> Optional[models.Product]:
    db_product = get_product(db, product_id)
    if db_product is None:
        return None
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> bool:
    db_product = get_product(db, product_id)
    if db_product is None:
        return False
    
    db.delete(db_product)
    db.commit()
    return True

# PRICE CRUD 

def create_price(db: Session, price: schemas.PriceCreate) -> models.Price:
    db_price = models.Price(**price.model_dump())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price

def get_price(db: Session, price_id: int) -> Optional[models.Price]:
    return db.query(models.Price).filter(models.Price.price_id == price_id).first()

def get_prices(db: Session, skip: int = 0, limit: int = 100) -> List[models.Price]:
    return db.query(models.Price).offset(skip).limit(limit).all()

def get_prices_by_product(db: Session, product_id: int, skip: int = 0, limit: int = 100) -> List[models.Price]:
    return db.query(models.Price).filter(
        models.Price.product_id == product_id
    ).order_by(models.Price.date_recorded.desc()).offset(skip).limit(limit).all()

def get_prices_by_store(db: Session, store_id: int, skip: int = 0, limit: int = 100) -> List[models.Price]:
    return db.query(models.Price).filter(
        models.Price.store_id == store_id
    ).order_by(models.Price.date_recorded.desc()).offset(skip).limit(limit).all()

def get_latest_price(db: Session, product_id: int, store_id: int) -> Optional[models.Price]:
    return db.query(models.Price).filter(
        models.Price.product_id == product_id,
        models.Price.store_id == store_id
    ).order_by(models.Price.date_recorded.desc()).first()

def get_special_prices(db: Session, skip: int = 0, limit: int = 100) -> List[models.Price]:
    return db.query(models.Price).filter(
        models.Price.is_special == True
    ).order_by(models.Price.date_recorded.desc()).offset(skip).limit(limit).all()

def get_price_history(db: Session, product_id: int, store_id: int, skip: int = 0, limit: int = 100) -> List[models.Price]:
    return db.query(models.Price).filter(
        models.Price.product_id == product_id,
        models.Price.store_id == store_id
    ).order_by(models.Price.date_recorded.desc()).offset(skip).limit(limit).all()

def update_price(db: Session, price_id: int, price_update: schemas.PriceUpdate) -> Optional[models.Price]:
    db_price = get_price(db, price_id)
    if db_price is None:
        return None
    
    update_data = price_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_price, field, value)
    
    db.commit()
    db.refresh(db_price)
    return db_price

def delete_price(db: Session, price_id: int) -> bool:
    db_price = get_price(db, price_id)
    if db_price is None:
        return False
    
    db.delete(db_price)
    db.commit()
    return True

def compare_prices_across_stores(db: Session, product_id: int) -> List[models.Price]:
    from sqlalchemy import func
    
    subquery = db.query(
        models.Price.store_id,
        func.max(models.Price.date_recorded).label('max_date')
    ).filter(
        models.Price.product_id == product_id
    ).group_by(models.Price.store_id).subquery()
    
    return db.query(models.Price).join(
        subquery,
        (models.Price.store_id == subquery.c.store_id) &
        (models.Price.date_recorded == subquery.c.max_date)
    ).filter(models.Price.product_id == product_id).all()

def get_cheapest_store_for_product(db: Session, product_id: int) -> Optional[models.Price]:
    prices = compare_prices_across_stores(db, product_id)
    if not prices:
        return None
    return min(prices, key=lambda p: p.price)

# ParentList CRUD 

def create_parent_list(db: Session, parent_list: schemas.ParentListCreate) -> models.ParentList:
    db_list = models.ParentList(**parent_list.model_dump())
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    return db_list

def get_parent_list(db: Session, parent_list_id: int) -> Optional[models.ParentList]:
    return db.query(models.ParentList).filter(
        models.ParentList.parent_list_id == parent_list_id
    ).first()

def get_parent_lists_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.ParentList]:
    return db.query(models.ParentList).filter(
        models.ParentList.user_id == user_id
    ).offset(skip).limit(limit).all()

def update_parent_list(db: Session, parent_list_id: int, update: schemas.ParentListUpdate) -> Optional[models.ParentList]:
    db_list = get_parent_list(db, parent_list_id)
    if db_list is None:
        return None
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_list, field, value)
    db.commit()
    db.refresh(db_list)
    return db_list

def delete_parent_list(db: Session, parent_list_id: int) -> bool:
    db_list = get_parent_list(db, parent_list_id)
    if db_list is None:
        return False
    db.delete(db_list)
    db.commit()
    return True

# StoreList CRUD 

def create_store_list(db: Session, parent_list_id: int, store_list: schemas.StoreListCreate) -> models.StoreList:
    db_store_list = models.StoreList(
        parent_list_id=parent_list_id,
        **store_list.model_dump()
    )
    db.add(db_store_list)
    db.commit()
    db.refresh(db_store_list)
    return db_store_list

def get_store_list(db: Session, store_list_id: int) -> Optional[models.StoreList]:
    return db.query(models.StoreList).filter(
        models.StoreList.store_list_id == store_list_id
    ).first()

def get_store_lists_by_parent(db: Session, parent_list_id: int) -> List[models.StoreList]:
    return db.query(models.StoreList).filter(
        models.StoreList.parent_list_id == parent_list_id
    ).all()

def delete_store_list(db: Session, store_list_id: int) -> bool:
    db_store_list = get_store_list(db, store_list_id)
    if db_store_list is None:
        return False
    db.delete(db_store_list)
    db.commit()
    return True

# StoreListItem CRUD

def create_store_list_item(db: Session, store_list_id: int, item: schemas.StoreListItemCreate) -> models.StoreListItem:
    db_item = models.StoreListItem(
        store_list_id=store_list_id,
        **item.model_dump()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_store_list_item(db: Session, list_item_id: int) -> Optional[models.StoreListItem]:
    return db.query(models.StoreListItem).filter(
        models.StoreListItem.list_item_id == list_item_id
    ).first()

def get_items_by_store_list(db: Session, store_list_id: int) -> List[models.StoreListItem]:
    return db.query(models.StoreListItem).filter(
        models.StoreListItem.store_list_id == store_list_id
    ).all()

def update_store_list_item(db: Session, list_item_id: int, update: schemas.StoreListItemUpdate) -> Optional[models.StoreListItem]:
    db_item = get_store_list_item(db, list_item_id)
    if db_item is None:
        return None
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_store_list_item(db: Session, list_item_id: int) -> bool:
    db_item = get_store_list_item(db, list_item_id)
    if db_item is None:
        return False
    db.delete(db_item)
    db.commit()
    return True

def check_off_item(db: Session, list_item_id: int) -> Optional[models.StoreListItem]:
    return update_store_list_item(db, list_item_id, schemas.StoreListItemUpdate(is_checked=True))

def uncheck_item(db: Session, list_item_id: int) -> Optional[models.StoreListItem]:
    return update_store_list_item(db, list_item_id, schemas.StoreListItemUpdate(is_checked=False))








