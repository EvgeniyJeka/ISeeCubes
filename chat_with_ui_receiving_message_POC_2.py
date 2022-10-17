import time
from tkinter import *
from tkinter import ttk

import socketio
import requests
import json
import threading

# TO DO:
# Add handling ON CONNECT & ON DISCONNECT. KEEP A LIST/DICT OF USERS THAT ARE CURRENTLY CONNECTED.

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

                    current_messages_box = self.address_book[message['sender']]

                    # First message from given user
                    if current_messages_box is None:
                        t1 = threading.Thread(target=self.show_message_box, args=(first_message_conversation, message['sender']))
                        t1.start()
                        time.sleep(6)

                    # The conversation with the given user is going on, and a Chat Room is already open
                    else:
                        current_messages_box.insert(INSERT, "\n")
                        current_messages_box.insert(INSERT, f"{message['sender']}: {message['content']}")

            message = input()
            sio.emit('client_sends_message', {'sender':my_name, "content":message, "conversation_room": conversation_room})


    def show_message_box(self, first_mesage, message_sender):

        # Window size
        hight = 500
        width = 900
        size = '%sx%s' % (width, hight)
        columns_size = 50

        # Window
        root = Tk()
        root.geometry(size)
        root.resizable(0, 0)

        print("Inside show-message-box")

        # Text
        messages_box = Text(root, height=20, width=105)
        messages_box.grid(row=4, column=0, padx=25, pady=10)
        messages_box.grid(columnspan=10)

        # Entry box
        created_entry = Entry(root, width="140")
        created_entry.grid(row=7, column=1, padx=25, pady=5)

        messages_box.insert(INSERT, first_mesage)
        messages_box.insert(INSERT, "\n")

        self.address_book[message_sender] = messages_box


        root.mainloop()

        # secondary = Tk()
        # secondary.geometry("550x100")

        # label_1 = Label(secondary, text=f"Entry {self.cnt}:", fg="blue", font=("", 11))
        # created_entry = Entry(secondary, width="70")
        # created_entry.num = self.cnt
        #
        # label_1.grid(row=0, column=0, sticky=E)
        # created_entry.grid(row=0, column=1)
        #
        # created_entry.insert(0, first_mesage)
        #
        # self.address_book[message_sender] = created_entry
        #
        # self.cnt += 1
        #secondary.mainloop()


if __name__ == '__main__':
    chtr = ChatRoom()



    # # Window size
    # hight = 500
    # width = 900
    # size = '%sx%s' % (width, hight)
    # columns_size = 50
    #
    # # Window
    # root = Tk()
    # root.geometry(size)
    # root.resizable(0, 0)
    #
    # # Text
    # messages_box = Text(root, height=20, width=105)
    # messages_box.grid(row=4, column=0, padx=25, pady=10)
    # messages_box.grid(columnspan=10)
    #
    # # Entry box
    # created_entry = Entry(root, width="140")
    # created_entry.grid(row=7, column=1, padx=25, pady=5)
    #
    # messages_box.insert(INSERT, "Hello.")
    # messages_box.insert(INSERT, "\n")
    # messages_box.insert(INSERT, "Test")
    #
    #
    # root.mainloop()