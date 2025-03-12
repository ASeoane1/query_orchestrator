import jwt
from typing import Dict, List, Any

class JWTManager:
    def __init__(self, secret: str, algorithm: str = 'HS256'):
        """
        Initialize the JWT manager.

        :param secret: Secret key used to sign the token.
        :param algorithm: Encryption algorithm (default 'HS256').
        """
        self.secret = secret
        self.algorithm = algorithm

    def create_token(self, data: Dict[str, List[str]], user: str, is_admin: bool) -> str:
        """
        Creates a JWT token without an expiration date.

        :param data: Dictionary (hashmap) with string keys and list values.
        :param user: Username.
        :param is_admin: Boolean indicating if the admin role should be added.
        :return: JWT token as a string.
        """
        payload = data.copy()
        payload['user'] = user
        if is_admin:
            payload['role'] = 'admin'
        token = "Bearer {}".format(jwt.encode(payload, self.secret, algorithm=self.algorithm))
        return token

    def read_token(self, token: str) -> dict:
        """
        Decodes the given JWT token.

        :param token: JWT token as a string.
        :return: Payload contained in the token.
        """
        # Decoding the token will verify its signature
        payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        return payload