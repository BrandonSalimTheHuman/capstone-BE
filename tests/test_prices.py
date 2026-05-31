from tests.helpers import make_store, make_product, make_price


class TestCreatePrice:
    def test_happy_path(self, client):
        store = make_store(client)
        product = make_product(client)
        r = client.post("/prices/", json={
            "product_id": product["product_id"],
            "store_id": store["store_id"],
            "price": "4.99",
        })
        assert r.status_code == 200
        data = r.json()
        assert float(data["price"]) == 4.99
        assert data["is_special"] is False
        assert isinstance(data["price_id"], int)

    def test_special_price(self, client):
        store = make_store(client)
        product = make_product(client)
        r = client.post("/prices/", json={
            "product_id": product["product_id"],
            "store_id": store["store_id"],
            "price": "2.50",
            "is_special": True,
            "special_type": "Half Price",
            "special_buy_quantity": 2,
            "special_buy_price": "4.00",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["is_special"] is True
        assert data["special_type"] == "Half Price"
        assert data["special_buy_quantity"] == 2

    def test_missing_price_returns_422(self, client):
        store = make_store(client)
        product = make_product(client)
        r = client.post("/prices/", json={
            "product_id": product["product_id"],
            "store_id": store["store_id"],
        })
        assert r.status_code == 422


class TestReadPrices:
    def test_list_empty(self, client):
        assert client.get("/prices/").json() == []

    def test_list_returns_all(self, client):
        store = make_store(client)
        product = make_product(client)
        make_price(client, product["product_id"], store["store_id"], "3.00")
        make_price(client, product["product_id"], store["store_id"], "3.50")
        r = client.get("/prices/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_by_id(self, client):
        store = make_store(client)
        product = make_product(client)
        price = make_price(client, product["product_id"], store["store_id"])
        r = client.get(f"/prices/{price['price_id']}")
        assert r.status_code == 200
        assert r.json()["price_id"] == price["price_id"]

    def test_get_by_id_not_found(self, client):
        r = client.get("/prices/99999")
        assert r.status_code == 404
        assert r.json()["detail"] == "Price not found"

    def test_prices_by_product(self, client):
        store = make_store(client)
        product_a = make_product(client, "Milk", "1L")
        product_b = make_product(client, "Bread", "700g")
        make_price(client, product_a["product_id"], store["store_id"], "3.00")
        make_price(client, product_a["product_id"], store["store_id"], "3.20")
        make_price(client, product_b["product_id"], store["store_id"], "4.00")
        r = client.get(f"/prices/product/{product_a['product_id']}")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 2
        assert all(p["product_id"] == product_a["product_id"] for p in results)

    def test_prices_by_store(self, client):
        store_a = make_store(client, "Woolworths", "https://woolworths.com.au")
        store_b = make_store(client, "Coles", "https://coles.com.au")
        product = make_product(client)
        make_price(client, product["product_id"], store_a["store_id"], "3.00")
        make_price(client, product["product_id"], store_b["store_id"], "3.50")
        r = client.get(f"/prices/store/{store_a['store_id']}")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 1
        assert results[0]["store_id"] == store_a["store_id"]

    def test_specials_endpoint(self, client):
        store = make_store(client)
        product = make_product(client)
        make_price(client, product["product_id"], store["store_id"], "5.00", is_special=False)
        make_price(client, product["product_id"], store["store_id"], "2.50", is_special=True)
        r = client.get("/prices/specials/")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 1
        assert results[0]["is_special"] is True


class TestComparePrices:
    def test_compare_across_stores(self, client):
        store_a = make_store(client, "Woolworths", "https://woolworths.com.au")
        store_b = make_store(client, "Coles", "https://coles.com.au")
        product = make_product(client)
        make_price(client, product["product_id"], store_a["store_id"], "3.00")
        make_price(client, product["product_id"], store_b["store_id"], "2.80")
        r = client.get(f"/prices/compare/{product['product_id']}")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 2
        store_ids = {p["store_id"] for p in results}
        assert store_a["store_id"] in store_ids
        assert store_b["store_id"] in store_ids

    def test_compare_returns_only_latest_per_store(self, client):
        store = make_store(client)
        product = make_product(client)
        make_price(client, product["product_id"], store["store_id"], "4.00")
        make_price(client, product["product_id"], store["store_id"], "3.50")
        r = client.get(f"/prices/compare/{product['product_id']}")
        assert r.status_code == 200
        assert len(r.json()) == 1  # one entry per store

    def test_compare_empty_returns_empty_list(self, client):
        store = make_store(client)
        product = make_product(client)
        r = client.get(f"/prices/compare/{product['product_id']}")
        assert r.status_code == 200
        assert r.json() == []

    def test_cheapest_store(self, client):
        store_a = make_store(client, "Cheap Store", "https://cheap.com")
        store_b = make_store(client, "Expensive Store", "https://expensive.com")
        product = make_product(client)
        make_price(client, product["product_id"], store_a["store_id"], "1.99")
        make_price(client, product["product_id"], store_b["store_id"], "3.99")
        r = client.get(f"/prices/cheapest/{product['product_id']}")
        assert r.status_code == 200
        assert r.json()["store_id"] == store_a["store_id"]
        assert float(r.json()["price"]) == 1.99

    def test_cheapest_no_prices_returns_404(self, client):
        product = make_product(client)
        r = client.get(f"/prices/cheapest/{product['product_id']}")
        assert r.status_code == 404
        assert r.json()["detail"] == "No prices found for product"


class TestUpdatePrice:
    def test_update_price_value(self, client):
        store = make_store(client)
        product = make_product(client)
        price = make_price(client, product["product_id"], store["store_id"], "5.00")
        r = client.put(f"/prices/{price['price_id']}", json={"price": "4.50"})
        assert r.status_code == 200
        assert float(r.json()["price"]) == 4.50

    def test_update_not_found(self, client):
        r = client.put("/prices/99999", json={"price": "1.00"})
        assert r.status_code == 404


class TestDeletePrice:
    def test_delete(self, client):
        store = make_store(client)
        product = make_product(client)
        price = make_price(client, product["product_id"], store["store_id"])
        r = client.delete(f"/prices/{price['price_id']}")
        assert r.status_code == 200
        assert r.json()["detail"] == "Price deleted"

    def test_deleted_price_is_gone(self, client):
        store = make_store(client)
        product = make_product(client)
        price = make_price(client, product["product_id"], store["store_id"])
        client.delete(f"/prices/{price['price_id']}")
        assert client.get(f"/prices/{price['price_id']}").status_code == 404

    def test_delete_not_found(self, client):
        assert client.delete("/prices/99999").status_code == 404
