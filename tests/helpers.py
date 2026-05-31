"""
Shared factory helpers for building test fixtures via the HTTP client.
Each function creates one resource and asserts 200 so callers don't need to.
"""


def make_store(client, name="Woolworths", url="https://woolworths.com.au"):
    r = client.post("/stores/", json={"store_name": name, "url": url})
    assert r.status_code == 200, r.text
    return r.json()


def make_product(client, name="Full Cream Milk", size="1L", description=None, image=None):
    payload = {"product_name": name, "size": size}
    if description is not None:
        payload["description"] = description
    if image is not None:
        payload["image"] = image
    r = client.post("/products/", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def make_price(client, product_id, store_id, price="3.50", is_special=False, special_type=None):
    payload = {
        "product_id": product_id,
        "store_id": store_id,
        "price": price,
        "is_special": is_special,
    }
    if special_type:
        payload["special_type"] = special_type
    r = client.post("/prices/", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def make_parent_list(client, user_id="user-abc-123", list_name="Weekend Shop"):
    r = client.post("/lists/", json={"user_id": user_id, "list_name": list_name})
    assert r.status_code == 200, r.text
    return r.json()


def make_store_list(client, parent_list_id, store_id):
    r = client.post(f"/lists/{parent_list_id}/stores/", json={"store_id": store_id})
    assert r.status_code == 200, r.text
    return r.json()


def make_item(client, store_list_id, product_id, quantity=1):
    r = client.post(
        f"/store-lists/{store_list_id}/items/",
        json={"product_id": product_id, "quantity": quantity, "is_checked": False},
    )
    assert r.status_code == 200, r.text
    return r.json()
