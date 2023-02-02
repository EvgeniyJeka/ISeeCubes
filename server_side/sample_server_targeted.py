import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request
from flask_socketio import SocketIO, join_room
import logging

logging.basicConfig(level=logging.INFO)

# TO DO:
# 1.  Custom 'keep alive' logic both on server and on client side // TEST AGAINST 2-3 CLIENTS, NOT EMULATIONS D
#
# 1.1 Client - while connected, will emit 'connection_alive' event every X seconds (will contain the username) D
#
# 1.2 Server - will keep a dict of all online users and the time when the last 'connection_alive' event was received D
#
# 1.3 Sever - on 'connection_alive' event the dict will be updated (the time) D
#
# 1.4 Server - while the app is running each X seconds the method 'connection_checker' that is running in a separate
# thread will check for each user in the 'online users' dict (see 1.2) if CURRENT_TIME - LAST_TIME_CONNECTION_ALIVE_WAS_RECEVED < T,
# while 'T' is configurable.  If CURRENT_TIME - LAST_TIME_CONNECTION_ALIVE_WAS_RECEVED => T, the connection will be
# considered as DEAD - the user will be removed from the 'online users' list and an 'user_has_gone_offline' event will D
# be published for all other users D
#
# Document methods & events
# Make the server run in a Docker container
# CASE ISSUE - Server and Client side
# handle_client_message - avoid sending user's JWT to another user (client + server side)


# Add 2 variations of import (for Dockerization)
from server_side.authorization_manager import AuthManager

# Config
from server_side.chatgpt_integration import ChatGPTIntegration

CONNECTIONS_VERIFICATION_INTERVAL = 10
KEEP_ALIVE_DELAY_BETWEEN_EVENTS = 8

# Special users
CHAT_GPT_USER = "ChatGPT"
ADMIN_USER = "Admin"


