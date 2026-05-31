from tests.helpers import make_store


class TestCreateStore:
    def test_happy_path(self, client):
        r = client.post("/stores/", json={"store_name": "Coles", "url": "https://coles.com.au"})
        assert r.status_code == 200
        data = r.json()
        assert data["store_name"] == "Coles"
        assert data["url"] == "https://coles.com.au"
        assert isinstance(data["store_id"], int)

    def test_missing_url_returns_422(self, client):
        r = client.post("/stores/", json={"store_name": "Coles"})
        assert r.status_code == 422

    def test_missing_name_returns_422(self, client):
        r = client.post("/stores/", json={"url": "https://coles.com.au"})
        assert r.status_code == 422

    def test_empty_body_returns_422(self, client):
        r = client.post("/stores/", json={})
        assert r.status_code == 422


class TestReadStores:
    def test_list_empty(self, client):
        r = client.get("/stores/")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_multiple(self, client):
        make_store(client, "Woolworths", "https://woolworths.com.au")
        make_store(client, "Coles", "https://coles.com.au")
        r = client.get("/stores/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_by_id(self, client):
        store = make_store(client)
        r = client.get(f"/stores/{store['store_id']}")
        assert r.status_code == 200
        assert r.json()["store_name"] == store["store_name"]

    def test_get_by_id_not_found(self, client):
        r = client.get("/stores/99999")
        assert r.status_code == 404
        assert r.json()["detail"] == "Store not found"

    def test_pagination_skip(self, client):
        make_store(client, "Store A", "https://a.com")
        make_store(client, "Store B", "https://b.com")
        r = client.get("/stores/?skip=1&limit=10")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_pagination_limit(self, client):
        for i in range(5):
            make_store(client, f"Store {i}", f"https://store{i}.com")
        r = client.get("/stores/?limit=3")
        assert r.status_code == 200
        assert len(r.json()) == 3


class TestUpdateStore:
    def test_update_name(self, client):
        store = make_store(client, "Woolworths", "https://woolworths.com.au")
        r = client.put(f"/stores/{store['store_id']}", json={"store_name": "Woolies"})
        assert r.status_code == 200
        assert r.json()["store_name"] == "Woolies"
        assert r.json()["url"] == "https://woolworths.com.au"  # unchanged

    def test_update_url(self, client):
        store = make_store(client)
        r = client.put(f"/stores/{store['store_id']}", json={"url": "https://new-url.com"})
        assert r.status_code == 200
        assert r.json()["url"] == "https://new-url.com"

    def test_update_not_found(self, client):
        r = client.put("/stores/99999", json={"store_name": "Ghost"})
        assert r.status_code == 404


class TestDeleteStore:
    def test_delete(self, client):
        store = make_store(client)
        r = client.delete(f"/stores/{store['store_id']}")
        assert r.status_code == 200
        assert r.json()["detail"] == "Store deleted"

    def test_deleted_store_is_gone(self, client):
        store = make_store(client)
        client.delete(f"/stores/{store['store_id']}")
        r = client.get(f"/stores/{store['store_id']}")
        assert r.status_code == 404

    def test_delete_not_found(self, client):
        r = client.delete("/stores/99999")
        assert r.status_code == 404
