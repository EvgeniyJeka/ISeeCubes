import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request
from flask_socketio import SocketIO, join_room
import logging
import os
import configparser
import redis
import signal



try:
    # Add 2 variations of import (for Dockerization)
    from server_side.authorization_manager import AuthManager
    from server_side.chatgpt_integration import ChatGPTIntegration
    from server_side.postgres_integration import PostgresIntegration
    from server_side.redis_integration import RedisIntegration
    from server_side.local_chatbot_integration import LocalChatBotIntegration

except ModuleNotFoundError:
    # Add 2 variations of import (for Dockerization)
    from authorization_manager import AuthManager
    from chatgpt_integration import ChatGPTIntegration
    from postgres_integration import PostgresIntegration
    from redis_integration import RedisIntegration
    from local_chatbot_integration import LocalChatBotIntegration


logging.basicConfig(level=logging.INFO)

config_file_path = "./config.ini"

CACHED_OFFLINE_MESSAGES_DELAY = 3
KEEP_ALIVE_LOGGING = os.getenv("KEEP_ALIVE_LOGGING")


# Special users
CHAT_GPT_USER = "ChatGPT"
ADMIN_USER = "Admin"
LEONID_THE_CHATBOT = "Leonid"

LOCAL_CHAT_BOTS_LIST = ["Leonid"]


