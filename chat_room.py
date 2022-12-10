import time
from tkinter import *
from tkinter import ttk
from tkinter import font
from PIL import ImageTk, Image

import socketio
import requests
import json
import threading


# TO DO:
# Address Book - create an empty dict, fill it with DATA RECEIVED FROM THE SERVER ON CONNECTION

# Default window size when there are no bookmarks
height = 475
width = 220

class ChatRoom:

    entry = None
    contacts_list = None
    currently_online_contacts = None

    sio = None
    connected = False

    contacts_list_ui_element = None

    address_book = {
        "avi": None,
        "tsahi": None,
        "era": None,
        "bravo": None
    }

    def __init__(self, contacts_list_ui_element):
        self.contacts_list_ui_element = contacts_list_ui_element

    def initiate_connection(self):
        # CONNECT method
        try:
            self.sio = socketio.Client()

            # Will be replace with the username from the 'Log In' form
            self.my_name = "lisa"

            # GET CONTACTS request
            self.sio.connect('http://localhost:5000')
            response = requests.get(f"http://localhost:5000/get_contacts_list/{self.my_name}")
            server_contacts_data = json.loads(response.text)

            # All existing contacts
            self.contacts_list = server_contacts_data["contacts"]
            # Contacts that are currently online
            self.currently_online_contacts = server_contacts_data["currently_online"]

            # Establishing contacts with all persons from the Contacts List
            for contact in self.contacts_list:
                conversation_room = self.contacts_list[contact]
                self.sio.emit('join', {"room": conversation_room, "client": self.my_name})

            # Returning the list of all available contacts received from the server
            print(f"Contacts list received from the server: {self.contacts_list}")
            print(f"Online contacts list received: {self.currently_online_contacts}")

            return {"contacts": self.contacts_list, "currently_online": self.currently_online_contacts}

        except Exception:
            return False

    def start_listening_loop(self):

        @self.sio.on('received_message')
        def handle_my_custom_event(message):

            if self.my_name != message['sender']:
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

        @self.sio.on('new_user_online')
        def handle_new_user_online(message):
            user_name = message["username"]

            if user_name != self.my_name:
                print(f"Handling: new user is now online: {user_name}")
                # Color the username in 'self.contacts_list_ui_element' in GREEN
                if not self.color_selected_contact(user_name, "green"):
                    print(f"Warning: failed to color contact {user_name} in GREEN")

        @self.sio.on('user_has_gone_offline')
        def user_has_gone_offline(message):
            user_name = message["username"]

            if user_name != self.my_name:
                print(f"Handling: user has gone offline: {user_name}")
                # Color the username in 'self.contacts_list_ui_element' in RED
                if not self.color_selected_contact(user_name, "red"):
                    print(f"Warning: failed to color contact {user_name} in RED")

    # OPEN MESSAGE BOX (method in use)
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
                             command=lambda: self.handle_send(created_entry, messages_box, message_sender.lower()))
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

        # Sending the message to the chat room, so the person defined as "destination" will receive it.
        conversation_room_ = self.contacts_list[destination]

        # CLEAR the ENTRY FIELD
        target_entry.delete(0, 'end')

        # ADD the message to the TEXT BOX (MESSAGE BOX)
        target_messages_box.insert(INSERT, "\n")
        target_messages_box.insert(INSERT, f"{self.my_name}: {message_content}")
        target_messages_box.insert(INSERT, "\n")

        # SEND the message to the server
        self.sio.emit('client_sends_message', {'sender': self.my_name,
                                          "content": message_content,
                                          "conversation_room": conversation_room_})

    def handle_clear(self):
        print("Handling CLEAR")

    def color_online_offline_contacts(self, currently_online_contacts_list: list):
        """
        This method is used to color all contacts in CONTACTS LIST UI ELEMENT that are currently ONLINE
        in GREEN, and all other contacts - in RED.
        :param currently_online_contacts_list: list of str
        :param contacts_list_ui_element: tkinter ui element
        :return: True on success
        """
        try:
            for i in range(0, self.contacts_list_ui_element.size()):
                current_item = self.contacts_list_ui_element.get(i)
                # Online
                if current_item in currently_online_contacts_list:
                    self.contacts_list_ui_element.itemconfig(i, fg='green')
                # Offline
                else:
                    self.contacts_list_ui_element.itemconfig(i, fg='red')

            return True

        except Exception:
            return False

    def color_selected_contact(self, selected_contact, color):
        try:
            for i in range(0, self.contacts_list_ui_element.size()):
                current_item = self.contacts_list_ui_element.get(i)

                if current_item == selected_contact:
                    self.contacts_list_ui_element.itemconfig(i, fg=color)

            return True

        except Exception:
            return False


# if __name__ == '__main__':
#     chtr = ChatRoom()
