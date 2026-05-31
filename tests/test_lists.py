from tests.helpers import make_store, make_product, make_parent_list, make_store_list, make_item


class TestParentList:
    def test_create_list(self, client):
        r = client.post("/lists/", json={"user_id": "user-1", "list_name": "My Groceries"})
        assert r.status_code == 200
        data = r.json()
        assert data["list_name"] == "My Groceries"
        assert data["user_id"] == "user-1"
        assert isinstance(data["parent_list_id"], int)
        assert data["store_lists"] == []

    def test_create_list_missing_field_returns_422(self, client):
        r = client.post("/lists/", json={"user_id": "user-1"})
        assert r.status_code == 422

    def test_get_list_by_id(self, client):
        lst = make_parent_list(client)
        r = client.get(f"/lists/{lst['parent_list_id']}")
        assert r.status_code == 200
        assert r.json()["parent_list_id"] == lst["parent_list_id"]

    def test_get_list_not_found(self, client):
        r = client.get("/lists/99999")
        assert r.status_code == 404
        assert r.json()["detail"] == "List not found"

    def test_get_lists_by_user(self, client):
        make_parent_list(client, user_id="user-A", list_name="List 1")
        make_parent_list(client, user_id="user-A", list_name="List 2")
        make_parent_list(client, user_id="user-B", list_name="Other")
        r = client.get("/lists/user/user-A")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 2
        assert all(l["user_id"] == "user-A" for l in results)

    def test_get_lists_user_no_lists(self, client):
        r = client.get("/lists/user/nobody")
        assert r.status_code == 200
        assert r.json() == []

    def test_update_list_name(self, client):
        lst = make_parent_list(client, list_name="Old Name")
        r = client.put(f"/lists/{lst['parent_list_id']}", json={"list_name": "New Name"})
        assert r.status_code == 200
        assert r.json()["list_name"] == "New Name"

    def test_update_list_not_found(self, client):
        r = client.put("/lists/99999", json={"list_name": "Ghost"})
        assert r.status_code == 404

    def test_delete_list(self, client):
        lst = make_parent_list(client)
        r = client.delete(f"/lists/{lst['parent_list_id']}")
        assert r.status_code == 200
        assert r.json()["detail"] == "List deleted"

    def test_deleted_list_is_gone(self, client):
        lst = make_parent_list(client)
        client.delete(f"/lists/{lst['parent_list_id']}")
        assert client.get(f"/lists/{lst['parent_list_id']}").status_code == 404

    def test_delete_list_not_found(self, client):
        assert client.delete("/lists/99999").status_code == 404


class TestListSharing:
    def test_generate_share_token(self, client):
        lst = make_parent_list(client)
        r = client.post(f"/lists/{lst['parent_list_id']}/share")
        assert r.status_code == 200
        token = r.json()["share_token"]
        assert isinstance(token, str) and len(token) > 0

    def test_share_token_persisted_on_list(self, client):
        lst = make_parent_list(client)
        token = client.post(f"/lists/{lst['parent_list_id']}/share").json()["share_token"]
        updated = client.get(f"/lists/{lst['parent_list_id']}").json()
        assert updated["share_token"] == token

    def test_share_not_found_returns_404(self, client):
        r = client.post("/lists/99999/share")
        assert r.status_code == 404

    def test_import_shared_list(self, client):
        store = make_store(client)
        product = make_product(client)
        lst = make_parent_list(client, user_id="original-user", list_name="Family Shop")
        sl = make_store_list(client, lst["parent_list_id"], store["store_id"])
        make_item(client, sl["store_list_id"], product["product_id"], quantity=3)

        token = client.post(f"/lists/{lst['parent_list_id']}/share").json()["share_token"]
        r = client.post(f"/lists/import/{token}", json={"user_id": "new-user"})
        assert r.status_code == 200
        imported = r.json()
        assert imported["user_id"] == "new-user"
        assert imported["list_name"] == "Family Shop"
        assert len(imported["store_lists"]) == 1
        assert len(imported["store_lists"][0]["items"]) == 1
        assert imported["store_lists"][0]["items"][0]["quantity"] == 3
        assert imported["store_lists"][0]["items"][0]["is_checked"] is False

    def test_import_invalid_token_returns_404(self, client):
        r = client.post("/lists/import/not-a-real-token", json={"user_id": "someone"})
        assert r.status_code == 404


