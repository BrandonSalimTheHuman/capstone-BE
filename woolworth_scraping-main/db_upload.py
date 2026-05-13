import os
import re
import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_SIZE_RE = re.compile(r'\b\d+(\.\d+)?\s*(kg|g|ml|l|pk|pack|pieces?|pcs?)\b', re.IGNORECASE)
_PRICE_RE = re.compile(r'[\d.]+')


def _extract_size(name: str) -> str:
    m = _SIZE_RE.search(name)
    return m.group(0).strip() if m else "N/A"


def _parse_price(raw) -> float:
    m = _PRICE_RE.search(str(raw))
    return float(m.group(0)) if m else 0.0


def upload_products(products: list, store_name: str) -> None:
    """Upsert scraped products into the database and mark them available.

    For each product:
      - Creates a new Product row if the name hasn't been seen before.
      - Inserts a new Price row only when the price has changed.
      - Upserts a StoreProduct row, setting is_available=True and refreshing last_updated.

    Args:
        products:   List of dicts returned by a scraper function.
        store_name: Partial store name used to look up the store row (case-insensitive LIKE match).
    """
    conn_str = os.environ.get("DATABASE_URL")
    if not conn_str:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT store_id FROM stores WHERE LOWER(store_name) LIKE %s LIMIT 1",
            (f"%{store_name.lower()}%",),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Store '{store_name}' not found in the database. "
                             "Make sure the stores table is seeded.")
        store_id = row[0]

        uploaded = 0
        for item in products:
            name = (item.get("Product Name") or "").strip()
            if not name:
                continue

            price_val = _parse_price(item.get("Price", "0"))
            unit_price_raw = item.get("Unit Price") or item.get("unit_price")
            unit_price = unit_price_raw if unit_price_raw and unit_price_raw != "N/A" else None
            image = item.get("Image") or item.get("Image url") or None
            size = _extract_size(name)

            cd = item.get("Complex discount") or item.get("Complex Discount")
            is_special = False
            special_qty = None
            special_price = None
            if isinstance(cd, dict):
                is_special = True
                try:
                    special_qty = int(cd.get("Quantity", 0))
                except (ValueError, TypeError):
                    special_qty = None
                try:
                    special_price = float(cd.get("Price", 0))
                except (ValueError, TypeError):
                    special_price = None

            # Find or create product (matched by exact name)
            cur.execute(
                "SELECT product_id FROM products WHERE product_name = %s LIMIT 1",
                (name,),
            )
            row = cur.fetchone()
            if row:
                product_id = row[0]
                if image:
                    cur.execute(
                        "UPDATE products SET image = %s WHERE product_id = %s AND image IS NULL",
                        (image, product_id),
                    )
            else:
                cur.execute(
                    "INSERT INTO products (product_name, size, image) "
                    "VALUES (%s, %s, %s) RETURNING product_id",
                    (name, size, image),
                )
                product_id = cur.fetchone()[0]

            # Insert a new price record only when the price has changed
            cur.execute(
                """
                SELECT price FROM prices
                WHERE product_id = %s AND store_id = %s
                ORDER BY date_recorded DESC LIMIT 1
                """,
                (product_id, store_id),
            )
            existing = cur.fetchone()
            if not existing or abs(float(existing[0]) - price_val) > 0.005:
                cur.execute(
                    """
                    INSERT INTO prices
                        (product_id, store_id, price, unit_price, date_recorded,
                         is_special, special_buy_quantity, special_buy_price)
                    VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s)
                    """,
                    (product_id, store_id, price_val, unit_price,
                     is_special, special_qty, special_price),
                )

            # Upsert availability — always refresh last_updated to mark as "seen this run"
            cur.execute(
                """
                INSERT INTO store_products (store_id, product_id, is_available, last_updated)
                VALUES (%s, %s, TRUE, NOW())
                ON CONFLICT (store_id, product_id)
                DO UPDATE SET is_available = TRUE, last_updated = NOW()
                """,
                (store_id, product_id),
            )

            uploaded += 1

        conn.commit()
        print(f"[db_upload] Committed {uploaded} products for '{store_name}'")

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()
