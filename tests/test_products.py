from tests.helpers import make_product


class TestCreateProduct:
    def test_happy_path(self, client):
        r = client.post("/products/", json={"product_name": "Full Cream Milk", "size": "2L"})
        assert r.status_code == 200
        data = r.json()
        assert data["product_name"] == "Full Cream Milk"
        assert data["size"] == "2L"
        assert isinstance(data["product_id"], int)
        assert data["description"] is None
        assert data["image"] is None

    def test_with_optional_fields(self, client):
        r = client.post("/products/", json={
            "product_name": "Coca-Cola",
            "size": "375ml",
            "description": "Classic soft drink",
            "image": "https://example.com/coke.png",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["description"] == "Classic soft drink"
        assert data["image"] == "https://example.com/coke.png"

    def test_missing_name_returns_422(self, client):
        r = client.post("/products/", json={"size": "1L"})
        assert r.status_code == 422

    def test_missing_size_returns_422(self, client):
        r = client.post("/products/", json={"product_name": "Milk"})
        assert r.status_code == 422


class TestReadProducts:
    def test_list_empty(self, client):
        assert client.get("/products/").json() == []

    def test_list_returns_all(self, client):
        make_product(client, "Milk", "1L")
        make_product(client, "Bread", "700g")
        r = client.get("/products/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_by_id(self, client):
        product = make_product(client)
        r = client.get(f"/products/{product['product_id']}")
        assert r.status_code == 200
        assert r.json()["product_name"] == product["product_name"]

    def test_get_by_id_not_found(self, client):
        r = client.get("/products/99999")
        assert r.status_code == 404
        assert r.json()["detail"] == "Product not found"

    def test_pagination(self, client):
        for i in range(5):
            make_product(client, f"Product {i}", "1kg")
        r = client.get("/products/?skip=2&limit=2")
        assert r.status_code == 200
        assert len(r.json()) == 2


class TestSearchProducts:
    def test_search_returns_matching(self, client):
        make_product(client, "Full Cream Milk", "2L")
        make_product(client, "Skim Milk", "1L")
        make_product(client, "Orange Juice", "1L")
        r = client.get("/products/search/?q=milk")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 2
        names = [p["product_name"] for p in results]
        assert all("Milk" in n for n in names)

    def test_search_case_insensitive(self, client):
        make_product(client, "Full Cream Milk", "1L")
        r = client.get("/products/search/?q=MILK")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_search_no_match_returns_empty(self, client):
        make_product(client, "Bread", "700g")
        r = client.get("/products/search/?q=coffee")
        assert r.status_code == 200
        assert r.json() == []

    def test_search_requires_query(self, client):
        r = client.get("/products/search/")
        assert r.status_code == 422


class TestUpdateProduct:
    def test_update_name(self, client):
        product = make_product(client, "Old Name", "1L")
        r = client.put(f"/products/{product['product_id']}", json={"product_name": "New Name"})
        assert r.status_code == 200
        assert r.json()["product_name"] == "New Name"
        assert r.json()["size"] == "1L"  # unchanged

    def test_update_multiple_fields(self, client):
        product = make_product(client)
        r = client.put(f"/products/{product['product_id']}", json={
            "size": "2L",
            "description": "Updated",
        })
        assert r.status_code == 200
        assert r.json()["size"] == "2L"
        assert r.json()["description"] == "Updated"

    def test_update_not_found(self, client):
        r = client.put("/products/99999", json={"product_name": "Ghost"})
        assert r.status_code == 404


class TestDeleteProduct:
    def test_delete(self, client):
        product = make_product(client)
        r = client.delete(f"/products/{product['product_id']}")
        assert r.status_code == 200
        assert r.json()["detail"] == "Product deleted"

    def test_deleted_product_is_gone(self, client):
        product = make_product(client)
        client.delete(f"/products/{product['product_id']}")
        assert client.get(f"/products/{product['product_id']}").status_code == 404

    def test_delete_not_found(self, client):
        r = client.delete("/products/99999")
        assert r.status_code == 404
