import redis
import logging

REDIS_PORT = 6379
REDIS_HOST = 'localhost'
REDIS_TOKENS_HASH_MAP_NAME = 'auth_tokens'

class RedisIntegration:

    # Copy this to Redis, fetch on app start
    active_tokens = dict()

    redis_client = None

    def __init__(self, config_file_path):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    def insert_token(self, username, inserted_token):

        try:
            logging.info(f"Inserting  the JWT to Redis, username: {username}, token: {inserted_token}")
            return self.redis_client.hset(REDIS_TOKENS_HASH_MAP_NAME, username, inserted_token)

        except Exception as e:
            logging.error(f"Redis Integration: Error! Failed to insert user token {username} into Redis - {e}")
            raise e

    def fetch_token_by_username(self, username):
        try:
            logging.info(f"Fetching JWT from Redis by username: {username}")
            user_token = self.redis_client.hget(REDIS_TOKENS_HASH_MAP_NAME, username)

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
            self.redis_client.hdel(REDIS_TOKENS_HASH_MAP_NAME, username)
            return True

        except Exception as e:
            logging.error(f"Redis integration: Failed to delete JWT {username} from Redis: {e}")
            raise e



if __name__ == "__main__":
    print("Test")
    config_file_path = "./config.ini"
    me_redis = RedisIntegration(config_file_path)
    me_redis.delete_token("Mioau")
    #me_redis.insert_token("Mioau", "Miau_token")
    print(me_redis.fetch_token_by_username("Mioau"))




    # # Connect to Redis
    # r = redis.Redis(host='localhost', port=6379, db=0)
    #
    # # Create a hash and add a record to it
    # r.hset('myhash', 'key1', 'value1')
    # r.hset('myhash', 'key2', 'test_me_value')
    #
    # # Retrieve the record from the hash
    # value = r.hget('myhash', 'key2')
    # print(value.decode('utf-8'))

