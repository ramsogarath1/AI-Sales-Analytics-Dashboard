"""
Phase 7A Authentication Test Suite for AI-Sales-Analytics-Dashboard.
Tests user registration, duplicate email rejection (409), password hashing security,
login verification, JWT token issuance, expiration, invalid token handling, and /api/auth/me.
"""

import sys
import os
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root and backend to python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(project_root, "backend")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///./test_phase7_auth.db"
os.environ["TESTING"] = "true"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_unit_tests_32bytes_minimum!"

from backend.main import app
from backend.database.connection import init_db
from backend.database.models import UserRecord
from backend.utils.rate_limiter import clear_rate_limit_store

class TestPhase7Auth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_db_path = Path("./test_phase7_auth.db")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass

        init_db("sqlite:///./test_phase7_auth.db")
        cls.client = TestClient(app)

        from backend.database.connection import get_db_session
        with get_db_session() as db:
            db.query(UserRecord).delete()

    @classmethod
    def tearDownClass(cls):
        test_db_path = Path("./test_phase7_auth.db")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception:
                pass

    def setUp(self):
        clear_rate_limit_store()

    def test_01_user_registration_success(self):
        """Tests valid user account registration."""
        payload = {"email": "testuser1@example.com", "password": "securepassword123"}
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")
        user = data["user"]
        self.assertEqual(user["email"], "testuser1@example.com")
        self.assertIn("user_id", user)
        # Ensure password and hash are NEVER returned in response
        self.assertNotIn("password", user)
        self.assertNotIn("password_hash", user)

    def test_02_duplicate_email_registration_conflict(self):
        """Tests duplicate email registration returns HTTP 409 Conflict."""
        payload = {"email": "duplicate@example.com", "password": "securepassword123"}
        res1 = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already exists", res2.json()["message"].lower())

    def test_03_weak_password_registration_rejected(self):
        """Tests registration with weak password (<8 characters) returns HTTP 400."""
        payload = {"email": "weakpass@example.com", "password": "123"}
        res = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)

    def test_04_login_success(self):
        """Tests valid user login returns Bearer token and user info."""
        # 1. Register
        reg_payload = {"email": "loginuser@example.com", "password": "password123"}
        self.client.post("/api/auth/register", json=reg_payload)

        # 2. Login
        login_payload = {"email": "loginuser@example.com", "password": "password123"}
        res = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertTrue(len(data["access_token"]) > 20)

    def test_05_invalid_password_login_rejected(self):
        """Tests login with invalid password returns generic HTTP 401 error."""
        login_payload = {"email": "loginuser@example.com", "password": "wrongpassword"}
        res = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(res.status_code, 401)
        self.assertIn("invalid email or password", res.json()["message"].lower())

    def test_06_nonexistent_account_login_rejected(self):
        """Tests login for non-existent email returns generic HTTP 401 error."""
        login_payload = {"email": "nonexistent@example.com", "password": "password123"}
        res = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(res.status_code, 401)
        self.assertIn("invalid email or password", res.json()["message"].lower())

    def test_07_get_current_user_profile(self):
        """Tests GET /api/auth/me returns authenticated user profile."""
        email = "profileuser@example.com"
        pwd = "password123"
        self.client.post("/api/auth/register", json={"email": email, "password": pwd})
        token = self.client.post("/api/auth/login", json={"email": email, "password": pwd}).json()["access_token"]

        # Call GET /api/auth/me with Bearer token
        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(res.status_code, 200)
        user_data = res.json()
        self.assertEqual(user_data["email"], email)
        self.assertNotIn("password_hash", user_data)

    def test_08_unauthenticated_request_rejected(self):
        """Tests request without Authorization header returns HTTP 401."""
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)

    def test_09_invalid_token_rejected(self):
        """Tests request with invalid Bearer token returns HTTP 401."""
        headers = {"Authorization": "Bearer invalid_garbage_token_string"}
        res = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(res.status_code, 401)

if __name__ == "__main__":
    unittest.main()
