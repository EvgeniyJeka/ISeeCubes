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

        secret_key = secrets.token_hex(16)

        token_content = {"user_name": user_name, "user_token": LEONID_AUTH_TOKEN}
        encoded_jwt = jwt.encode(token_content, secret_key, algorithm="HS256")

        payload = {"user_data":   encoded_jwt,
                   "user_prompt": message_content}

        bot_prompt_url = LEONID_BASE_URL + '/receive_prompt'
        response = requests.post(url=bot_prompt_url,json=payload)

        return response.text

    def notify_all_bots_on_user_disconnection(self, user_name, bot_name="Leonid"):
        # TO DO
        secret_key = secrets.token_hex(16)

        # Each bot might have a different procedure for conversation termination
        # Right now we have only one local chat bot. If more chat bots are to be integrated with
        # the application more procedures will be added to this method.
        if bot_name == "Leonid":

            token_content = {"user_name": user_name, "user_token": LEONID_AUTH_TOKEN}
            encoded_jwt = jwt.encode(token_content, secret_key, algorithm="HS256")

            payload = {"user_data": encoded_jwt}

            bot_prompt_url = LEONID_BASE_URL + '/user_disconnection'
            logging.info(f"Chat Server: notifying Leonid the chatbot that user {user_name} "
                         f"has disconnected and left the chat")

            response = requests.post(url=bot_prompt_url, json=payload)
            logging.info(f"Chat Server: response received from Leonid: {response.text}")

            return response.text