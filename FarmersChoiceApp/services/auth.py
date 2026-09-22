from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class User:
    id: int
    name: str
    email: str
    department: str
    semester: str


class AuthError(ValueError):
    pass


class AuthService:
    def __init__(self, database_path: str | Path = "user_data.db") -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    department TEXT NOT NULL,
                    semester TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)

    @staticmethod
    def _hash_password(password: str, salt: bytes | None = None) -> str:
        salt = salt or os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
        return f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"

    @classmethod
    def _verify_password(cls, password: str, encoded: str) -> bool:
        try:
            algorithm, rounds, salt_hex, digest_hex = encoded.split("$")
            if algorithm != "pbkdf2_sha256" or int(rounds) != 310_000:
                return False
            expected = cls._hash_password(password, bytes.fromhex(salt_hex)).split("$")[-1]
            return hmac.compare_digest(expected, digest_hex)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _validate(name: str, email: str, password: str, department: str, semester: str) -> tuple[str, ...]:
        email = email.strip().lower()
        if not name.strip() or not department.strip() or not semester.strip():
            raise AuthError("Please complete every field.")
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise AuthError("Enter a valid email address.")
        if len(password) < 8:
            raise AuthError("Password must contain at least 8 characters.")
        return name.strip(), email, password, department.strip(), semester.strip()

    def register(self, name: str, email: str, password: str, department: str, semester: str) -> User:
        name, email, password, department, semester = self._validate(name, email, password, department, semester)
        try:
            with self._connection() as connection:
                cursor = connection.execute(
                    "INSERT INTO users (name, email, department, semester, password_hash) VALUES (?, ?, ?, ?, ?)",
                    (name, email, department, semester, self._hash_password(password)),
                )
                return User(cursor.lastrowid, name, email, department, semester)
        except sqlite3.IntegrityError as error:
            raise AuthError("An account with that email already exists.") from error

    def login(self, email: str, password: str) -> User:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        if not row or not self._verify_password(password, row["password_hash"]):
            raise AuthError("Email or password is incorrect.")
        return User(row["id"], row["name"], row["email"], row["department"], row["semester"])

    def update_profile(self, user_id: int, name: str, department: str, semester: str) -> User:
        if not name.strip() or not department.strip() or not semester.strip():
            raise AuthError("Please complete every profile field.")
        with self._connection() as connection:
            connection.execute("UPDATE users SET name = ?, department = ?, semester = ? WHERE id = ?", (name.strip(), department.strip(), semester.strip(), user_id))
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise AuthError("That account no longer exists.")
        return User(row["id"], row["name"], row["email"], row["department"], row["semester"])

    def create_reset_token(self, email: str) -> str:
        with self._connection() as connection:
            row = connection.execute("SELECT id FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
            if not row:
                raise AuthError("No account was found for that email.")
            token = secrets.token_urlsafe(24)
            connection.execute("INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, datetime('now', '+15 minutes'))", (row["id"], token))
            return token

    def reset_password(self, token: str, password: str) -> None:
        if len(password) < 8:
            raise AuthError("Password must contain at least 8 characters.")
        with self._connection() as connection:
            row = connection.execute("SELECT id, user_id FROM password_reset_tokens WHERE token = ? AND used = 0 AND expires_at > datetime('now')", (token.strip(),)).fetchone()
            if not row:
                raise AuthError("That reset code is invalid or expired.")
            connection.execute("UPDATE users SET password_hash = ? WHERE id = ?", (self._hash_password(password), row["user_id"]))
            connection.execute("UPDATE password_reset_tokens SET used = 1 WHERE id = ?", (row["id"],))