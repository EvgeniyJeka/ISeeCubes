import requests
import logging
import jwt
import secrets

LEONID_AUTH_TOKEN = "%Leonid_Test_Token%"
LEONID_BASE_URL = "http://localhost:5001"

# TO DO:
#
# 1. Add a method that would notify the bot on user disconnection (for each bot)


class LocalChatBotIntegration:

    def check_if_bot_available(self, bot_name: str):
        # Temporary stab. The method will send a request to verify that bot with given name/ID is available

        return True


    def route_incoming_message(self, bot_name, user_name, message_content):
        if bot_name == 'Leonid':
            return self.send_message_to_leonid(user_name, message_content)


    def send_message_to_leonid(self, user_name, message_content):
        # content = "Hello there! I'm leonid."

        secret_key = secrets.token_hex(16)

        token_content = {"user_name": user_name, "user_token": LEONID_AUTH_TOKEN}
        encoded_jwt = jwt.encode(token_content, secret_key, algorithm="HS256")

        payload = {"user_data":   encoded_jwt,
                   "user_prompt": message_content}

        bot_prompt_url = LEONID_BASE_URL + '/receive_prompt'
        response = requests.post(url=bot_prompt_url,json=payload)

        return response.text

    def notify_leonid_on_user_disconnection(self, user_name):
        # TO DO
        pass