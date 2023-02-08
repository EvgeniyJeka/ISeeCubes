

class RedisIntegration:

    # Copy this to Redis, fetch on app start
    active_tokens = dict()

    def fetch_active_tokens(self):
        print("Fetching here all active tokens from Redis - Stab")
        return self.active_tokens

    def insert_token(self, username, inserted_token):
        print("Inserting here the JWT to Redis - Stab")
        self.active_tokens[username] = inserted_token
        return True

    def validate_user_token(self, username, token):
        print("Validating here the provided token against Redis - Stab")
        return self.active_tokens[username] == token

    def delete_token(self, username):
        print("Deleting here the token from Redis - Stab")
        self.active_tokens.pop(username)

