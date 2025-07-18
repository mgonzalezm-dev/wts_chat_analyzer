"""Shared test fixtures and configuration."""
import os
import pytest
from typing import Generator, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.security import get_password_hash

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Override settings for testing
settings.DATABASE_URL = TEST_DATABASE_URL
settings.SECRET_KEY = "test-secret-key"
settings.ALGORITHM = "HS256"
settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create test engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for tests."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
        roles=["user"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session) -> User:
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword"),
        full_name="Admin User",
        is_active=True,
        roles=["admin", "user"]
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> Dict[str, str]:
    """Create authentication headers for test user."""
    access_token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user) -> Dict[str, str]:
    """Create authentication headers for admin user."""
    access_token = create_access_token(admin_user.id)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_conversation(db_session, test_user) -> Conversation:
    """Create a test conversation."""
    conversation = Conversation(
        name="Test Conversation",
        user_id=test_user.id,
        file_path="/test/path/conversation.txt",
        file_size=1024,
        message_count=10,
        participant_count=2,
        start_date=datetime.utcnow() - timedelta(days=7),
        end_date=datetime.utcnow(),
        metadata={
            "participants": ["Alice", "Bob"],
            "format": "whatsapp"
        }
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


@pytest.fixture
def test_messages(db_session, test_conversation) -> list[Message]:
    """Create test messages."""
    messages = []
    participants = ["Alice", "Bob"]
    
    for i in range(10):
        message = Message(
            conversation_id=test_conversation.id,
            sender=participants[i % 2],
            content=f"Test message {i}",
            timestamp=datetime.utcnow() - timedelta(hours=10-i),
            message_type="text",
            metadata={}
        )
        messages.append(message)
        db_session.add(message)
    
    db_session.commit()
    return messages


@pytest.fixture
def sample_whatsapp_text() -> str:
    """Sample WhatsApp chat export text."""
    return """[1/1/24, 10:00 AM] Alice: Hey Bob! How are you?
[1/1/24, 10:01 AM] Bob: Hi Alice! I'm doing great, thanks for asking 😊
[1/1/24, 10:02 AM] Alice: That's wonderful to hear!
[1/1/24, 10:03 AM] Bob: How about you? How was your weekend?
[1/1/24, 10:05 AM] Alice: It was fantastic! Went hiking and the weather was perfect
[1/1/24, 10:06 AM] Bob: <Media omitted>
[1/1/24, 10:07 AM] Bob: Check out this photo from my hike!
[1/1/24, 10:08 AM] Alice: Wow, that view is amazing! 😍
[1/1/24, 10:10 AM] Bob: Thanks! We should go together next time
[1/1/24, 10:11 AM] Alice: Absolutely! Let's plan for next weekend"""


@pytest.fixture
def sample_whatsapp_json() -> Dict[str, Any]:
    """Sample WhatsApp chat export JSON."""
    return {
        "messages": [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "sender": "Alice",
                "content": "Hey Bob! How are you?",
                "type": "text"
            },
            {
                "timestamp": "2024-01-01T10:01:00Z",
                "sender": "Bob",
                "content": "Hi Alice! I'm doing great, thanks for asking 😊",
                "type": "text"
            },
            {
                "timestamp": "2024-01-01T10:02:00Z",
                "sender": "Alice",
                "content": "That's wonderful to hear!",
                "type": "text"
            },
            {
                "timestamp": "2024-01-01T10:06:00Z",
                "sender": "Bob",
                "content": "photo.jpg",
                "type": "media"
            }
        ],
        "metadata": {
            "chat_name": "Alice and Bob",
            "participants": ["Alice", "Bob"],
            "export_date": "2024-01-15T12:00:00Z"
        }
    }


def create_access_token(user_id: str) -> str:
    """Create a test access token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


# Import get_db after it's defined in the actual app
try:
    from app.core.database import get_db
except ImportError:
    # Define a placeholder if the actual function doesn't exist yet
    def get_db():
        pass