import configparser
import json

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
                self.redis_pending_conversations_hashmap_name = config.get("REDIS", "pending_conversations_hashmap")
                self.db_number = int(config.get("REDIS", "db_number"))
            else:
                self.hst = os.getenv("REDIS_HOST")
                self.redis_jwt_hashmap_name = os.getenv("AUTH_TOKEN_HASHMAP")
                self.redis_pending_conversations_hashmap_name = os.getenv("PENDING_CONVERSATIONS_HASHMAP")
                self.db_number = int(os.getenv("REDIS_DB_NUMBER"))

        except FileNotFoundError as e:
            raise ValueError(f"Redis Integration: Error! Config file not found at {config_file_path}") from e

        except KeyError as e:
            raise ValueError(f"Redis Integration: Error! Missing configuration item: {e}") from e

        except ValueError as e:
            raise ValueError(f"Redis Integration: Error! Invalid configuration value: {e}") from e

        except Exception as e:
            raise ValueError(f"Redis Integration: Error! Failed to read configuration: {e}") from e

    def insert_token(self, username, inserted_token):
        """
        Inserting an auth. JWT that was generated for a user into Redis Hash Map - user name is the key,
        and the JWT is the value
        :param username: str
        :param inserted_token: str
        :return: True on success
        """

        if not username or not inserted_token:
            return False

        try:
            logging.info(f"Inserting  the JWT to Redis, username: {username}, token: {inserted_token}")

            redis_reply = self.redis_client.hset(self.redis_jwt_hashmap_name, username, inserted_token)
            if redis_reply >= 0:
                return True

            return False

        except redis.exceptions.RedisError as e:
            logging.error(f"Redis Integration: Redis Error! - {e}")
            raise e

        except Exception as e:
            logging.error(f"Redis Integration: Error! Failed to insert user token {username} into Redis - {e}")
            raise e

    def fetch_token_by_username(self, username):
        """
        Fetching auth. JWT from Redis by username.
        :param username: str
        :return: requested JWT on success, str
        """
        try:
            logging.info(f"Fetching JWT from Redis by username: {username}")
            user_token = self.redis_client.hget(self.redis_jwt_hashmap_name, username)

            if user_token:
                return user_token.decode('utf-8')
            else:
                logging.warning(f"No JWT for user {username}")
                return None

        except redis.exceptions.RedisError as e:
            logging.error(f"Redis Integration: Redis Error! - {e}")
            raise e

        except Exception as e:
            logging.error(f"Redis integration: Failed to fetch token by {username} from Redis: {e}")
            raise e

    def validate_user_token(self, username, token):
        """
        This method validates the provided auth JWT against JWT that is stored in Redis.
        Auth. JWT is fetched from Redis by username and compared with the provided JWT.
        The method returns True if those are identical
        :param username: str
        :param token: str
        :return: bool
        """

        try:
            token_saved_in_redis = self.fetch_token_by_username(username)

            if token_saved_in_redis is None:
                return False

            return token_saved_in_redis == token

        except redis.exceptions.RedisError as e:
            logging.error(f"Redis Integration: Redis Error! - {e}")
            raise e

        except Exception as e:
            logging.error(f"Redis integration: Failed to validate JWT {token} related to "
                          f"user {username} against Redis: {e}")
            raise e

    def delete_token(self, username):
        """
           Delete the JWT for the given username from Redis.

           :param username: (str) The username of the JWT to delete.
           :return: (bool) True if the JWT was deleted, False if the JWT was not found in Redis.
           :raises: Exception if an error occurs while deleting the JWT.
        """
        try:

            # Check if token exists in Redis
            if not self.redis_client.hexists(self.redis_jwt_hashmap_name, username):
                logging.warning(f"No JWT for user {username}")
                return False

            logging.info(f"Deleting the token  related to {username}from Redis")
            self.redis_client.hdel(self.redis_jwt_hashmap_name, username)
            return True

        except redis.exceptions.RedisError as e:
            logging.error(f"Redis Integration: Redis Error! - {e}")
            raise e

        except Exception as e:
            logging.error(f"Redis integration: Failed to delete JWT {username} from Redis: {e}")
            raise e

    def store_first_conversation(self, username, conversation):

        stored_conversations = json.dumps([conversation])

        try:
            logging.info(f"Storing first conversation for {username}, content: {conversation}")
            return self.redis_client.hset(self.redis_pending_conversations_hashmap_name, username, stored_conversations)

        except Exception as e:
            logging.error(f"Redis Integration: Error! Failed to insert a "
                          f"conversation line for {username} into Redis - {e}")
            raise e

    def extend_stored_conversations_list(self, username, conversation):

        existing_conversations = self.fetch_pending_conversations_for_user(username)

        if existing_conversations:
            existing_conversations.append(conversation)
            self.delete_stored_conversation(username)

            stored_conversation_item = json.dumps(existing_conversations)
            return self.redis_client.hset(self.redis_pending_conversations_hashmap_name, username, stored_conversation_item)

        else:
            return self.store_first_conversation(username, conversation)

    def fetch_pending_conversations_for_user(self, username):

        try:
            logging.info(f"Fetching pending conversations from Redis by username: {username}")
            saved_conversations = self.redis_client.hget(self.redis_pending_conversations_hashmap_name, username)

            if saved_conversations:
                pending_conversations = saved_conversations.decode('utf-8')
                return json.loads(pending_conversations)

            else:
                logging.warning(f"No pending conversations for user {username}")
                return None

        except Exception as e:
            logging.error(f"Redis integration: Failed to fetch pending conversations for {username} from Redis: {e}")
            raise e

    def get_users_list_with_pending_conversatons(self):

        users_list = self.redis_client.hkeys(self.redis_pending_conversations_hashmap_name)
        if len(users_list) == 0:
            return []

        return [username.decode('utf-8') for username in users_list]

    def delete_stored_conversation(self, username):
        try:
            logging.info(f"Deleting stored conversations related related to {username} from Redis")
            self.redis_client.hdel(self.redis_pending_conversations_hashmap_name, username)
            return True

        except Exception as e:
            logging.error(f"Redis integration: Failed to delete JWT {username} from Redis: {e}")
            raise e


#
# if __name__ == "__main__":
#     config_file_path = "./config.ini"



