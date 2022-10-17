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

                # Remove this validation? All messages shall be eventually printed to the TEXT Messages Box
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

            # Move to a separate method and link to the 'SEND' button.
            sio.emit('client_sends_message', {'sender': my_name, "content": message, "conversation_room": conversation_room})


    def show_message_box(self, first_mesage, message_sender):

        # Window size
        hight = 500
        width = 900
        size = '%sx%s' % (width, hight)

        # Window
        message_box_window = Tk()
        message_box_window.geometry(size)
        message_box_window.resizable(0, 0)

        #print("Inside show-message-box")

        # Messages Box - TK 'Text' object
        messages_box = Text(message_box_window, height=20, width=105)
        messages_box.grid(row=4, column=0, padx=25, pady=10)
        messages_box.grid(columnspan=10)

        # Entry box
        created_entry = Entry(message_box_window, width="140")
        created_entry.grid(row=7, column=1, padx=25, pady=5)

        messages_box.insert(INSERT, first_mesage)
        messages_box.insert(INSERT, "\n")

        self.address_book[message_sender] = messages_box

        # SEND button - the text from the entry box will be packed to a WS message and the former will be
        # emitted to the conversation room. (Remove 'not my message' validation?)
        button_send = Button(message_box_window, text="Send", bg="purple", fg="white", height="2", width="10")
        button_send.grid(row=14, column=0)

        message_box_window.mainloop()

        # If window is closed (by clicking on X) - set self.address_book[message_sender] = None



if __name__ == '__main__':
    #chtr = ChatRoom()

    # Window size
    hight = 500
    width = 900
    size = '%sx%s' % (width, hight)

    # Window
    message_box_window = Tk()
    message_box_window.geometry(size)
    message_box_window.resizable(0, 0)

    # print("Inside show-message-box")

    # Messages Box - TK 'Text' object
    messages_box = Text(message_box_window, height=20, width=105)
    messages_box.grid(row=4, column=0, padx=25, pady=10)
    messages_box.grid(columnspan=10)

    # Entry box
    created_entry = Entry(message_box_window, width="140")
    created_entry.grid(row=7, column=3, padx=25, pady=5, sticky=W)

    messages_box.insert(INSERT, 'loop')
    messages_box.insert(INSERT, "\n")

    #self.address_book[message_sender] = messages_box


    # SEND button - the text from the entry box will be packed to a WS message and the former will be
    # emitted to the conversation room. (Remove 'not my message' validation?)
    button_send = Button(message_box_window, text="Send", bg="purple", fg="white", height="2", width="30")
    button_send.place(x=25, y=380)


    def on_closing():
        print("Handling WINDOW CLOSED - add //self.address_book[message_sender] = None/")
        message_box_window.destroy()

    message_box_window.protocol("WM_DELETE_WINDOW", on_closing)
    message_box_window.mainloop()

    message_box_window.mainloop()

    # If window is closed (by clicking on X) - set self.address_book[message_sender] = None