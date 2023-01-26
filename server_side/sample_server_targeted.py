import json

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


import threading
import time
from datetime import datetime, timedelta

from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room

# Add 2 variations of import (for Dockerization)
from server_side.authorization_manager import AuthManager

# Will be taken from SQL DB
users_list = ["Lisa", "Avi", "Tsahi", "Era", "Bravo", "Dariya"]

# Mapping active users against the last time the 'connection_alive' event was received from each
keep_alive_tracking = {}

# Will be in service cache AND in DB (Redis DB?)
users_currently_online = []


# Config
CONNECTIONS_VERIFICATION_INTERVAL = 10
KEEP_ALIVE_DELAY_BETWEEN_EVENTS = 8

app = Flask(__name__)
socketio = SocketIO(app)

auth_manager = AuthManager()


@app.route("/get_contacts_list/<username>", methods=['GET'])
def get_rooms_list(username):
    contacts_data = {"contacts": prepare_rooms_for(username), "currently_online": users_currently_online,
                     "all_existing_contacts": users_list}

    return contacts_data

# def messageReceived(methods=['GET', 'POST']):
#     print('message was received!!!')

def user_joined():
    print(f"User joined!")

@socketio.on('join')
def on_join(data):
    client_name = data['client']
    # client_token = data['jwt']
    #
    # if auth_manager.validate_jwt_token(client_name, client_token):
    #     # Proceed

    # Perform only once on each connection
    if client_name not in users_currently_online:
        users_currently_online.append(client_name)
        # Emit 'new_user_online' to ALL (with current client username)
        socketio.emit('new_user_online', {"username": client_name}, callback=user_joined)

    print(f"Users currently online: {users_currently_online}")

    room = data['room']
    print(f"Adding a customer to a room: {data['room']}")
    join_room(room)


@socketio.on('client_sends_message')
def handle_client_message(json_):
    print('server responds to: ' + str(json_))
    response = json_

    # client_token = json_['jwt']
    #
    # if verified_client_token(client_name, client_token):
    #     # Proceed

    forwarded_message = {"sender": json_['sender'], "content": json_['content']}

    socketio.emit('received_message', forwarded_message, to=response["conversation_room"])


@socketio.on('client_disconnection')
def handle_client_disconnection(json_):
    print(f"Client disconnection: {json_}")

    client_name = json_['client']
    # client_token = json_['jwt']
    #
    # if verified_client_token(client_name, client_token):
    #     # Proceed

    if client_name in users_currently_online:
        users_currently_online.remove(client_name)
        socketio.emit('user_has_gone_offline', {"username": client_name})

    print(f"Users currently online: {users_currently_online}")


@socketio.on('connection_alive')
def processing_keep_alive_signals(json_):
    client_name = json_['client']
    message_time = json_['time']

    print(f"Client {client_name} sent 'keep alive' signal at {message_time}")

    # Updating the time at which the 'keep alive' signal was last time received for given user
    keep_alive_tracking[client_name] = datetime.strptime(message_time, '%m/%d/%y %H:%M:%S')
    print(f"Server Side Keep Alive Time Table Updated: {keep_alive_tracking}")


def room_names_generator(listed_users: list)-> list:
    # listed_users = [user for user in users_list]
    listed_users.sort()

    res = []

    for i in range(0, len(listed_users)):
        current_user = listed_users[i]

        for user in listed_users[i + 1:]:
            res.append(f"{current_user}&{user}")

    return res


def prepare_rooms_for(current_username: str):
    result = {}

    all_available_rooms = room_names_generator(users_list)

    for room_name in all_available_rooms:
        if current_username in room_name:
            names = room_name.split('&')

            if names[0] == current_username:
                result[names[1]] = room_name
            elif names[1] == current_username:
                result[names[0]] = room_name

    return result


def connection_checker():
    while True:
        # IN PROGRESS - SEE
        time.sleep(CONNECTIONS_VERIFICATION_INTERVAL)
        print("Verifying active connections..")

        users_to_disconnect = []

        for client_name in keep_alive_tracking:
            last_time_keep_alive_message_received = keep_alive_tracking[client_name]

            print(f"User: {client_name}, current time: {datetime.now()}, last time keep alive message was received:"
                  f" {last_time_keep_alive_message_received}, delta: {datetime.now() - last_time_keep_alive_message_received} ")

            # Consider the user as disconnected if no 'keep alive' was received for more than X seconds (configurable)
            if datetime.now() - last_time_keep_alive_message_received > timedelta(seconds=KEEP_ALIVE_DELAY_BETWEEN_EVENTS):
                users_to_disconnect.append(client_name)

        print(f"Disconnecting users: {users_to_disconnect}")
        for user in users_to_disconnect:
            if user in users_currently_online:
                users_currently_online.remove(user)

            keep_alive_tracking.pop(user)
            socketio.emit('user_has_gone_offline', {"username": user})

# API METHOD that will return this in response to GET request with a param (username)

if __name__ == '__main__':
    connection_verification_thread = threading.Thread(target=connection_checker)
    connection_verification_thread.start()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)