class ChatServer:
    # Will be taken from SQL DB
    users_list = None

    # Mapping active users against the last time the 'connection_alive' event was received from each
    keep_alive_tracking = {}

    users_currently_online = set()

    auth_manager = None
    chatgpt_instance = None
    chatbot_router = None

    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)

        self.chatgpt_instance = ChatGPTIntegration()
        self.chatbot_router = LocalChatBotIntegration()

        global emergency_flag
        emergency_flag = False

        # Verifying the ChatGPT service is available
        if self.chatgpt_instance.is_chatgpt_available():
            self.users_currently_online.add(CHAT_GPT_USER)

        # Verifying Leonid the ChatBot is available, if he is - adding him to the online users list
        if self.chatbot_router.check_if_bot_available(config_file_path, LEONID_THE_CHATBOT):
            logging.info(f"Chat Server: adding {LEONID_THE_CHATBOT} to the 'Online Users' list")
            self.users_currently_online.add(LEONID_THE_CHATBOT)

        try:
            self.postgres_integration = PostgresIntegration(config_file_path)
            self.redis_integration = RedisIntegration(config_file_path)

            self.users_list = self.postgres_integration.get_all_available_users_list()
            self.auth_manager = AuthManager(self.postgres_integration, self.redis_integration)

        # The Chat Service won't start unless Redis DB is available.
        except redis.exceptions.ConnectionError as e:
            logging.critical(f"Redis server isn't available - Chat Server goes down. "
                             f"Please make sure Redis DB is up'{e}")

            # Redis unavailable - activating the emergency flag.
            emergency_flag = True

    def room_names_generator(self, listed_users: list) -> list:
        """
           Generate a list of strings representing the possible combinations of two users' names that will be used
           to name the rooms.

           Args:
               listed_users (list): A list of user names to generate the combinations from.

           Returns:
               list: A list of strings in the format "<user1>&<user2>" representing the possible combinations
                     of two users' names.

           Example:
               Input :room_names_generator(["Alice", "Bob", "Charlie"])
               Output: ["Alice&Bob", "Alice&Charlie", "Bob&Charlie"]
        """
        listed_users.sort()

        res = []

        for i in range(0, len(listed_users)):
            current_user = listed_users[i]

            for user in listed_users[i + 1:]:
                res.append(f"{current_user}&{user}")

        return res

    def prepare_rooms_for(self, current_username: str):
        """
          Get all the rooms for a specific user.

          Parameters:
              current_username (str): The username of the user for whom rooms are being prepared.

          Returns:
              dict: A dictionary where the keys are usernames and the values are room names.
        """
        result = {}

        all_available_rooms = self.room_names_generator(self.users_list)

        for room_name in all_available_rooms:
            if current_username in room_name:
                names = room_name.split('&')

                if names[0] == current_username:
                    result[names[1]] = room_name
                elif names[1] == current_username:
                    result[names[0]] = room_name

        return result

    def handle_messaging_offline_user(self, message_sender, message_destination, content, conversation_room):
        """
           Handles messaging for offline users. Caches messages intended for offline users and publishes them once
           the user comes back online.

           Parameters:
           message_sender (str): The username of the sender of the message.
           message_destination (str): The username of the intended recipient of the message.
           content (str): The content of the message.
           conversation_room (str): The conversation room the message belongs to.

           """

        if not message_destination:
            logging.error("Message recipient not specified")
            return

        new_cached_message = {"sender": message_sender, "content": content, "conversation_room": conversation_room}
        logging.info(f"Caching a message from {message_sender} to {message_destination}: {content}")

        users_list = self.redis_integration.get_users_list_with_pending_conversatons()

        if message_destination in users_list:
            self.redis_integration.extend_stored_conversations_list(message_destination, new_cached_message)

        else:
            self.redis_integration.store_first_conversation(message_destination, new_cached_message)

    def publish_cached_messages(self, user_name):
        """
        This method retrieves cached messages that were sent to an offline user and publishes them to the user once
        they come online.

        Parameters:
            user_name (str): The name of the user for whom cached messages are being published.

        Returns:
            bool: True if the cached messages were successfully published, False otherwise.
        """

        try:
            users_list = self.redis_integration.get_users_list_with_pending_conversatons()

            if user_name in users_list:
                awaiting_messages = self.redis_integration.fetch_pending_conversations_for_user(user_name)

                for next_message_to_publish in awaiting_messages:
                    logging.info(f"Publishing a message cached for {user_name} - {next_message_to_publish['content']}")
                    message = {"sender": next_message_to_publish['sender'],
                               "content": next_message_to_publish['content']}

                    self.socketio.emit('received_message', message, to=next_message_to_publish["conversation_room"])
                    time.sleep(1)

                self.redis_integration.delete_stored_conversation(user_name)
                return True

        except Exception as e:
            logging.error(f"Failed to publish cached messages to user {user_name} - {e}")
            return False

    def stop_chat_server_because_redis_down(self, e):
        """
        This method is used for emergency situation handling - it is applied when Redis DB
        is unreachable. When the Chat Server runs in Docker container it terminates the Chat Server process.
        When the Chat Server runs locally, it stops the Flask - SocketIO sever.
        In both cases web socket session is terminated.
        :param e: Exception raised by RedisIntegration instance.
        """
        logging.critical(f" Alert! Redis DB is down - {e}")
        logging.critical(f"Chat server is going down to prevent further data loss")
        logging.critical(f"Please make sure Redis DB is up and running. "
                         f"After that please RESTART the Chat Server instance.")

        # If running in a Docker container - killing the Chat Serer process by process ID
        if os.getenv("KEEP_ALIVE_DELAY_BETWEEN_EVENTS"):
            os.kill(1, signal.SIGTERM)

        self.socketio.stop()


    def run(self):
        """
        This method handles incoming HTTP requests and websocket messages

        """

        @self.app.route("/get_contacts_list/<username>", methods=['GET'])
        def get_rooms_list(username):
            """
            Returns a JSON object containing the list of rooms for the specified user along with the list of all
            users who are currently online and the list of all registered users.

            Args:
                username (str): The name of the user whose contacts list is being requested.

            Returns:
                dict: A JSON object containing the following fields:
                    - 'contacts': A list of room names that the specified user is a member of.
                    - 'currently_online': A list of names of users who are currently online.
                    - 'all_existing_contacts': A list of all registered user names.
            """

            user_name = request.headers.get('username')
            jwt_token = request.headers.get('jwt')

            if not all([user_name, jwt_token]):
                return {"error": "The 'get_contact_list' request headers must contain username and jwt fields"}

            logging.info(f"Received a request for contacts, username: '{user_name}',  JWT: {jwt_token}")

            try:
                # Validating JWT before allowing the user to get the contacts list
                if not self.auth_manager.validate_jwt_token(user_name, jwt_token):
                    logging.error(f"Invalid JWT: {jwt_token}")
                    return {"error": "Invalid JWT"}

            except redis.exceptions.ConnectionError as e:
                self.stop_chat_server_because_redis_down(e)

            contacts_data = {"contacts": self.prepare_rooms_for(username),
                             "currently_online": list(self.users_currently_online),
                             "all_existing_contacts": self.users_list}

            return contacts_data

        @self.app.route("/log_in", methods=['POST'])
        def login_request():
            """
            Handle a login request sent to the "/log_in" endpoint.
            The request should include the username and password in the request body as a JSON object.
            Returns a JSON object containing a JWT token generated by the authentication manager.

            Raises:
                KeyError: If the request content is invalid or does not include the required fields.

            :return: dict
            """

            request_content = request.get_json()

            try:
                username = request_content['username']
                password = request_content['password']

            except KeyError:
                return {"error": "Invalid Log In request"}

            try:
                logging.info(f"New log in request received, username: {username}, password: {password}")
                requested_token = self.auth_manager.generate_jwt_token(username, password)

            except redis.exceptions.ConnectionError as e:
                self.stop_chat_server_because_redis_down(e)
                return {"result": "error", "token": "unavailable"}

            return requested_token

        @self.app.route("/admin/kill_token", methods=['POST'])
        def admin_kill_token():
            """
            Extracts JSON data from the request which should contain a 'username', 'password' and 'user_token_terminate'
            field.
            Uses the 'username' and 'password' fields to generate a JWT token using the 'generate_jwt_token'
            method of an 'auth_manager' object.
I           If the token generation is successful, the code removes the JWT token of the specified user
            ('user_token_terminate') from the 'active_tokens' dictionary of the 'auth_manager' object.
            :return: dict
            """

            request_content = request.get_json()

            if not request_content:
                return {"error": "Invalid request format, expected JSON data"}

            try:
                username = request_content['username']
                password = request_content['password']
                kill_user_token = request_content['user_token_terminate']

            except KeyError as e:
                return {"error": f"Invalid request, missing required field: {e}"}

            logging.info(f"Admin user request received, username: {username}, password: {password}")
            requested_token = self.auth_manager.generate_jwt_token(username, password)

            if requested_token['result'] == 'success':
                logging.info(f"Terminating JWT that belongs to {kill_user_token} by admin's request")

                try:
                    self.auth_manager.redis_integration.delete_token(kill_user_token)
                    self.keep_alive_tracking.pop(kill_user_token)
                    self.socketio.emit('user_has_gone_offline', {"username": kill_user_token})

                except KeyError:
                    return {"error": f"No JWT for user {kill_user_token}"}

                logging.info(f"Successfully terminated JWT for user: {kill_user_token}")
                return {"result": "success"}

            else:
                return {"error": "Admin access denied"}

        @self.app.route("/admin/get_info", methods=['POST'])
        def admin_get_info():
            """
            Extracts JSON data from the request which should contain a 'username' and 'password'
            fields.
            Uses the 'username' and 'password' fields to generate a JWT token using the 'generate_jwt_token'
            method of an 'auth_manager' object.
            If the token generation is successful, the method returns a list of all users that are currently online.

            """

            request_content = request.get_json()

            if not request_content:
                return {"error": "Invalid request format, expected JSON data"}

            try:
                username = request_content['username']
                password = request_content['password']

            except KeyError as e:
                return {"error": f"Invalid request, missing required field: {e}"}

            try:
                logging.info(f"Admin user request received, username: {username}, password: {password}")
                requested_token = self.auth_manager.generate_jwt_token(username, password)

            except redis.exceptions.ConnectionError as e:
                self.stop_chat_server_because_redis_down(e)
                return

            if requested_token['result'] == 'success':
                return {"online_clients_list": list(self.users_currently_online)}

        @self.socketio.on('join')
        def on_join(data):
            """
            Handling user 'join' request, a websocket message. The event is expected to contain the client name,
            auth. JWT and the Room to which the client wishes to join. The client is expected to send a 'join'
            request for each existing Room, but on the first 'join' request he is already added to the 'online
            users' list after the JWT is verified.

            This function handles the 'join' event by validating the client's JWT, adding the client to the specified
            Room, and performing some additional steps when the client first joins a Room. If the JWT is invalid, the
            function will return an error message.

            When a client first joins a Room, this function adds them to the 'online users' list and emits a
            'new_user_online' event to all connected clients, which includes the name of the new user. The function
            also checks for any cached messages that were sent to the client while they were offline, and publishes
            them to the Room so that the client can see them as incoming messages.

            Inputs:
            - data: A dictionary containing the client name, auth. JWT, and Room to join.

            Returns:
            - A dictionary with the result of the operation, which will be 'success' if everything went smoothly.

            Note: This function is expected to be called when the client sends a 'join' request via a websocket
            connection.
            """

            try:
                client_name = data['client']
                client_token = data['jwt']
                room = data['room']

            except KeyError as e:
                logging.error(f"Invalid request, missing required field: {e}")
                return {"error": f"Invalid request, missing required field: {e}"}

            try:
                # Validating JWT before allowing the user to JOIN
                if not self.auth_manager.validate_jwt_token(client_name, client_token):
                    logging.error(f"Invalid JWT: {client_token}")
                    return {"error": "Invalid JWT"}

            except redis.exceptions.ConnectionError as e:
                self.stop_chat_server_because_redis_down(e)
                return {"result": "error"}

            logging.info(f"Users currently online: {list(self.users_currently_online)}")

            logging.info(f"Adding a customer to a room: {data['room']}")
            join_room(room)

            time.sleep(CACHED_OFFLINE_MESSAGES_DELAY)

            # Perform only once on each connection
            if client_name not in self.users_currently_online:
                self.users_currently_online.add(client_name)
                # Emit 'new_user_online' to ALL (with current client username)
                self.socketio.emit('new_user_online', {"username": client_name})
                # Emitting messages that were cached for this user, if there are any
                self.publish_cached_messages(client_name)

                # Sending the first, initial 'keep alive' message so the client will be added to the
                # 'keep_alive_tracking" pool
                current_time = datetime.now()
                logging.info(f"Client {client_name} sent 'keep alive' signal at {current_time}")

                # Updating the time at which the 'keep alive' signal was last time received for given user
                self.keep_alive_tracking[client_name] = current_time

            return {"result": "success"}

        @self.socketio.on('client_sends_message')
        def handle_client_message(data):
            """
               Handle incoming message from client.

               This function is triggered by the 'client_sends_message' event, and
               performs the following actions:

               1. Extracts the 'sender', 'jwt', 'conversation_room', and 'content' data
                  from the incoming message.
               2. Validates the JWT token for the sender.
               3. If the conversation_room includes the CHAT_GPT_USER, the message is
                  sent to the ChatGPT instance for processing.

               4. If the conversation_room includes one of the local chat bots names, the message
                  is forwarded to the chatbot_router, so it can send it to the relevant chat bot instance
                  for processing.

               5. If the conversation_room does not include the CHAT_GPT_USER, the
                  message is sent as-is to the intended recipients.

                If the target user is offline at the moment, the message will be cached,
                forwarded to 'handle_messaging_offline_user' method.

                Else it will be sent to the target user - emitted to the Room that contains
                the target user and the message sender in 'received_message' event.

               :param data: Dictionary containing the incoming message data.
               :return: None
            """

            try:
                client_name = data['sender']
                client_token = data['jwt']
                conversation_room = data['conversation_room']
                content = data['content']

            except KeyError as e:
                logging.error(f"Invalid message, missing required field: {e}")
                return

            try:
                # Invalid JWT token in client message
                if not self.auth_manager.validate_jwt_token(client_name, client_token):
                    return send_error_message(f"User '{client_name}' must disconnect, re login and reconnect so the "
                                              f"conversation can be resumed.", client_name)

                # Message sent to ChatGPT
                if CHAT_GPT_USER in conversation_room:
                    chat_gpt_response = self.chatgpt_instance.send_input(content)
                    return send_bot_response(CHAT_GPT_USER, chat_gpt_response, conversation_room)

                # Message sent to one of the local chat bots
                for bot_name in LOCAL_CHAT_BOTS_LIST:
                    if bot_name in conversation_room:
                        local_bot_response = self.chatbot_router.route_incoming_message(bot_name, client_name, content)
                        return send_bot_response(bot_name, local_bot_response, conversation_room)

                # Extracting message target
                message_destination = _extract_target_user(conversation_room, client_name)

                if message_destination not in self.users_list or message_destination is False:
                    logging.error(f"Trying to send a message to non-existing user.")
                    return

                # Handling messages sent to OFFLINE users
                if message_destination not in self.users_currently_online:
                    return self.handle_messaging_offline_user(client_name, message_destination, content, conversation_room)

                # Happy Path - message is instantly delivered to it's destination
                else:
                    return send_message(client_name, content, conversation_room)

            except redis.exceptions.ConnectionError as e:
                logging.critical(f" Alert! Redis DB is down - {e}")
                logging.critical(f"Chat server is going down to prevent further data loss")
                logging.critical(f"Please make sure Redis DB is up and running. "
                                 f"After that please RESTART the Chat Server instance.")

                # If running in a Docker container  - killing the main Chat Server process.
                if os.getenv("KEEP_ALIVE_DELAY_BETWEEN_EVENTS"):
                    os.kill(1, signal.SIGTERM)

                self.socketio.stop()

        def send_message(sender, content, conversation_room):
            """
            Sends a message to a specified conversation room

             Args:
              - sender (str): the name of the sender
              - content (str): the content of the message
              - conversation_room (str): the name of the conversation room

             """

            message = {"sender": sender, "content": content}
            self.socketio.emit('received_message', message, to=conversation_room)

        def send_bot_response(sending_bot, content, conversation_room):
            """
            Forwards a bot response to a specified conversation room

             Args:
              - recipient (str): the name of the recipient
              - content (str): the content of the response
              - conversation_room (str): the name of the conversation room

            """

            message = {"sender": sending_bot, "content": content}
            self.socketio.emit('ai_response_received', message, to=conversation_room)

        def send_error_message(error_message, client_name):
            """
            Sends an error message to a specified recipient (from the Admin user)

            Args:
            - error_message (str): the content of the error message
            - recipient (str): the name of the recipient

            """
            message = {"sender": ADMIN_USER, "content": f"Error! {error_message}"}
            self.socketio.emit('received_message', message, to=f"{ADMIN_USER}&{client_name}")

        def _extract_target_user(conversation_room: str, sender: str):
            split_list = conversation_room.split("&")
            results_list = [x for x in split_list if x != sender]

            if len(results_list) != 1:
                logging.error(f"Invalid conversation room designation: {conversation_room}")
                return False

            return results_list[0]

        @self.socketio.on('client_disconnection')
        def handle_client_disconnection(json_):
            """
              Handles a client disconnection event. Expects a JSON object containing the client name and its JWT token.
              If the token is invalid, logs a warning and returns without doing anything.
              If the client was currently online, removes it from the online users set and deletes its token from Redis.
              Finally, emits a 'user_has_gone_offline' event to notify other users that this client has gone offline.

              Args:
                  json_: A dictionary containing the 'client' and 'jwt' keys.
              """

            logging.info(f"Client disconnection: {json_}")

            try:
                client_name = json_['client']
                client_token = json_['jwt']

            except KeyError as e:
                logging.error(f"Invalid message, missing required fields: {e}")
                return {"error": f"Invalid message, missing required fields: {e}"}

            try:
                # Invalid JWT token in client message
                if not self.auth_manager.validate_jwt_token(client_name, client_token):
                    logging.warning(f"Caution! An unauthorized disconnection attempt was just "
                                    f"performed for user {client_name}!")
                    return

            except redis.exceptions.ConnectionError as e:
                self.stop_chat_server_because_redis_down(e)

            if client_name in self.users_currently_online:
                self.users_currently_online.remove(client_name)
                self.auth_manager.redis_integration.delete_token(client_name)
                self.socketio.emit('user_has_gone_offline', {"username": client_name})

                self.chatbot_router.notify_all_bots_on_user_disconnection(client_name)

            logging.info(f"Users currently online: {list(self.users_currently_online)}")

        @self.socketio.on('connection_alive')
        def processing_keep_alive_signals(json_):
            """
            Handles the "keep alive" signal from the client. This method is expected to be called periodically
            by the client to indicate that the client is still connected and active.

            Args:
                json_: A dictionary containing the client name.
            """
            client_name = json_['client']
            current_time = datetime.now()

            logging.info(f"Client {client_name} sent 'keep alive' signal at {current_time}")

            # Updating the time at which the 'keep alive' signal was last time received for given user
            self.keep_alive_tracking[client_name] = current_time
            logging.info(f"Server Side Keep Alive Time Table Updated: {self.keep_alive_tracking}")

        self.socketio.run(self.app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0')


def fetch_internal_chat_server_config(config_file_path_):
    """
    This method can be used to fetch config either from the environmental variables or from config file
    :param config_file_path_: config file path
    :return: config dict
    """

    result = {}

    try:
        if os.getenv("SQL_USER") is None:
            # Reading DB name, host and credentials from config
            config = configparser.ConfigParser()
            config.read(config_file_path_)
            result["CONNECTIONS_VERIFICATION_INTERVAL"] =\
                int(config.get("CHAT_SERVER_CONFIG", "connections_verification_interval"))
            result["KEEP_ALIVE_DELAY_BETWEEN_EVENTS"] = \
                int(config.get("CHAT_SERVER_CONFIG", "keep_alive_delay_between_events"))

        else:
            result["CONNECTIONS_VERIFICATION_INTERVAL"] = int(os.getenv("CONNECTIONS_VERIFICATION_INTERVAL"))
            result["KEEP_ALIVE_DELAY_BETWEEN_EVENTS"] = int(os.getenv("KEEP_ALIVE_DELAY_BETWEEN_EVENTS"))

        return result

    except FileNotFoundError as e:
        raise ValueError(f"Redis Integration: Error! Config file not found at {config_file_path}") from e

    except KeyError as e:
        raise ValueError(f"Redis Integration: Error! Missing configuration item: {e}") from e

    except ValueError as e:
        raise ValueError(f"Redis Integration: Error! Invalid configuration value: {e}") from e

    except Exception as e:
        raise ValueError(f"Redis Integration: Error! Failed to read configuration: {e}") from e


def connection_checker(chat_instance: ChatServer):
    """
    This method runs in a loop in a separate thread and verifies that each user that
    is expected to be online at the moment sends 'connection_alive' event each X seconds -
    it goes over the table that stores the time when the last 'connection_alive' event was received
    against user name and if the delay is greater than X seconds the user is removed from the 'online users' list,
    the auth. JWT token is removed from Redis and the 'user_has_gone_offline' event is published for all other clients

    :param chat_instance:
    :return:
    """

    chat_internal_config = fetch_internal_chat_server_config(config_file_path)

    CONNECTIONS_VERIFICATION_INTERVAL = chat_internal_config["CONNECTIONS_VERIFICATION_INTERVAL"]
    KEEP_ALIVE_DELAY_BETWEEN_EVENTS = chat_internal_config["KEEP_ALIVE_DELAY_BETWEEN_EVENTS"]

    while True:
        time.sleep(CONNECTIONS_VERIFICATION_INTERVAL)
        logging.info("Verifying active connections..")

        users_to_disconnect = []

        for client_name in chat_instance.keep_alive_tracking:
            last_time_keep_alive_message_received = chat_instance.keep_alive_tracking[client_name]

            if KEEP_ALIVE_LOGGING:
                logging.info(f"User: {client_name}, current time: {datetime.now()}, "
                             f"last time keep alive message was received:"
                      f" {last_time_keep_alive_message_received},"
                      f" delta: {datetime.now() - last_time_keep_alive_message_received} ")

            # Consider the user as disconnected if no 'keep alive' was received for more than X seconds (configurable)
            if datetime.now() - last_time_keep_alive_message_received > timedelta(
                    seconds=KEEP_ALIVE_DELAY_BETWEEN_EVENTS):
                users_to_disconnect.append(client_name)

        chat_bots_manager = LocalChatBotIntegration()

        logging.info(f"Disconnecting users: {users_to_disconnect}")
        for user in users_to_disconnect:
            if user in chat_instance.users_currently_online:
                # Removing the user from 'active users' list and killing the JWT
                try:
                    chat_instance.users_currently_online.remove(user)
                    chat_instance.auth_manager.redis_integration.delete_token(user)
                except KeyError as e:
                    logging.error(f"Connection checker: error removing user JWT - {e}")

            chat_instance.keep_alive_tracking.pop(user)
            chat_instance.socketio.emit('user_has_gone_offline', {"username": user})

            chat_bots_manager.notify_all_bots_on_user_disconnection(user)


if __name__ == '__main__':
    my_chat_server = ChatServer()

    # Not starting the service if the emergency flag is up.
    if emergency_flag is False:
        connection_verification_thread = threading.Thread(target=connection_checker, args=(my_chat_server,))
        connection_verification_thread.start()
        my_chat_server.run()

