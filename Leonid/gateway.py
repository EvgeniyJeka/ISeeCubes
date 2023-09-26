import logging
from flask import Flask, request
import jwt

try:
    from Leonid.midlayer import MiddleLayer

except ModuleNotFoundError:
    from midlayer import MiddleLayer

logging.basicConfig(level=logging.INFO)


class GatewayApp:

    def __init__(self):
        self.app = Flask(__name__)

        @self.app.route("/receive_prompt", methods=['POST'])
        def receive_user_prompt():
            """
            This method parses user name and token packed in a JWT, and providing those are valid
            the user's name (extracted from JWT) and user's prompt are forwarded to Vicuna language model
            (through MiddleLayer). Response provided by the model is returned (if there is no response - the relevant
            error message or notification is returned).
            # NOTE: At the moment user's token isn't validated, the auth. module will be added later.
            :return: str
            """
            request_content = request.get_json()

            try:
                # Verifying user input
                user_data = request_content['user_data']  # User name & token as JWT
                user_prompt = request_content['user_prompt']

            except KeyError:
                return {"error": "Invalid request, fields missing"}

            except Exception as e:
                logging.error(f"Gateway: invalid request received: {request_content} - {e}")
                return {"error": f"Invalid request"}

            # Getting user name and user token - the former is used to verify the current user is authorized
            user_name, user_token = self.extract_user_data(user_data)
            token_validation = self.user_token_validator(user_token)

            if token_validation is False:
                logging.warning(f"Gateway: authorization issue - user {user_name} tried to use"
                                f" an invalid access token {user_token}")
                return {"error": "Access denied"}

            logging.info(f"Gateway: Forwarding to the model {user_name} : {user_prompt}")

            # Forwarding user name and user prompt to the model
            return MiddleLayer.handle_user_prompt(user_name, user_prompt)

        @self.app.route("/user_disconnection", methods=['POST'])
        def handle_user_disconnection():
            """
            This method handles user disconnection notification.
            When a user that has a conversation with the chat bot terminates connection
            the chat bot should be notified via this API method. After user name and token are
            validated user's name is passed to the MiddleLayer, and the bot instance that had a conversation
            with that given user is stopped and removed.
            :return: dict with result report
            """
            request_content = request.get_json()

            try:
                user_data = request_content['user_data']  # User name & token as JWT

            except KeyError:
                return {"error": "Invalid request, fields missing"}

            except Exception as e:
                logging.error(f"Gateway: invalid request received: {request_content} - {e}")
                return {"error": f"Invalid request"}

            # Getting user name and user token - the former is used to verify the current user is authorized
            user_name, user_token = self.extract_user_data(user_data)
            token_validation = self.user_token_validator(user_token)

            if token_validation is False:
                logging.warning(f"Gateway: authorization issue - user {user_name} tried to use"
                                f" an invalid access token {user_token}")
                return {"error": "Access denied"}

            logging.info(f"Gateway: forwarding user disconnection notification - {user_name}")
            return MiddleLayer.user_disconnection_internal_handling(user_name)

        @self.app.route("/user_disconnection/<user_name>", methods=['GET'])
        def status_check(user_name):
            """
            This simple can method is be used by chat bot users to verify the service
            is up and running
            :param user_name: str
            :return: dict
            """
            logging.info(f"Gateway: User {user_name} has sent 'status check' request. \n"
                         f"Confirming Chat Bot is up and running")

            return {"result": "ok"}

        @self.app.route("/inject_context", methods=['POST'])
        def inject_conversation_context():
            """
            This method can be used to inject initial context that will be used by the model during the conversation
            with that given user.
            :return: str
            """
            request_content = request.get_json()

            try:
                # Verifying user input
                user_data = request_content['user_data']  # User name & token as JWT
                injected_context = request_content['injected_context']

            except KeyError:
                return {"error": "Invalid request, fields missing"}

            except Exception as e:
                logging.error(f"Gateway: invalid request received: {request_content} - {e}")
                return {"error": f"Invalid request"}

            # Getting user name and user token - the former is used to verify the current user is authorized
            user_name, user_token = self.extract_user_data(user_data)
            token_validation = self.user_token_validator(user_token)

            if token_validation is False:
                logging.warning(f"Gateway: authorization issue - user {user_name} tried to use"
                                f" an invalid access token {user_token}")
                return {"error": "Access denied"}

            logging.info(f"Gateway: Forwarding injected context to the model {user_name} : {injected_context}")

            # Forwarding user name and user prompt to the model
            return MiddleLayer.inject_custom_context(user_name, injected_context)



    def run(self, host='0.0.0.0', port=5001):
        self.app.run(host=host, port=port)

    def extract_user_data(self, jwt_token):
        """
        Extracts user data from a JWT (JSON Web Token).

        Parameters:
           jwt_token (str): The JWT token to decode and extract user data from.
        Returns:
           tuple: A tuple containing user-related data extracted from the JWT.
                  The tuple contains two elements: user name and user token.
       """

        # Decode the JWT without verifying the signature
        decoded_payload = jwt.decode(jwt_token, algorithms=["HS256"], options={"verify_signature": False})
        logging.info(f"Gateway: decoded user token {decoded_payload}")

        return decoded_payload['user_name'], decoded_payload['user_token']

    def user_token_validator(self, token_to_validate):
        # Authorization method - temporary stub
        return True


if __name__ == "__main__":
    gateway_app = GatewayApp()
    gateway_app.run()
