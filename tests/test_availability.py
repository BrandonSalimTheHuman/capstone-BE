from tests.helpers import make_store, make_product


class TestSetAvailability:
    def test_set_available(self, client):
        store = make_store(client)
        product = make_product(client)
        r = client.put(
            f"/stores/{store['store_id']}/products/{product['product_id']}/availability",
            json={"is_available": True},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["is_available"] is True
        assert data["store_id"] == store["store_id"]
        assert data["product_id"] == product["product_id"]
        assert isinstance(data["store_product_id"], int)

    def test_set_unavailable(self, client):
        store = make_store(client)
        product = make_product(client)
        r = client.put(
            f"/stores/{store['store_id']}/products/{product['product_id']}/availability",
            json={"is_available": False},
        )
        assert r.status_code == 200
        assert r.json()["is_available"] is False

    def test_update_existing_availability(self, client):
        store = make_store(client)
        product = make_product(client)
        base_url = f"/stores/{store['store_id']}/products/{product['product_id']}/availability"
        client.put(base_url, json={"is_available": True})
        r = client.put(base_url, json={"is_available": False})
        assert r.status_code == 200
        assert r.json()["is_available"] is False

    def test_upsert_creates_single_record(self, client):
        store = make_store(client)
        product = make_product(client)
        base_url = f"/stores/{store['store_id']}/products/{product['product_id']}/availability"
        client.put(base_url, json={"is_available": True})
        client.put(base_url, json={"is_available": False})
        r = client.get(base_url)
        assert r.status_code == 200
        # Only one record should exist (upsert semantics)
        r2 = client.get(f"/stores/{store['store_id']}/available-products")
        assert len(r2.json()) == 0  # it's unavailable now


class TestGetAvailability:
    def test_get_availability(self, client):
        store = make_store(client)
        product = make_product(client)
        client.put(
            f"/stores/{store['store_id']}/products/{product['product_id']}/availability",
            json={"is_available": True},
        )
        r = client.get(f"/stores/{store['store_id']}/products/{product['product_id']}/availability")
        assert r.status_code == 200
        assert r.json()["is_available"] is True

    def test_get_availability_not_found(self, client):
        store = make_store(client)
        product = make_product(client)
        r = client.get(f"/stores/{store['store_id']}/products/{product['product_id']}/availability")
        assert r.status_code == 404
        assert r.json()["detail"] == "No availability record found"


class TestAvailableProducts:
    def test_available_products_for_store(self, client):
        store = make_store(client)
        product_a = make_product(client, "Milk", "1L")
        product_b = make_product(client, "Bread", "700g")
        product_c = make_product(client, "Eggs", "12pk")
        base = f"/stores/{store['store_id']}/products"
        client.put(f"{base}/{product_a['product_id']}/availability", json={"is_available": True})
        client.put(f"{base}/{product_b['product_id']}/availability", json={"is_available": True})
        client.put(f"{base}/{product_c['product_id']}/availability", json={"is_available": False})
        r = client.get(f"/stores/{store['store_id']}/available-products")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 2
        assert all(p["is_available"] for p in results)

    def test_available_products_empty(self, client):
        store = make_store(client)
        r = client.get(f"/stores/{store['store_id']}/available-products")
        assert r.status_code == 200
        assert r.json() == []

    def test_store_availability_for_product(self, client):
        store_a = make_store(client, "Woolworths", "https://woolworths.com.au")
        store_b = make_store(client, "Coles", "https://coles.com.au")
        product = make_product(client)
        client.put(
            f"/stores/{store_a['store_id']}/products/{product['product_id']}/availability",
            json={"is_available": True},
        )
        client.put(
            f"/stores/{store_b['store_id']}/products/{product['product_id']}/availability",
            json={"is_available": False},
        )
        r = client.get(f"/products/{product['product_id']}/store-availability")
        assert r.status_code == 200
        assert len(r.json()) == 2
        store_ids = {sp["store_id"] for sp in r.json()}
        assert store_a["store_id"] in store_ids
        assert store_b["store_id"] in store_ids

    def test_store_availability_empty(self, client):
        product = make_product(client)
        r = client.get(f"/products/{product['product_id']}/store-availability")
        assert r.status_code == 200
        assert r.json() == []
