import json

from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room

# Will be taken from SQL DB
users_list = ["Lisa", "Avi", "Tsahi", "Era"]

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)

@app.route('/')
def sessions():
    return render_template('session.html')

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('join')
def on_join(data):
    room = data['room']
    print(f"Adding a customer to a room: {data['room']}")
    join_room(room)


@socketio.on('client_sends_message')
def handle_my_custom_event(json_):
    print('server responds to: ' + str(json_))
    response = json_
    # response['source'] = "server"

    socketio.emit('received_message', response, callback=messageReceived, to=response["conversation_room"])


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

if __name__ == '__main__':
    print(prepare_rooms_for("Tsahi"))
    #socketio.run(app, debug=True, allow_unsafe_werkzeug=True)