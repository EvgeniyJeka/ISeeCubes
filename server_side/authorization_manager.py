import jwt
import random
import logging

logging.basicConfig(level=logging.INFO)

class AuthManager:

    # Copy this to Redis, fetch on app start
    active_tokens = dict()

    # Move this to SQL DB
    credentials = {"Lisa": hash("TestMe"),
                   "Avi": hash("MoreMoreMore"),
                   "Era": hash("Come on"),
                   "Tsahi": hash("Virtual Environment")}


    def key_gen(self):
        return "key" + str(random.randint(1000, 10000))

    def generate_jwt_token(self, username, password):
        """
        This method generates a JWT basing on passed credentials, providing the credentials are valid
        :param username: str
        :param password: str
        :return: dict
        """
        if self.validate_credentials_for_jwt_creation(username, password):
            key = self.key_gen()
            encoded_jwt = jwt.encode({"user": username, "password": password}, key, algorithm="HS256")
            self.active_tokens[username] = encoded_jwt
            return {"result": "success", "key": encoded_jwt}

        else:
            return {"error": "Invalid credentials!"}


    def validate_jwt_token(self, username, token):
        if username not in self.active_tokens.keys():
            return False

        return self.active_tokens[username] == token


    def validate_credentials_for_jwt_creation(self, username, password):
        if username not in self.credentials.keys():
            return False

        return self.credentials[username] == hash(password)

