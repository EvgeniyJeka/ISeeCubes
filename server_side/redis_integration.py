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

        except Exception as e:
            logging.critical(f"Redis integration: Error! Failed to read config from the "
                             f"'config.ini' file or fetch from environment variables! {e}")
            raise e

    def insert_token(self, username, inserted_token):

        try:
            logging.info(f"Inserting  the JWT to Redis, username: {username}, token: {inserted_token}")

            redis_reply = self.redis_client.hset(self.redis_jwt_hashmap_name, username, inserted_token)
            if isinstance(redis_reply, int) and redis_reply >= 0:
                return True

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



if __name__ == "__main__":
    config_file_path = "./config.ini"
    print("Test")
    new_cached_message = {"sender": 'message_sender1', "content": 'content1', "conversation_room": 'conversation_room1'}
    new_cached_message2 = {"sender": 'message_sender2', "content": 'content2', "conversation_room": 'conversation_room2'}
    new_cached_message3 = {"sender": 'message_sender3', "content": 'content3', "conversation_room": 'conversation_room3'}
    new_cached_message4 = {"sender": 'message_sender4', "content": 'content4',"conversation_room": 'conversation_room4'}
    red = RedisIntegration(config_file_path)
    red.delete_stored_conversation("El")

    red.store_first_conversation("El", new_cached_message)
    red.extend_stored_conversations_list("El", new_cached_message2)
    red.extend_stored_conversations_list("El", new_cached_message3)
    red.extend_stored_conversations_list("El", new_cached_message4)
    print(red.fetch_pending_conversations_for_user("El"))

    # red.extend_stored_conversations_list("El", "Good bye")
    # red.store_first_conversation("Boris", "Ga Ga Ga")
    # print(red.delete_stored_conversation("El"))
    # print(red.fetch_pending_conversations_for_user("Boris"))



