import json

from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room

# Will be taken from SQL DB
users_list = ["Lisa", "Avi", "Tsahi", "Era", "Bravo"]

# Will be in service cache AND in DB (Redis DB?)
users_currently_online = []

app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/get_contacts_list/<username>", methods=['GET'])
def get_rooms_list(username):
    contacts_data = {"contacts": prepare_rooms_for(username), "currently_online": users_currently_online}
    return contacts_data

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('join')
def on_join(data):

    client_name = data['client']
    if client_name not in users_currently_online:
        users_currently_online.append(client_name)

    print(f"Users currently online: {users_currently_online}")

    room = data['room']
    print(f"Adding a customer to a room: {data['room']}")
    join_room(room)

    # Emit 'new_user_online' to ALL (with current client username)
    # socketio.emit('received_message', response, callback=messageReceived, to=response["conversation_room"])


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

    print(f"Users currently online: {users_currently_online}")

    # Emit 'user_has_gone_offline' to ALL (with current client username)


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

# API METHOD that will return this in response to GET request with a param (username)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)