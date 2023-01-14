import time
from datetime import datetime

import socketio
import requests
import json

# standard Python
sio = socketio.Client()

my_name = "avi"

sio.connect('http://localhost:5000')

response = requests.get(f"http://localhost:5000/get_contacts_list/{my_name}")

contacts_list = json.loads(response.text)["contacts"]

# Establishing contacts with all persons from the Contacts List
for contact in contacts_list:
    conversation_room = contacts_list[contact]
    sio.emit('join', {"room": conversation_room, "client": my_name})

# When choosing the contact we want to converse with
# 'conversation_room' is selected.

# Choosing who do we want to talk with (message target, can be different for each message)
conversation_room = contacts_list["lisa"]


while True:

    time.sleep(4)

    now = datetime.now()
    sio.emit('connection_alive', {'client': my_name,
                                  "time": now.strftime('%m/%d/%y %H:%M:%S')})

    @sio.on('received_message')
    def handle_my_custom_event(message):

        if my_name != message['sender']:
            print(f"{message['sender']}: {message['content']}")

    message = input()
    if message == 'disconnect':
        sio.emit('client_disconnection', {"client": my_name})
        print("Disconnecting")
        break

    sio.emit('client_sends_message', {'sender':my_name, "content":message, "conversation_room": conversation_room})


    # now = datetime.now()
    # sio.emit('connection_alive', {'client': my_name,
    #                               "time": now.strftime('%m/%d/%y %H:%M:%S')})

    time.sleep(6)