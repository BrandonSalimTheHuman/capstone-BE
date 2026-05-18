import os
import re
import psycopg2
from psycopg2 import extras

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


def _normalize_unit_price(raw):
    return raw if raw and raw != "N/A" else None


def _normalize_complex_discount(cd):
    if not isinstance(cd, dict):
        return False, None, None

    try:
        special_qty = int(cd.get("Quantity", 0))
    except (ValueError, TypeError):
        special_qty = None

    try:
        special_price = float(cd.get("Price", 0))
    except (ValueError, TypeError):
        special_price = None

    return True, special_qty, special_price


def upload_products(products: list, store_name: str, batch_size: int = 5000) -> None:
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
            raise ValueError(
                f"Store '{store_name}' not found in the database. "
                "Make sure the stores table is seeded."
            )
        store_id = row[0]

        total_uploaded = 0
        total_duplicates_skipped = 0
        total_products = len(products)

        for i in range(0, total_products, batch_size):
            batch = products[i : i + batch_size]
            items_by_name = {}
            batch_duplicates_count = 0

            for item in batch:
                name = (item.get("Product Name") or "").strip()
                if not name:
                    continue

                price_val = _parse_price(item.get("Price", "0"))

                if name in items_by_name:
                    batch_duplicates_count += 1
                    # If the new tile isn't strictly cheaper than what we already stored, skip it
                    if price_val >= items_by_name[name]["price_val"]:
                        continue

                unit_price = _normalize_unit_price(
                    item.get("Unit Price") or item.get("unit_price")
                )
                image = item.get("Image") or item.get("Image url") or None
                size = _extract_size(name)
                is_special, special_qty, special_price = _normalize_complex_discount(
                    item.get("Complex discount") or item.get("Complex Discount")
                )

                items_by_name[name] = {
                    "size": size,
                    "image": image,
                    "price_val": price_val,
                    "unit_price": unit_price,
                    "is_special": is_special,
                    "special_qty": special_qty,
                    "special_price": special_price,
                }

            if not items_by_name:
                continue

            try:
                product_names = list(items_by_name.keys())
                cur.execute(
                    "SELECT product_id, product_name, image FROM products WHERE product_name = ANY(%s)",
                    (product_names,),
                )
                existing_products = {
                    row[1]: {"product_id": row[0], "image": row[2]}
                    for row in cur.fetchall()
                }

                new_products = [
                    (name, data["size"], data["image"])
                    for name, data in items_by_name.items()
                    if name not in existing_products
                ]

                if new_products:
                    extras.execute_values(
                        cur,
                        "INSERT INTO products (product_name, size, image) VALUES %s RETURNING product_id, product_name",
                        new_products,
                        template="(%s, %s, %s)",
                        page_size=1000,
                    )
                    for product_id, product_name in cur.fetchall():
                        existing_products[product_name] = {
                            "product_id": product_id,
                            "image": items_by_name[product_name]["image"],
                        }

                image_updates = [
                    (product_info["product_id"], items_by_name[name]["image"])
                    for name, product_info in existing_products.items()
                    if items_by_name[name]["image"]
                    and product_info["image"] is None
                ]

                if image_updates:
                    extras.execute_values(
                        cur,
                        "UPDATE products SET image = data.image FROM (VALUES %s) AS data(product_id, image) "
                        "WHERE products.product_id = data.product_id AND products.image IS NULL",
                        image_updates,
                        template="(%s, %s)",
                        page_size=1000,
                    )

                product_ids = [info["product_id"] for info in existing_products.values()]
                last_prices = {}
                if product_ids:
                    cur.execute(
                        "SELECT DISTINCT ON (product_id) product_id, price "
                        "FROM prices WHERE product_id = ANY(%s) AND store_id = %s "
                        "ORDER BY product_id, date_recorded DESC",
                        (product_ids, store_id),
                    )
                    last_prices = {row[0]: row[1] for row in cur.fetchall()}

                price_rows = []
                store_rows = []
                for name, data in items_by_name.items():
                    product_id = existing_products[name]["product_id"]
                    previous_price = last_prices.get(product_id)
                    if previous_price is None or abs(float(previous_price) - data["price_val"]) > 0.005:
                        price_rows.append(
                            (
                                product_id,
                                store_id,
                                data["price_val"],
                                data["unit_price"],
                                data["is_special"],
                                data["special_qty"],
                                data["special_price"],
                            )
                        )

                    store_rows.append((store_id, product_id))

                if price_rows:
                    extras.execute_values(
                        cur,
                        "INSERT INTO prices "
                        "(product_id, store_id, price, unit_price, date_recorded, "
                        "is_special, special_buy_quantity, special_buy_price) "
                        "VALUES %s",
                        price_rows,
                        template="(%s, %s, %s, %s, NOW(), %s, %s, %s)",
                        page_size=1000,
                    )

                if store_rows:
                    extras.execute_values(
                        cur,
                        "INSERT INTO store_products (store_id, product_id, is_available, last_updated) "
                        "VALUES %s ON CONFLICT (store_id, product_id) "
                        "DO UPDATE SET is_available = TRUE, last_updated = NOW()",
                        store_rows,
                        template="(%s, %s, TRUE, NOW())",
                        page_size=1000,
                    )

                total_uploaded += len(items_by_name)
                total_duplicates_skipped += batch_duplicates_count
                conn.commit()
                print(
                    f"[db_upload] Committed batch {i // batch_size + 1}: processed {total_uploaded}/{total_products} items."
                )

            except Exception:
                conn.rollback()
                raise

        print(
            f"[db_upload] Completed! Total committed: {total_uploaded} products for '{store_name}'"
        )
        if total_duplicates_skipped > 0:
            print(
                f"[db_upload] Note: Skipped {total_duplicates_skipped} duplicate product entries (retained cheaper options)."
            )

    finally:
        cur.close()
        conn.close()
