import jwt
import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    try:
        payload = jwt.decode(
            token.credentials,
            key=os.environ["PUBLIC_CLERK_PUBLISHABLE_KEY"],
            algorithms=['RS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")