import jwt
import logging
import secrets

try:
    from server_side.postgres_integration import PostgresIntegration

except ModuleNotFoundError:
    from postgres_integration import PostgresIntegration

logging.basicConfig(level=logging.INFO)


class AuthManager:

    def __init__(self):
        self.postgres_integration = PostgresIntegration()

    # Copy this to Redis, fetch on app start
    active_tokens = dict()

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
        usersnames_list = self.postgres_integration.get_all_available_users_list()
        if username not in usersnames_list:
            return False

        return self.postgres_integration.get_users_hashed_password(username) == hash(password)
