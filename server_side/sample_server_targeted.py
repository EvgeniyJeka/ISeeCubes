import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request
from flask_socketio import SocketIO, join_room


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

class ChatServer:

    # Will be taken from SQL DB
    users_list = ["Lisa", "Avi", "Tsahi", "Era", "Bravo", "Dariya", "ChatGPT"]

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
            contacts_data = {"contacts": self.prepare_rooms_for(username), "currently_online": self.users_currently_online,
                             "all_existing_contacts": self.users_list}

            return contacts_data

        @self.app.route("/log_in", methods=['POST'])
        def login_request():
            request_content = request.get_json()

            if 'username' and 'password' not in request_content.keys():
                return {"error": "Invalid Log In request"}

            username = request_content['username']
            password = request_content['password']

            print(username, password)

            requested_token = self.auth_manager.generate_jwt_token(username, password)

            return requested_token


        def user_joined():
            print(f"User joined!")

        @self.socketio.on('join')
        def on_join(data):
            client_name = data['client']
            # client_token = data['jwt']
            #
            # if auth_manager.validate_jwt_token(client_name, client_token):
            #     # Proceed

            # Perform only once on each connection
            if client_name not in self.users_currently_online:
                self.users_currently_online.append(client_name)
                # Emit 'new_user_online' to ALL (with current client username)
                self.socketio.emit('new_user_online', {"username": client_name}, callback=user_joined)

            print(f"Users currently online: {self.users_currently_online}")

            room = data['room']
            print(f"Adding a customer to a room: {data['room']}")
            join_room(room)

        @self.socketio.on('client_sends_message')
        def handle_client_message(json_):
            print('server responds to: ' + str(json_))
            response = json_

            # client_token = json_['jwt']
            #
            # if auth_manager.validate_jwt_token(client_name, client_token):
            #     # Proceed
            # else:
            #   #find a way to notify the client on auth error!
            #   # forwarded_message = {"sender": "admin, "content": "Error! Failed Authorization!"}

            if CHAT_GPT_USER in json_["conversation_room"]:
                print(f"Sending this content to ChatGPT: {json_['content']}")

                chat_gpt_response = self.chatgpt_instance.send_input(json_['content'])
                print(f"Response received from ChatGPT: {chat_gpt_response}")

                forwarded_message = {"sender": CHAT_GPT_USER, "content": chat_gpt_response}
                self.socketio.emit('ai_response_received', forwarded_message, to=response["conversation_room"])
                return

            forwarded_message = {"sender": json_['sender'], "content": json_['content']}
            self.socketio.emit('received_message', forwarded_message, to=response["conversation_room"])


        @self.socketio.on('client_disconnection')
        def handle_client_disconnection(json_):
            print(f"Client disconnection: {json_}")

            client_name = json_['client']
            # client_token = json_['jwt']
            #
            # if verified_client_token(client_name, client_token):
            #     # Proceed

            if client_name in self.users_currently_online:
                self.users_currently_online.remove(client_name)
                self.socketio.emit('user_has_gone_offline', {"username": client_name})

            print(f"Users currently online: {self.users_currently_online}")


        @self.socketio.on('connection_alive')
        def processing_keep_alive_signals(json_):
            client_name = json_['client']
            message_time = json_['time']

            print(f"Client {client_name} sent 'keep alive' signal at {message_time}")

            # Updating the time at which the 'keep alive' signal was last time received for given user
            self.keep_alive_tracking[client_name] = datetime.strptime(message_time, '%m/%d/%y %H:%M:%S')
            print(f"Server Side Keep Alive Time Table Updated: {self.keep_alive_tracking}")


        self.socketio.run(self.app, debug=True, allow_unsafe_werkzeug=True)


def connection_checker(chat_instance: ChatServer):
    while True:
        # IN PROGRESS - SEE
        time.sleep(CONNECTIONS_VERIFICATION_INTERVAL)
        print("Verifying active connections..")

        users_to_disconnect = []

        for client_name in chat_instance.keep_alive_tracking:
            last_time_keep_alive_message_received = chat_instance.keep_alive_tracking[client_name]

            # print(f"User: {client_name}, current time: {datetime.now()}, last time keep alive message was received:"
            #       f" {last_time_keep_alive_message_received}, delta: {datetime.now() - last_time_keep_alive_message_received} ")

            # Consider the user as disconnected if no 'keep alive' was received for more than X seconds (configurable)
            if datetime.now() - last_time_keep_alive_message_received > timedelta(seconds=KEEP_ALIVE_DELAY_BETWEEN_EVENTS):
                users_to_disconnect.append(client_name)

        print(f"Disconnecting users: {users_to_disconnect}")
        for user in users_to_disconnect:
            if user in chat_instance.users_currently_online:
                chat_instance.users_currently_online.remove(user)

            chat_instance.keep_alive_tracking.pop(user)
            chat_instance.socketio.emit('user_has_gone_offline', {"username": user})



if __name__ == '__main__':
    my_chat_server = ChatServer()
    connection_verification_thread = threading.Thread(target=connection_checker, args=(my_chat_server,))
    connection_verification_thread.start()
    my_chat_server.run()
