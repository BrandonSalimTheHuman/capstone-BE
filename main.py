from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import asynccontextmanager

from database.database import engine, get_db, Base
from database import models
from database.schemas import schemas
from database import crud
from auth.auth import get_current_user
from auth.oauth import get_google_oauth_url
from database.database import supabase


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup if DB is connected
    if engine is not None:
        models.Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
    else:
        print("WARNING: DATABASE_URL not set. SQLAlchemy tables not created.")
    yield


app = FastAPI(title="Grocery Price Comparison API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Stores ──────────────────────────────────────────

@app.post("/stores/", response_model=schemas.Store)
def create_store(store: schemas.StoreCreate, db: Session = Depends(get_db)):
    return crud.create_store(db, store)


@app.get("/stores/", response_model=List[schemas.Store])
def read_stores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_stores(db, skip=skip, limit=limit)


@app.get("/stores/{store_id}", response_model=schemas.Store)
def read_store(store_id: int, db: Session = Depends(get_db)):
    store = crud.get_store(db, store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@app.put("/stores/{store_id}", response_model=schemas.Store)
def update_store(store_id: int, store_update: schemas.StoreUpdate, db: Session = Depends(get_db)):
    store = crud.update_store(db, store_id, store_update)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@app.delete("/stores/{store_id}")
def delete_store(store_id: int, db: Session = Depends(get_db)):
    if not crud.delete_store(db, store_id):
        raise HTTPException(status_code=404, detail="Store not found")
    return {"detail": "Store deleted"}


# ── Products ────────────────────────────────────────

@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, product)


@app.get("/products/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)


@app.get("/products/search/", response_model=List[schemas.Product])
def search_products(q: str = Query(..., min_length=1), skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.search_products(db, q, skip=skip, limit=limit)


@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product_update: schemas.ProductUpdate, db: Session = Depends(get_db)):
    product = crud.update_product(db, product_id, product_update)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    if not crud.delete_product(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"detail": "Product deleted"}


# ── Prices ──────────────────────────────────────────

@app.post("/prices/", response_model=schemas.Price)
def create_price(price: schemas.PriceCreate, db: Session = Depends(get_db)):
    return crud.create_price(db, price)


@app.get("/prices/", response_model=List[schemas.Price])
def read_prices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_prices(db, skip=skip, limit=limit)


@app.get("/prices/{price_id}", response_model=schemas.Price)
def read_price(price_id: int, db: Session = Depends(get_db)):
    price = crud.get_price(db, price_id)
    if price is None:
        raise HTTPException(status_code=404, detail="Price not found")
    return price


@app.get("/prices/product/{product_id}", response_model=List[schemas.Price])
def read_prices_by_product(product_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_prices_by_product(db, product_id, skip=skip, limit=limit)


@app.get("/prices/store/{store_id}", response_model=List[schemas.Price])
def read_prices_by_store(store_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_prices_by_store(db, store_id, skip=skip, limit=limit)


@app.get("/prices/specials/", response_model=List[schemas.Price])
def read_special_prices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_special_prices(db, skip=skip, limit=limit)


@app.get("/prices/compare/{product_id}", response_model=List[schemas.Price])
def compare_prices(product_id: int, db: Session = Depends(get_db)):
    return crud.compare_prices_across_stores(db, product_id)


@app.get("/prices/cheapest/{product_id}", response_model=schemas.Price)
def cheapest_store(product_id: int, db: Session = Depends(get_db)):
    price = crud.get_cheapest_store_for_product(db, product_id)
    if price is None:
        raise HTTPException(status_code=404, detail="No prices found for product")
    return price


@app.put("/prices/{price_id}", response_model=schemas.Price)
def update_price(price_id: int, price_update: schemas.PriceUpdate, db: Session = Depends(get_db)):
    price = crud.update_price(db, price_id, price_update)
    if price is None:
        raise HTTPException(status_code=404, detail="Price not found")
    return price


@app.delete("/prices/{price_id}")
def delete_price(price_id: int, db: Session = Depends(get_db)):
    if not crud.delete_price(db, price_id):
        raise HTTPException(status_code=404, detail="Price not found")
    return {"detail": "Price deleted"}


# ── Shopping Lists ──────────────────────────────────

@app.post("/lists/", response_model=schemas.ParentList)
def create_parent_list(parent_list: schemas.ParentListCreate, db: Session = Depends(get_db)):
    return crud.create_parent_list(db, parent_list)


@app.get("/lists/user/{user_id}", response_model=List[schemas.ParentList])
def read_user_lists(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_parent_lists_by_user(db, user_id, skip=skip, limit=limit)


@app.get("/lists/{parent_list_id}", response_model=schemas.ParentList)
def read_parent_list(parent_list_id: int, db: Session = Depends(get_db)):
    pl = crud.get_parent_list(db, parent_list_id)
    if pl is None:
        raise HTTPException(status_code=404, detail="List not found")
    return pl


@app.put("/lists/{parent_list_id}", response_model=schemas.ParentList)
def update_parent_list(parent_list_id: int, update: schemas.ParentListUpdate, db: Session = Depends(get_db)):
    pl = crud.update_parent_list(db, parent_list_id, update)
    if pl is None:
        raise HTTPException(status_code=404, detail="List not found")
    return pl


@app.delete("/lists/{parent_list_id}")
def delete_parent_list(parent_list_id: int, db: Session = Depends(get_db)):
    if not crud.delete_parent_list(db, parent_list_id):
        raise HTTPException(status_code=404, detail="List not found")
    return {"detail": "List deleted"}


# ── Store Lists ─────────────────────────────────────

@app.post("/lists/{parent_list_id}/stores/", response_model=schemas.StoreList)
def create_store_list(parent_list_id: int, store_list: schemas.StoreListCreate, db: Session = Depends(get_db)):
    return crud.create_store_list(db, parent_list_id, store_list)


@app.get("/store-lists/{store_list_id}", response_model=schemas.StoreList)
def read_store_list(store_list_id: int, db: Session = Depends(get_db)):
    sl = crud.get_store_list(db, store_list_id)
    if sl is None:
        raise HTTPException(status_code=404, detail="Store list not found")
    return sl


@app.delete("/store-lists/{store_list_id}")
def delete_store_list(store_list_id: int, db: Session = Depends(get_db)):
    if not crud.delete_store_list(db, store_list_id):
        raise HTTPException(status_code=404, detail="Store list not found")
    return {"detail": "Store list deleted"}


# ── Store List Items ────────────────────────────────

@app.post("/store-lists/{store_list_id}/items/", response_model=schemas.StoreListItem)
def create_store_list_item(store_list_id: int, item: schemas.StoreListItemCreate, db: Session = Depends(get_db)):
    return crud.create_store_list_item(db, store_list_id, item)


@app.get("/store-lists/{store_list_id}/items/", response_model=List[schemas.StoreListItem])
def read_store_list_items(store_list_id: int, db: Session = Depends(get_db)):
    return crud.get_items_by_store_list(db, store_list_id)


@app.put("/items/{list_item_id}", response_model=schemas.StoreListItem)
def update_item(list_item_id: int, update: schemas.StoreListItemUpdate, db: Session = Depends(get_db)):
    item = crud.update_store_list_item(db, list_item_id, update)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/items/{list_item_id}/check", response_model=schemas.StoreListItem)
def check_item(list_item_id: int, db: Session = Depends(get_db)):
    item = crud.check_off_item(db, list_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/items/{list_item_id}/uncheck", response_model=schemas.StoreListItem)
def uncheck_item(list_item_id: int, db: Session = Depends(get_db)):
    item = crud.uncheck_item(db, list_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/items/{list_item_id}")
def delete_item(list_item_id: int, db: Session = Depends(get_db)):
    if not crud.delete_store_list_item(db, list_item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": "Item deleted"}


# ── Auth (Supabase) ──────────────────────────────────

@app.post("/auth/register", response_model=schemas.UserResponse, status_code=201)
def register(body: schemas.UserRegister):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Auth service not configured")
    try:
        result = supabase.auth.sign_up({"email": body.email, "password": body.password})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result.user is None:
        raise HTTPException(status_code=400, detail="Registration failed")
    return schemas.UserResponse(
        user_id=str(result.user.id),
        email=result.user.email,
        email_confirmed=result.user.email_confirmed_at is not None,
    )


@app.post("/auth/login", response_model=schemas.Token)
def login(credentials: schemas.LoginRequest):
    if supabase is None:
        raise HTTPException(status_code=503, detail="Auth service not configured")
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": credentials.email, "password": credentials.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return schemas.Token(access_token=result.session.access_token)


@app.get("/auth/google")
def google_login(redirect_to: str = "http://localhost:3000/auth/callback"):
    """Redirect the browser to Supabase's Google OAuth consent screen."""
    try:
        url = get_google_oauth_url(redirect_to)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return RedirectResponse(url)


@app.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return schemas.UserResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        email_confirmed=current_user.email_confirmed_at is not None,
    )


# ── Store Product Availability ───────────────────────

@app.put("/stores/{store_id}/products/{product_id}/availability", response_model=schemas.StoreProduct)
def set_availability(store_id: int, product_id: int, update: schemas.StoreProductUpdate, db: Session = Depends(get_db)):
    return crud.set_store_product_availability(db, store_id, product_id, update.is_available)


@app.get("/stores/{store_id}/products/{product_id}/availability", response_model=schemas.StoreProduct)
def get_availability(store_id: int, product_id: int, db: Session = Depends(get_db)):
    sp = crud.get_store_product(db, store_id, product_id)
    if sp is None:
        raise HTTPException(status_code=404, detail="No availability record found")
    return sp


@app.get("/stores/{store_id}/available-products", response_model=List[schemas.StoreProduct])
def available_products_for_store(store_id: int, db: Session = Depends(get_db)):
    return crud.get_available_products_for_store(db, store_id)


@app.get("/products/{product_id}/store-availability", response_model=List[schemas.StoreProduct])
def product_store_availability(product_id: int, db: Session = Depends(get_db)):
    return crud.get_stores_with_product(db, product_id)
