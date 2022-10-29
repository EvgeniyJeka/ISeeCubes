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
# THINK HOW TO PREVENT THE CONVERSATION ROOM FROM BEING HARDCODED!
# LISA CAN ADDRESS ANY PERSON FROM THE CONTACT LIST, BUT WHEN SHE IS ADDRESSED BY ANOTHER CONTACT
# SHE SHOULD REPLY TO THAT CONTACT.
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

        # Messages Box - TK 'Text' object
        messages_box = Text(message_box_window, height=20, width=105)
        messages_box.grid(row=4, column=0, padx=25, pady=10)
        messages_box.grid(columnspan=10)

        # Entry box
        created_entry = Entry(message_box_window, width="140")
        created_entry.grid(row=7, column=3, padx=25, pady=5, sticky=W)

        messages_box.insert(INSERT, first_mesage)
        messages_box.insert(INSERT, "\n")

        self.address_book[message_sender] = messages_box

        # SEND button - the text from the entry box will be packed to a WS message and the former will be
        # emitted to the conversation room. (Remove 'not my message' validation?)
        button_send = Button(message_box_window, text="Send", bg="purple", fg="white", height="2", width="30",
                             command=lambda :self.handle_send(created_entry, messages_box, "Test destination"))
        button_send.place(x=240, y=380)

        # CLEAR button - clears the entry box
        button_clear = Button(message_box_window, text="Clear", bg="green", fg="white", height="2", width="30",
                              command=lambda: self.handle_clear())
        button_clear.place(x=440, y=380)

        # Handling WINDOW CLOSED - the value related to current message sender in the ADDRESS BOOK is NONE again,
        # so a NEW WINDOW will be opened once a message from that sender is received
        def on_closing():
            self.address_book[message_sender] = None
            message_box_window.destroy()

        message_box_window.protocol("WM_DELETE_WINDOW", on_closing)
        message_box_window.mainloop()


    def handle_send(self, target_entry, target_messages_box, destination):
        """
         # IN PROGRESS!
        :param target_entry:
        :param target_messages_box:
        :param destination:
        :return:
        """
        message_content = target_entry.get()
        print(f"Handling SEND {message_content} to {destination}")

        # CLEAR the ENTRY FIELD
        target_entry.delete(0, 'end')

        # ADD the message to the TEXT BOX (MESSAGE BOX)
        target_messages_box.insert(INSERT, "\n")
        target_messages_box.insert(INSERT, f"{my_name}: {message_content}")
        target_messages_box.insert(INSERT, "\n")

        # SEND the message to the server
        sio.emit('client_sends_message', {'sender': my_name,
                                          "content": message_content,
                                          "conversation_room": conversation_room})

    def handle_clear(self):
        print("Handling CLEAR")







if __name__ == '__main__':
    chtr = ChatRoom()

