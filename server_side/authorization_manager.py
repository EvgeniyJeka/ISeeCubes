import jwt
import logging
import secrets
import redis


try:
    from server_side.postgres_integration import PostgresIntegration
    from server_side.redis_integration import RedisIntegration

except ModuleNotFoundError:
    from postgres_integration import PostgresIntegration
    from redis_integration import RedisIntegration

logging.basicConfig(level=logging.INFO)


class AuthManager:

    def __init__(self, postgres_integration, redis_integration):
        self.postgres_integration = postgres_integration
        self.redis_integration = redis_integration

    def generate_jwt_token(self, username, password):
        """
           This method generates a JWT token based on passed credentials.
           The provided credentials are first validated. If the credentials are valid,
           a secret key is generated and used to encode a payload containing the username.
           The encoded JWT token is then stored in the `active_tokens` dictionary and returned.
           If the credentials are invalid, a dictionary with a result key of "Invalid credentials" is returned.
           If an exception occurs during the process, a dictionary with an error key is returned.

           :param username: str, the username to be included in the JWT payload
           :param password: str, the password to be used to validate the credentials
           :return: dict, with the following keys:
               - `result`: str, either "success" or "Invalid credentials"
               - `token`: str, the encoded JWT token if the `result` is "success"
               - `error`: str, the error message if an exception occurs during the process
        """

        try:
            if self.validate_credentials_for_jwt_creation(username, password):
                secret_key = secrets.token_hex(16)
                print(secret_key)
                payload = {"user": username}

                encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")

                if self.redis_integration.insert_token(username, encoded_jwt):
                    return {"result": "success", "token": encoded_jwt}
                else:
                    logging.error("Error! Failed to insert newly created token to Redis")
                    return {"error": "Failed to insert newly created token to Redis"}

            else:
                return {"result": "Invalid credentials"}

        except redis.exceptions.RedisError as e:
            logging.critical(f"Chat Server: Redis DB is unavailable shutting down the server - {e}")
            raise e

        except Exception as e:
            return {"error": f"Authorization module: failed to generate a JWT - {e}"}

    def validate_jwt_token(self, username, token):
        """
        Validate a given JSON Web Token (JWT) for the specified username.

        This function is used to check if a given JWT is still valid for a particular user.

        :param username: The username for which to validate the JWT.
        :type username: str
        :param token: The JSON Web Token to validate.
        :type token: str
        :return: Whether the JWT is valid or not.
        :rtype: bool
        """
        try:
            return self.redis_integration.validate_user_token(username, token)

        except redis.exceptions.RedisError as e:
            logging.critical(f"Chat Server: Redis DB is unavailable shutting down the server - {e}")
            raise e

    def validate_credentials_for_jwt_creation(self, username, password):
        """
        Validate the given credentials for JSON Web Token (JWT) creation.

        :param username: the username of the user to validate
        :type username: str
        :param password: the password of the user to validate
        :type password: str
        :return: True if the credentials are valid, False otherwise
        :rtype: bool
        """

        usersnames_list = self.postgres_integration.get_all_available_users_list()
        if username not in usersnames_list:
            return False

        return self.postgres_integration.get_users_hashed_password(username) == self.postgres_integration.hash_string(password)