class TestStoreLists:
    def test_create_store_list(self, client):
        store = make_store(client)
        lst = make_parent_list(client)
        r = client.post(f"/lists/{lst['parent_list_id']}/stores/", json={"store_id": store["store_id"]})
        assert r.status_code == 200
        data = r.json()
        assert data["store_id"] == store["store_id"]
        assert data["parent_list_id"] == lst["parent_list_id"]

    def test_get_store_list(self, client):
        store = make_store(client)
        lst = make_parent_list(client)
        sl = make_store_list(client, lst["parent_list_id"], store["store_id"])
        r = client.get(f"/store-lists/{sl['store_list_id']}")
        assert r.status_code == 200
        assert r.json()["store_list_id"] == sl["store_list_id"]

    def test_get_store_list_not_found(self, client):
        r = client.get("/store-lists/99999")
        assert r.status_code == 404

    def test_store_list_embedded_in_parent(self, client):
        store = make_store(client)
        lst = make_parent_list(client)
        make_store_list(client, lst["parent_list_id"], store["store_id"])
        r = client.get(f"/lists/{lst['parent_list_id']}")
        assert r.status_code == 200
        assert len(r.json()["store_lists"]) == 1

    def test_delete_store_list(self, client):
        store = make_store(client)
        lst = make_parent_list(client)
        sl = make_store_list(client, lst["parent_list_id"], store["store_id"])
        r = client.delete(f"/store-lists/{sl['store_list_id']}")
        assert r.status_code == 200
        assert r.json()["detail"] == "Store list deleted"

    def test_delete_store_list_not_found(self, client):
        assert client.delete("/store-lists/99999").status_code == 404


class TestStoreListItems:
    def _setup(self, client):
        store = make_store(client)
        product = make_product(client)
        lst = make_parent_list(client)
        sl = make_store_list(client, lst["parent_list_id"], store["store_id"])
        return sl, product

    def test_create_item(self, client):
        sl, product = self._setup(client)
        r = client.post(f"/store-lists/{sl['store_list_id']}/items/", json={
            "product_id": product["product_id"],
            "quantity": 2,
            "is_checked": False,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["product_id"] == product["product_id"]
        assert data["quantity"] == 2
        assert data["is_checked"] is False

    def test_list_items(self, client):
        sl, product = self._setup(client)
        make_item(client, sl["store_list_id"], product["product_id"], quantity=1)
        make_item(client, sl["store_list_id"], product["product_id"], quantity=3)
        r = client.get(f"/store-lists/{sl['store_list_id']}/items/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_update_item_quantity(self, client):
        sl, product = self._setup(client)
        item = make_item(client, sl["store_list_id"], product["product_id"], quantity=1)
        r = client.put(f"/items/{item['list_item_id']}", json={"quantity": 5})
        assert r.status_code == 200
        assert r.json()["quantity"] == 5

    def test_update_item_not_found(self, client):
        r = client.put("/items/99999", json={"quantity": 1})
        assert r.status_code == 404

    def test_check_item(self, client):
        sl, product = self._setup(client)
        item = make_item(client, sl["store_list_id"], product["product_id"])
        assert item["is_checked"] is False
        r = client.post(f"/items/{item['list_item_id']}/check")
        assert r.status_code == 200
        assert r.json()["is_checked"] is True

    def test_uncheck_item(self, client):
        sl, product = self._setup(client)
        item = make_item(client, sl["store_list_id"], product["product_id"])
        client.post(f"/items/{item['list_item_id']}/check")
        r = client.post(f"/items/{item['list_item_id']}/uncheck")
        assert r.status_code == 200
        assert r.json()["is_checked"] is False

    def test_check_item_not_found(self, client):
        assert client.post("/items/99999/check").status_code == 404

    def test_uncheck_item_not_found(self, client):
        assert client.post("/items/99999/uncheck").status_code == 404

    def test_delete_item(self, client):
        sl, product = self._setup(client)
        item = make_item(client, sl["store_list_id"], product["product_id"])
        r = client.delete(f"/items/{item['list_item_id']}")
        assert r.status_code == 200
        assert r.json()["detail"] == "Item deleted"

    def test_delete_item_not_found(self, client):
        assert client.delete("/items/99999").status_code == 404

    def test_items_cascade_delete_with_store_list(self, client):
        sl, product = self._setup(client)
        make_item(client, sl["store_list_id"], product["product_id"])
        assert len(client.get(f"/store-lists/{sl['store_list_id']}/items/").json()) == 1
        client.delete(f"/store-lists/{sl['store_list_id']}")
        # Store list itself is gone
        assert client.get(f"/store-lists/{sl['store_list_id']}").status_code == 404
        # Items were cascade-deleted — endpoint returns empty list
        r = client.get(f"/store-lists/{sl['store_list_id']}/items/")
        assert r.status_code == 200
        assert r.json() == []
