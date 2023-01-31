import jwt
import random
import logging
import secrets

logging.basicConfig(level=logging.INFO)


class AuthManager:
    # Copy this to Redis, fetch on app start
    active_tokens = dict()

    # Move this to SQL DB
    credentials = {"Lisa": hash("TestMe"),
                   "Avi": hash("MoreMoreMore"),
                   "Era": hash("Come on"),
                   "Tsahi": hash("Virtual Environment")}

    def generate_jwt_token(self, username, password):
        """
           This method generates a JWT basing on passed credentials, providing the credentials are valid
           :param username: str
           :param password: str
           :return: dict

       """

        try:
            if self.validate_credentials_for_jwt_creation(username, password):
                secret_key = secrets.token_hex(16)
                print(secret_key)
                payload = {"user": username}

                encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")
                self.active_tokens[username] = encoded_jwt
                return {"result": "success", "token": encoded_jwt}
            else:
                return {"result": "Invalid credentials"}

        except Exception as e:
            return {"error": f"Authorization module: failed to generate a JWT - {e}"}

    def validate_jwt_token(self, username, token):
        if username not in self.active_tokens.keys():
            return False

        return self.active_tokens[username] == token

    def validate_credentials_for_jwt_creation(self, username, password):
        if username not in self.credentials.keys():
            return False

        return self.credentials[username] == hash(password)
