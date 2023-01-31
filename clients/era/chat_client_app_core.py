import time
from datetime import datetime
from tkinter import *

import socketio
import requests
import json
import threading


# TO DO:
# Address Book - create an empty dict, fill it with DATA RECEIVED FROM THE SERVER ON CONNECTION D

# Default window size when there are no bookmarks
from clients.era.message_box import MessageBox

# Move to config
keep_alive_delay_between_events = 6

class ClientAppCore:

    entry = None
    contacts_list = None
    currently_online_contacts = None
    message_box = None

    sio = None
    connected = False
    my_name = None

    contacts_list_ui_element = None
    current_auth_token = None

    user_logged_in = False

    address_book = {}

    def __init__(self, contacts_list_ui_element):
        self.contacts_list_ui_element = contacts_list_ui_element

    def send_log_in_request(self, username, password):
        # IN PROGRESS! #

        print(f"App Core: sending a sign in request to the server, username: {username}, password: {password}")
        response = json.dumps({'result': 'success', 'key': '1245Test'}) # Temporary stub for client side
        sign_in_data = json.loads(response)

        if 'result' in sign_in_data.keys():
            if sign_in_data['result'] == 'success':
                self.my_name = username
                self.current_auth_token = sign_in_data['key']
                self.user_logged_in = True
                return {"result": "success"}

            elif sign_in_data['result'] == 'wrong credentials':
                return {"result": "wrong credentials"}
        else:
            return {"result": "server error"}


    def initiate_connection(self):
        # CONNECT method
        try:
            self.sio = socketio.Client()

            if self.user_logged_in is False:
                print("Core App: user isn't logged in, can't connect!")
                return False

            # GET CONTACTS request
            self.sio.connect('http://localhost:5000')
            response = requests.get(f"http://localhost:5000/get_contacts_list/{self.my_name}")
            server_contacts_data = json.loads(response.text)

            # All existing contacts
            self.contacts_list = server_contacts_data["contacts"]
            contacts_names = server_contacts_data["all_existing_contacts"]

            for contact in contacts_names:
                self.address_book[contact] = None

            # Contacts that are currently online
            self.currently_online_contacts = server_contacts_data["currently_online"]

            # Establishing contacts with all persons from the Contacts List
            for contact in self.contacts_list:
                conversation_room = self.contacts_list[contact]
                self.sio.emit('join', {"room": conversation_room, "client": self.my_name, "jwt": self.current_auth_token})

            self.message_box = MessageBox(self)

            # Returning the list of all available contacts received from the server
            print(f"Contacts list received from the server: {self.contacts_list}")
            print(f"Online contacts list received: {self.currently_online_contacts}")

            return {"contacts": self.contacts_list, "currently_online": self.currently_online_contacts, "my_name": self.my_name}

        except Exception as e:
            print(f"Failed to connect: {e}")
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
                    t1 = threading.Thread(target=self.message_box.show_message_box, args=(first_message_conversation, message['sender']))
                    t1.start()
                    time.sleep(6)

                # The conversation with the given user is going on, and a Chat Room is already open
                else:
                    current_messages_box.configure(state="normal")
                    current_messages_box.insert(INSERT, "\n")
                    current_messages_box.insert(INSERT, f"{message['sender']}: {message['content']}")
                    current_messages_box.insert(INSERT, "\n")
                    current_messages_box.see("end")
                    current_messages_box.configure(state="disabled")

        @self.sio.on('ai_response_received')
        def handle_my_custom_event(message):

            print(f"{message['sender']}: {message['content']}")
            first_message_conversation = f"{message['sender']}: {message['content']}"

            current_messages_box = self.address_book[message['sender']]

            # First message from given user
            if current_messages_box is None:
                t1 = threading.Thread(target=self.message_box.show_message_box,
                                      args=(first_message_conversation, message['sender']))
                t1.start()
                time.sleep(6)

            # The conversation with the given user is going on, and a Chat Room is already open
            else:
                current_messages_box.configure(state="normal")
                current_messages_box.insert(INSERT, "\n")
                current_messages_box.insert(INSERT, f"{message['sender']}: {message['content']}")
                current_messages_box.insert(INSERT, "\n")
                current_messages_box.see("end")
                current_messages_box.configure(state="disabled")

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


    def sending_keep_alive_loop(self):
        print(f"SENDING KEEP ALIVE SIGNALS EVERY {keep_alive_delay_between_events} seconds")

        while True:
            now = datetime.now()
            self.sio.emit('connection_alive', {'client': self.my_name,
                                               "time": now.strftime('%m/%d/%y %H:%M:%S')})

            time.sleep(keep_alive_delay_between_events)

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
