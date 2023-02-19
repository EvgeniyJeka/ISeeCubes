import configparser
import redis
import logging
import os

REDIS_PORT = 6379


class RedisIntegration:

    redis_client = None

    def __init__(self, config_file_path):
        try:
            self.read_config(config_file_path)
            self.redis_client = redis.Redis(host=self.hst, port=REDIS_PORT, db=self.db_number)

        except Exception as e:
            logging.critical(f"Redis integration: Error! Failed to connect to Redis DB container - {e}")
            raise e

    def read_config(self, config_file_path):
        """
            This method reads database configuration information from either the provided configuration file
            or environment variables.

            :param config_file_path: (str) Path to the configuration file.
            :raises: Exception if the database configuration information cannot be read.
        """

        try:
            if os.getenv("SQL_USER") is None:
                # Reading DB name, host and credentials from config
                config = configparser.ConfigParser()
                config.read(config_file_path)
                self.hst = config.get("REDIS", "host")
                self.redis_jwt_hashmap_name = config.get("REDIS", "auth_token_hashmap")
                self.db_number = int(config.get("REDIS", "db_number"))
            else:
                self.hst = os.getenv("REDIS_HOST")
                self.redis_jwt_hashmap_name = os.getenv("AUTH_TOKEN_HASHMAP")
                self.db_number = int(os.getenv("REDIS_DB_NUMBER"))

        except Exception as e:
            logging.critical(f"Redis integration: Error! Failed to read config from the "
                             f"'config.ini' file or fetch from environment variables! {e}")
            raise e

    def insert_token(self, username, inserted_token):

        try:
            logging.info(f"Inserting  the JWT to Redis, username: {username}, token: {inserted_token}")
            return self.redis_client.hset(self.redis_jwt_hashmap_name, username, inserted_token)

        except Exception as e:
            logging.error(f"Redis Integration: Error! Failed to insert user token {username} into Redis - {e}")
            raise e

    def fetch_token_by_username(self, username):
        try:
            logging.info(f"Fetching JWT from Redis by username: {username}")
            user_token = self.redis_client.hget(self.redis_jwt_hashmap_name, username)

            if user_token:
                return user_token.decode('utf-8')
            else:
                logging.warning(f"No JWT for user {username}")
                return None

        except Exception as e:
            logging.error(f"Redis integration: Failed to fetch token by {username} from Redis: {e}")
            raise e

    def validate_user_token(self, username, token):

        try:
            token_saved_in_redis = self.fetch_token_by_username(username)

            if token_saved_in_redis is None:
                return False

            return token_saved_in_redis == token

        except Exception as e:
            logging.error(f"Redis integration: Failed to validate JWT {token} related to "
                          f"user {username} against Redis: {e}")
            raise e

    def delete_token(self, username):
        try:
            logging.info(f"Deleting the token  related to {username}from Redis")
            self.redis_client.hdel(self.redis_jwt_hashmap_name, username)
            return True

        except Exception as e:
            logging.error(f"Redis integration: Failed to delete JWT {username} from Redis: {e}")
            raise e


#
# if __name__ == "__main__":
#     print("Test")


