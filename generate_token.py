import jwt
from datetime import datetime, timedelta

# Create a test token
secret_key = "test-secret-key-change-in-production"
payload = {
    "sub": "1",  # user_id
    "exp": datetime.utcnow() + timedelta(hours=24)
}

token = jwt.encode(payload, secret_key, algorithm="HS256")
print(f"Generated token: {token}")
print(f"Add this to localStorage: localStorage.setItem('authToken', '{token}')")
