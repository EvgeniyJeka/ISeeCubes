import requests
import logging
import jwt
import secrets
import os
import configparser

LEONID_AUTH_TOKEN = "%Leonid_Test_Token%"
LEONID_BASE_URL = "http://localhost:5001"


class LocalChatBotIntegration:

    def check_if_bot_available(self, config_file_path, bot_name: str):
        """
        This method fetches configuration from environmental variables in order to check if given
        chat bot is available.
        :param bot_name: str
        :return: bool
        """
        try:
            if bot_name == 'Leonid':
                # Running on local machine - fetching config from the config file
                if os.getenv("SQL_USER") is None:
                    # Reading DB name, host and credentials from config
                    config = configparser.ConfigParser()
                    config.read(config_file_path)
                    bot_status = config.get("CHAT_SERVER_CONFIG", "enable_leonid_chat_bot")

                    if bot_status == 'Enabled':
                        return True

                # Running in a Docker container - fetching config from env. variable
                flag = os.getenv("LEONID_THE_CHAT_BOT")
                if flag == 'Enabled':
                    return True
                else:
                    return False

        except Exception:
            return False

    def route_incoming_message(self, bot_name, user_name, message_content):
        """
        This method redirects user's message and name to the selected local chat bot
        and returns the response that comes from the bot back to the calling method.
        :param bot_name: str (must be on the chat bots list)
        :param user_name: str
        :param message_content: str
        :return: str
        """
        if bot_name == 'Leonid':
            return self.send_message_to_leonid(user_name, message_content)

        else:
            return {"Error": f"No chat bot with ID {bot_name}"}

    def send_message_to_leonid(self, user_name, message_content):
        """
        This method redirects user's message and name to Leonid the chat bot
        and returns the response that comes from the bot back to the calling method
        :param user_name: str
        :param message_content: str
        :return: str
        """

        secret_key = secrets.token_hex(16)

        token_content = {"user_name": user_name, "user_token": LEONID_AUTH_TOKEN}
        encoded_jwt = jwt.encode(token_content, secret_key, algorithm="HS256")

        payload = {"user_data":   encoded_jwt,
                   "user_prompt": message_content}

        bot_prompt_url = LEONID_BASE_URL + '/receive_prompt'
        response = requests.post(url=bot_prompt_url,json=payload)

        return response.text

    def notify_all_bots_on_user_disconnection(self, user_name, bot_name="Leonid"):
        """
        This method notifies the selected chat bot on user disconnection.
        Each bot may have a different procedure for this, so the method contains a separate
        section for each chat bot.
        :param user_name: str
        :param bot_name: str  (must be on the chat bots list)
        :return: str
        """
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

        else:
            return {"error": f"The bot {bot_name} is not on the list."}