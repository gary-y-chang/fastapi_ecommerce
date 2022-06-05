from decouple import config
from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

class Auth:
    JWT_SECRET = config("SECRET")
    JWT_ALGORITHM = config("ALGORITHM")
    hasher= CryptContext(schemes=['bcrypt'])

    def encode_password(self, password):
        return self.hasher.hash(password)

    def verify_password(self, password, encoded_password):
        return self.hasher.verify(password, encoded_password)

    def encode_token(self, user_id, email):
        payload = {
            'exp' : datetime.utcnow() + timedelta(days=0, hours=12),
            'iat' : datetime.utcnow(),
	        'scope': 'access_token',
            'id': str(user_id),
            'sub' : email
        }
        return jwt.encode(
            payload, 
            self.JWT_SECRET,
            algorithm=self.JWT_ALGORITHM
        )

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=[self.JWT_ALGORITHM])
            if payload['scope'] in ['access_token', 'refresh_token']:
                return payload   
            raise HTTPException(status_code=401, detail='Scope for the token is invalid')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid token')

    def encode_refresh_token(self, user_id, email):
        payload = {
            'exp' : datetime.utcnow() + timedelta(days=0, hours=12),
            'iat' : datetime.utcnow(),
	        'scope': 'refresh_token',
            'id': str(user_id),
            'sub' : email
        }
        return jwt.encode(
            payload, 
            self.JWT_SECRET,
            algorithm=self.JWT_ALGORITHM
        )

    def refresh_token(self, refresh_token):
        try:
            payload = jwt.decode(refresh_token, self.JWT_SECRET, algorithms=[self.JWT_ALGORITHM])
            if (payload['scope'] == 'refresh_token'):
                email = payload['sub']
                user_id = payload['id']
                new_token = self.encode_token(user_id, email)
                return new_token
            raise HTTPException(status_code=401, detail='Invalid scope for token')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Refresh token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid refresh token')


class Guard(HTTPBearer):
    async def __call__(self, req: Request):
        client_host = req.client.host
        print('-----> in to dependency', client_host)
        credentials: HTTPAuthorizationCredentials = await super().__call__(req)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            
            payload = self.verify_jwt(credentials.credentials)
            try:
                if payload['scope']=='access_token':
                    return payload['id'] 
                elif payload['scope']=='refresh_token':
                    return Auth().refresh_token(credentials.credentials)
            except TypeError: # payload is None when expired
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str):
        print('---> token: ', jwtoken)
        try:
            payload = Auth().decode_token(jwtoken)
            print(payload)
        except:
            payload = None
        
        return payload
       


