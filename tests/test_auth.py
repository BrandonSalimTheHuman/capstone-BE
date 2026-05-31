from unittest.mock import MagicMock, patch


def _mock_supabase():
    """Return a pre-configured mock supabase client."""
    return MagicMock()


class TestRegister:
    def test_register_success(self, client):
        mock_sup = _mock_supabase()
        mock_user = MagicMock()
        mock_user.id = "uuid-abc-123"
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = None
        mock_sup.auth.sign_up.return_value = MagicMock(user=mock_user)

        with patch("main.supabase", mock_sup):
            r = client.post("/auth/register", json={
                "email": "test@example.com",
                "password": "securepassword",
            })
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "test@example.com"
        assert data["user_id"] == "uuid-abc-123"
        assert data["email_confirmed"] is False

    def test_register_email_confirmed(self, client):
        mock_sup = _mock_supabase()
        mock_user = MagicMock()
        mock_user.id = "uuid-confirmed"
        mock_user.email = "confirmed@example.com"
        mock_user.email_confirmed_at = "2024-01-01T00:00:00Z"
        mock_sup.auth.sign_up.return_value = MagicMock(user=mock_user)

        with patch("main.supabase", mock_sup):
            r = client.post("/auth/register", json={
                "email": "confirmed@example.com",
                "password": "password123",
            })
        assert r.status_code == 201
        assert r.json()["email_confirmed"] is True

    def test_register_supabase_unavailable(self, client):
        with patch("main.supabase", None):
            r = client.post("/auth/register", json={
                "email": "test@example.com",
                "password": "password123",
            })
        assert r.status_code == 503

    def test_register_supabase_raises_exception(self, client):
        mock_sup = _mock_supabase()
        mock_sup.auth.sign_up.side_effect = Exception("Email already in use")

        with patch("main.supabase", mock_sup):
            r = client.post("/auth/register", json={
                "email": "dupe@example.com",
                "password": "password123",
            })
        assert r.status_code == 400

    def test_register_invalid_email_returns_422(self, client):
        r = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
        })
        assert r.status_code == 422

    def test_register_missing_password_returns_422(self, client):
        r = client.post("/auth/register", json={"email": "test@example.com"})
        assert r.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        mock_sup = _mock_supabase()
        mock_session = MagicMock()
        mock_session.access_token = "jwt-token-xyz"
        mock_sup.auth.sign_in_with_password.return_value = MagicMock(session=mock_session)

        with patch("main.supabase", mock_sup):
            r = client.post("/auth/login", json={
                "email": "user@example.com",
                "password": "password123",
            })
        assert r.status_code == 200
        data = r.json()
        assert data["access_token"] == "jwt-token-xyz"
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        mock_sup = _mock_supabase()
        mock_sup.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")

        with patch("main.supabase", mock_sup):
            r = client.post("/auth/login", json={
                "email": "user@example.com",
                "password": "wrongpassword",
            })
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid email or password"

    def test_login_supabase_unavailable(self, client):
        with patch("main.supabase", None):
            r = client.post("/auth/login", json={
                "email": "user@example.com",
                "password": "password123",
            })
        assert r.status_code == 503

    def test_login_invalid_email_returns_422(self, client):
        r = client.post("/auth/login", json={
            "email": "not-email",
            "password": "password123",
        })
        assert r.status_code == 422


class TestGetMe:
    def test_get_me_no_token_returns_403(self, client):
        r = client.get("/auth/me")
        assert r.status_code == 403  # missing bearer scheme

    def test_get_me_with_valid_token(self, client):
        mock_sup = _mock_supabase()
        mock_user = MagicMock()
        mock_user.id = "me-uuid"
        mock_user.email = "me@example.com"
        mock_user.email_confirmed_at = "2024-01-01"
        mock_sup.auth.get_user.return_value = MagicMock(user=mock_user)

        with patch("main.supabase", mock_sup), patch("auth.auth.supabase", mock_sup):
            r = client.get("/auth/me", headers={"Authorization": "Bearer valid-jwt"})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == "me@example.com"
        assert data["user_id"] == "me-uuid"

    def test_get_me_invalid_token_returns_401(self, client):
        mock_sup = _mock_supabase()
        mock_sup.auth.get_user.return_value = MagicMock(user=None)

        with patch("auth.auth.supabase", mock_sup):
            r = client.get("/auth/me", headers={"Authorization": "Bearer bad-jwt"})
        assert r.status_code == 401
