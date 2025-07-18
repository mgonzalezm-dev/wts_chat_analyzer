"""Unit tests for authentication and authorization."""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    decode_token,
    create_password_reset_token,
    verify_password_reset_token
)
from app.core.config import settings
from app.models.user import User
from app.services.auth_service import AuthService


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_password_hash_creation(self):
        """Test creating password hash."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 chars
        assert hashed.startswith("$2b$")  # Bcrypt prefix
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "TestPassword456"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_different_hashes_same_password(self):
        """Test that same password produces different hashes."""
        password = "SamePassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenCreation:
    """Test JWT token creation."""
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_create_access_token(self):
        """Test creating access token."""
        user_id = "test-user-123"
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Decode and verify
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_create_access_token_with_expiry(self):
        """Test creating access token with custom expiry."""
        user_id = "test-user-456"
        expires_delta = timedelta(minutes=15)
        token = create_access_token(user_id, expires_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        
        # Check expiry is approximately correct (within 1 minute)
        expected_exp = datetime.utcnow() + expires_delta
        assert abs((exp_time - expected_exp).total_seconds()) < 60
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_create_refresh_token(self):
        """Test creating refresh token."""
        user_id = "test-user-789"
        token = create_refresh_token(user_id)
        
        assert isinstance(token, str)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_token_expiration(self):
        """Test that expired tokens are rejected."""
        user_id = "test-user"
        # Create token that expires immediately
        token = create_access_token(user_id, timedelta(seconds=-1))
        
        with pytest.raises(JWTError):
            decode_token(token)


class TestTokenDecoding:
    """Test JWT token decoding."""
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = "decode-test-user"
        token = create_access_token(user_id)
        
        decoded = decode_token(token)
        assert decoded["sub"] == user_id
        assert "exp" in decoded
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.jwt.token"
        
        with pytest.raises(JWTError):
            decode_token(invalid_token)
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_decode_tampered_token(self):
        """Test decoding tampered token."""
        user_id = "tamper-test"
        token = create_access_token(user_id)
        
        # Tamper with token
        parts = token.split(".")
        tampered_token = f"{parts[0]}.tampered.{parts[2]}"
        
        with pytest.raises(JWTError):
            decode_token(tampered_token)


class TestPasswordReset:
    """Test password reset token functionality."""
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_create_password_reset_token(self):
        """Test creating password reset token."""
        email = "reset@example.com"
        token = create_password_reset_token(email)
        
        assert isinstance(token, str)
        assert len(token) > 50
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_verify_password_reset_token_success(self):
        """Test verifying valid password reset token."""
        email = "valid@example.com"
        token = create_password_reset_token(email)
        
        verified_email = verify_password_reset_token(token)
        assert verified_email == email
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_verify_password_reset_token_expired(self):
        """Test verifying expired password reset token."""
        email = "expired@example.com"
        
        # Create expired token
        expire = datetime.utcnow() - timedelta(hours=1)
        to_encode = {"sub": email, "exp": expire, "type": "password_reset"}
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        verified_email = verify_password_reset_token(token)
        assert verified_email is None
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_verify_password_reset_token_invalid(self):
        """Test verifying invalid password reset token."""
        invalid_token = "invalid.reset.token"
        
        verified_email = verify_password_reset_token(invalid_token)
        assert verified_email is None


class TestAuthService:
    """Test authentication service."""
    
    @pytest.fixture
    def auth_service(self, db_session):
        """Create auth service instance."""
        return AuthService(db_session)
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_authenticate_user_success(self, auth_service, test_user):
        """Test successful user authentication."""
        authenticated = auth_service.authenticate_user(
            email="test@example.com",
            password="testpassword"
        )
        
        assert authenticated is not None
        assert authenticated.id == test_user.id
        assert authenticated.email == test_user.email
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_authenticate_user_wrong_password(self, auth_service, test_user):
        """Test authentication with wrong password."""
        authenticated = auth_service.authenticate_user(
            email="test@example.com",
            password="wrongpassword"
        )
        
        assert authenticated is None
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_authenticate_user_not_found(self, auth_service):
        """Test authentication with non-existent user."""
        authenticated = auth_service.authenticate_user(
            email="nonexistent@example.com",
            password="anypassword"
        )
        
        assert authenticated is None
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_authenticate_inactive_user(self, auth_service, db_session):
        """Test authentication with inactive user."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Inactive User",
            is_active=False,
            roles=["user"]
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        authenticated = auth_service.authenticate_user(
            email="inactive@example.com",
            password="password"
        )
        
        assert authenticated is None
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_create_user_tokens(self, auth_service, test_user):
        """Test creating user tokens."""
        tokens = auth_service.create_user_tokens(test_user)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Verify tokens
        access_payload = decode_token(tokens["access_token"])
        assert access_payload["sub"] == test_user.id
        
        refresh_payload = decode_token(tokens["refresh_token"])
        assert refresh_payload["sub"] == test_user.id
        assert refresh_payload["type"] == "refresh"
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_refresh_access_token(self, auth_service, test_user):
        """Test refreshing access token."""
        # Create initial tokens
        tokens = auth_service.create_user_tokens(test_user)
        refresh_token = tokens["refresh_token"]
        
        # Refresh access token
        new_access_token = auth_service.refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        assert new_access_token != tokens["access_token"]
        
        # Verify new token
        payload = decode_token(new_access_token)
        assert payload["sub"] == test_user.id
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_refresh_with_invalid_token(self, auth_service):
        """Test refreshing with invalid token."""
        invalid_token = "invalid.refresh.token"
        
        new_access_token = auth_service.refresh_access_token(invalid_token)
        assert new_access_token is None
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_refresh_with_access_token(self, auth_service, test_user):
        """Test refreshing with access token instead of refresh token."""
        access_token = create_access_token(test_user.id)
        
        # Should fail because it's not a refresh token
        new_access_token = auth_service.refresh_access_token(access_token)
        assert new_access_token is None
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_verify_user_permissions(self, auth_service, test_user, admin_user):
        """Test verifying user permissions."""
        # Regular user should not have admin permissions
        assert auth_service.verify_user_permission(test_user, "admin") is False
        assert auth_service.verify_user_permission(test_user, "user") is True
        
        # Admin user should have both permissions
        assert auth_service.verify_user_permission(admin_user, "admin") is True
        assert auth_service.verify_user_permission(admin_user, "user") is True
    
    @pytest.mark.unit
    @pytest.mark.auth
    def test_update_last_login(self, auth_service, test_user, db_session):
        """Test updating user's last login timestamp."""
        original_login = test_user.last_login
        
        auth_service.update_last_login(test_user)
        db_session.refresh(test_user)
        
        assert test_user.last_login is not None
        assert test_user.last_login > original_login if original_login else True
        assert (datetime.utcnow() - test_user.last_login).total_seconds() < 5