from tkinter import *
import socketio
import requests
import json
import threading

# Default window size when there are no bookmarks
height = 475
width = 220

# standard Python
sio = socketio.Client()

my_name = "Lisa"

sio.connect('http://localhost:5000')

response = requests.get(f"http://localhost:5000/get_contacts_list/{my_name}")

contacts_list = json.loads(response.text)

# Establishing contacts with all persons from the Contacts List
for contact in contacts_list:
    conversation_room = contacts_list[contact]
    sio.emit('join', {"room": conversation_room})

# When choosing the contact we want to converse with
# 'conversation_room' is selected.

# Choosing who do we want to talk with (message target, can be different for each message)
conversation_room = contacts_list["tsahi"]


class ChatRoom:

    entry = None
    cnt = 0

    address_book = {
        "Avi": None,
        "Tsahi": None,
        "Era": None
    }

    def __init__(self):
        while True:

            @sio.on('received_message')
            def handle_my_custom_event(message):

                if my_name != message['sender']:
                    print(f"{message['sender']}: {message['content']}")
                    first_message_conversation = f"{message['sender']}: {message['content']}"

                    current_entry = self.address_book[message['sender']]

                    # First message from given user
                    if current_entry is None:
                        t1 = threading.Thread(target=self.show_message_box, args=(first_message_conversation, message['sender']))
                        t1.start()

                    current_entry.delete(0, 'end')
                    current_entry.insert(0, f"{message['sender']}: {message['content']}")

            message = input()
            sio.emit('client_sends_message', {'sender':my_name, "content":message, "conversation_room": conversation_room})


    def show_message_box(self, first_mesage, message_sender):
        secondary = Tk()
        secondary.geometry("550x100")

        label_1 = Label(secondary, text=f"Entry {self.cnt}:", fg="blue", font=("", 11))
        created_entry = Entry(secondary, width="70")
        created_entry.num = self.cnt

        label_1.grid(row=0, column=0, sticky=E)
        created_entry.grid(row=0, column=1)

        created_entry.insert(0, first_mesage)

        self.address_book[message_sender] = created_entry

        self.cnt += 1
        secondary.mainloop()


if __name__ == '__main__':
    chtr = ChatRoom()