class ChatServer:
    # Will be taken from SQL DB
    users_list = ["Lisa", "Avi", "Tsahi", "Era", "Bravo", "Dariya", CHAT_GPT_USER, ADMIN_USER]

    # Mapping active users against the last time the 'connection_alive' event was received from each
    keep_alive_tracking = {}

    # Will be in service cache AND in DB (Redis DB?)
    users_currently_online = []

    auth_manager = None
    chatgpt_instance = None

    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)

        self.auth_manager = AuthManager()
        self.chatgpt_instance = ChatGPTIntegration()

        # Verifying the ChatGPT service is available
        if self.chatgpt_instance.is_chatgpt_available():
            self.users_currently_online.append(CHAT_GPT_USER)

    def room_names_generator(self, listed_users: list) -> list:
        listed_users.sort()

        res = []

        for i in range(0, len(listed_users)):
            current_user = listed_users[i]

            for user in listed_users[i + 1:]:
                res.append(f"{current_user}&{user}")

        return res

    def prepare_rooms_for(self, current_username: str):
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

    def run(self):

        @self.app.route("/get_contacts_list/<username>", methods=['GET'])
        def get_rooms_list(username):

            user_name = request.headers.get('username')
            jwt_token = request.headers.get('jwt')

            if not all([user_name, jwt_token]):
                return {"error": "The 'get_contact_list' request headers must contain username and jwt fields"}

            logging.info(f"Received a request for contacts, username: '{user_name}',  JWT: {jwt_token}")

            # Validating JWT before allowing the user to get the contacts list
            if not self.auth_manager.validate_jwt_token(user_name, jwt_token):
                logging.error(f"Invalid JWT: {jwt_token}")
                return {"error": "Invalid JWT"}

            contacts_data = {"contacts": self.prepare_rooms_for(username),
                             "currently_online": self.users_currently_online,
                             "all_existing_contacts": self.users_list}

            return contacts_data

        @self.app.route("/log_in", methods=['POST'])
        def login_request():
            request_content = request.get_json()

            try:
                username = request_content['username']
                password = request_content['password']

            except KeyError:
                return {"error": "Invalid Log In request"}

            logging.info(f"New log in request received, username: {username}, password: {password}")
            requested_token = self.auth_manager.generate_jwt_token(username, password)

            return requested_token

        @self.app.route("/admin/kill_token", methods=['POST'])
        def admin_kill_token():
            """
            Extracts JSON data from the request which should contain a 'username', 'password' and 'user_token_terminate' field.
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
                    self.auth_manager.active_tokens.pop(kill_user_token)

                except KeyError:
                    return {"error": f"No JWT for user {kill_user_token}"}

                logging.info(f"Successfully terminated JWT for user: {kill_user_token}")
                return {"result": "success"}

            else:
                return {"error": "Admin access denied"}

        def user_joined():
            print(f"User joined!")

        @self.socketio.on('join')
        def on_join(data):

            try:
                client_name = data['client']
                client_token = data['jwt']
                room = data['room']

            except KeyError as e:
                logging.error(f"Invalid request, missing required field: {e}")
                return {"error": f"Invalid request, missing required field: {e}"}

            # Validating JWT before allowing the user to JOIN
            if not self.auth_manager.validate_jwt_token(client_name, client_token):
                logging.error(f"Invalid JWT: {client_token}")
                return {"error": "Invalid JWT"}

            # Perform only once on each connection
            if client_name not in self.users_currently_online:
                self.users_currently_online.append(client_name)
                # Emit 'new_user_online' to ALL (with current client username)
                self.socketio.emit('new_user_online', {"username": client_name}, callback=user_joined)

            logging.info(f"Users currently online: {self.users_currently_online}")

            logging.info(f"Adding a customer to a room: {data['room']}")
            join_room(room)
            return {"result": "success"}

        @self.socketio.on('client_sends_message')
        def handle_client_message(data):
            """
            This method is used to handle messages received from end client via websocket.
            JWT token is validated. If JWT is invalid, the message isn't handled and the sender receives an error message from Admin.
            If the message destination is another user, the message is redirected to him (published to the relevant conversation room).
            If the message destination is ChatGPT user (or another bot), the message is forwarded to it,
            and bot's response is sent back to the user.
            :param data: message content, dict
            :return:
            """

            logging.info('server responds to: ' + str(data))
            response = data

            try:
                client_name = data['sender']
                client_token = data['jwt']

            except KeyError as e:
                logging.error(f"Invalid message, missing required fields: {e}")
                return {"error": f"Invalid message, missing required fields: {e}"}

            # Invalid JWT token in client message
            if not self.auth_manager.validate_jwt_token(client_name, client_token):
                forwarded_message = {"sender": ADMIN_USER, "content": f"Error! Failed Authorization! "
                f"User '{client_name}' must disconnect, re login and reconnect so the conversation can be resumed."}

                self.socketio.emit('received_message', forwarded_message, to=f"{ADMIN_USER}&{client_name}")
                return

            # Message sent to ChatGPT
            if CHAT_GPT_USER in data["conversation_room"]:
                logging.info(f"Sending this content to ChatGPT: {data['content']}")

                chat_gpt_response = self.chatgpt_instance.send_input(data['content'])
                logging.info(f"Response received from ChatGPT: {chat_gpt_response}")

                forwarded_message = {"sender": CHAT_GPT_USER, "content": chat_gpt_response}
                self.socketio.emit('ai_response_received', forwarded_message, to=response["conversation_room"])
                return

            forwarded_message = {"sender": data['sender'], "content": data['content']}
            self.socketio.emit('received_message', forwarded_message, to=response["conversation_room"])

        @self.socketio.on('client_disconnection')
        def handle_client_disconnection(json_):
            print(f"Client disconnection: {json_}")

            try:
                client_name = json_['client']
                client_token = json_['jwt']

            except KeyError as e:
                logging.error(f"Invalid message, missing required fields: {e}")
                return {"error": f"Invalid message, missing required fields: {e}"}

            # Invalid JWT token in client message
            if not self.auth_manager.validate_jwt_token(client_name, client_token):
                logging.warning(f"Caution! An unauthorized disconnection attempt was just performed for user {client_name}!")
                return

            if client_name in self.users_currently_online:
                self.users_currently_online.remove(client_name)
                self.socketio.emit('user_has_gone_offline', {"username": client_name})

            logging.info(f"Users currently online: {self.users_currently_online}")

        @self.socketio.on('connection_alive')
        def processing_keep_alive_signals(json_):
            client_name = json_['client']
            message_time = json_['time']

            logging.info(f"Client {client_name} sent 'keep alive' signal at {message_time}")

            # Updating the time at which the 'keep alive' signal was last time received for given user
            self.keep_alive_tracking[client_name] = datetime.strptime(message_time, '%m/%d/%y %H:%M:%S')
            logging.info(f"Server Side Keep Alive Time Table Updated: {self.keep_alive_tracking}")

        self.socketio.run(self.app, debug=True, allow_unsafe_werkzeug=True)


def connection_checker(chat_instance: ChatServer):
    while True:
        # IN PROGRESS - SEE
        time.sleep(CONNECTIONS_VERIFICATION_INTERVAL)
        logging.info("Verifying active connections..")

        users_to_disconnect = []

        for client_name in chat_instance.keep_alive_tracking:
            last_time_keep_alive_message_received = chat_instance.keep_alive_tracking[client_name]

            print(f"User: {client_name}, current time: {datetime.now()}, last time keep alive message was received:"
                  f" {last_time_keep_alive_message_received}, delta: {datetime.now() - last_time_keep_alive_message_received} ")

            # Consider the user as disconnected if no 'keep alive' was received for more than X seconds (configurable)
            if datetime.now() - last_time_keep_alive_message_received > timedelta(
                    seconds=KEEP_ALIVE_DELAY_BETWEEN_EVENTS):
                users_to_disconnect.append(client_name)

        logging.info(f"Disconnecting users: {users_to_disconnect}")
        for user in users_to_disconnect:
            if user in chat_instance.users_currently_online:
                # Removing the user from 'active users' list and killing the JWT
                chat_instance.users_currently_online.remove(user)
                if user in chat_instance.auth_manager.active_tokens:
                    chat_instance.auth_manager.active_tokens.pop(user)

            chat_instance.keep_alive_tracking.pop(user)
            chat_instance.socketio.emit('user_has_gone_offline', {"username": user})


if __name__ == '__main__':
    my_chat_server = ChatServer()
    connection_verification_thread = threading.Thread(target=connection_checker, args=(my_chat_server,))
    connection_verification_thread.start()
    my_chat_server.run()
