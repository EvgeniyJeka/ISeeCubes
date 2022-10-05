import socketio
import requests

# standard Python
sio = socketio.Client()

my_name = "Tsahi"

sio.connect('http://localhost:5000')

contacts_list = {
    "Lisa": "lisa&tsahi",
    "Avi": "avi&tsahi"
}

# Establishing contacts with all persons from the Contacts List
for contact in contacts_list:
    conversation_room = contacts_list[contact]
    sio.emit('join', {"room": conversation_room})

# When choosing the contact we want to converse with
# 'conversation_room' is selected.

# Choosing who do we want to talk with (message target, can be different for each message)
conversation_room = contacts_list["Lisa"]

while True:

    @sio.on('received_message')
    def handle_my_custom_event(message):

        if my_name != message['sender']:
            print(f"{message['sender']}: {message['content']}")


    message = input()
    sio.emit('client_sends_message', {'sender': my_name, "content": message, "conversation_room": conversation_room})