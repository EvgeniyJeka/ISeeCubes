import json

# TO DO:
# 1.  Custom 'keep alive' logic both on server and on client side
#
# 1.1 Client - while connected, will emit 'connection_alive' event every X seconds (will contain the username)
#
# 1.2 Server - will keep a dict of all online users and the time when the last 'connection_alive' event was received
#
# 1.3 Sever - on 'connection_alive' event the dict will be updated (the time)
#
# 1.4 Server - while the app is running each X seconds the method 'connection_checker' that is running in a separate
# thread will check for each user in the 'online users' dict (see 1.2) if CURRENT_TIME - LAST_TIME_CONNECTION_ALIVE_WAS_RECEVED < T,
# while 'T' is configurable.  If CURRENT_TIME - LAST_TIME_CONNECTION_ALIVE_WAS_RECEVED => T, the connection will be
# considered as DEAD - the user will be removed from the 'online users' list and an 'user_has_gone_offline' event will
# be published for all other users.


import threading
import time
from datetime import datetime

from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room

# Will be taken from SQL DB
users_list = ["Lisa", "Avi", "Tsahi", "Era", "Bravo"]

keep_alive_tracking = {}

# Will be in service cache AND in DB (Redis DB?)
users_currently_online = []

# Mapping active users against the last time the 'connection_alive' event was received from each
connection_keep_alive = {}


# Config
CONNECTIONS_VERIFICATION_INTERVAL = 10

app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/get_contacts_list/<username>", methods=['GET'])
def get_rooms_list(username):
    contacts_data = {"contacts": prepare_rooms_for(username), "currently_online": users_currently_online}
    return contacts_data

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

def user_joined():
    print(f"User joined!")

@socketio.on('join')
def on_join(data):
    client_name = data['client']

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

    socketio.emit('received_message', response, callback=messageReceived, to=response["conversation_room"])


@socketio.on('client_disconnection')
def handle_client_disconnection(json_):
    print(f"Client disconnection: {json_}")

    client_name = json_['client']
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


def room_names_generator(users_list: list)-> list:
    listed_users = [user.lower() for user in users_list]
    listed_users.sort()

    res = []

    for i in range(0, len(listed_users)):
        current_user = listed_users[i]

        for user in listed_users[i + 1:]:
            res.append(f"{current_user}&{user}")

    return res


def prepare_rooms_for(username: str):
    result = {}

    all_available_rooms = room_names_generator(users_list)
    current_username = username.lower()

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

# API METHOD that will return this in response to GET request with a param (username)

if __name__ == '__main__':
    connection_verification_thread = threading.Thread(target=connection_checker)
    connection_verification_thread.start()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)