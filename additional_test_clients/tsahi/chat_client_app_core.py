import time
from datetime import datetime
from tkinter import *

import socketio
import requests
import json
import threading
import logging

from socketio import exceptions

from additional_test_clients.lisa.local_client_config import AppConfig
from additional_test_clients.lisa.pop_up_window import PopupWindow

logging.basicConfig(level=logging.INFO)


# Default window size when there are no bookmarks
from additional_test_clients.tsahi.message_box import MessageBox


class ClientAppCore:

    entry = None
    contacts_list = None
    currently_online_contacts = None
    message_box = None

    sio = None
    connected = False
    my_name = None

    contacts_list_ui_element = None
    connection_indicator_ui_element = None

    current_auth_token = None

    user_logged_in = False

    address_book = {}

    def __init__(self, contacts_list_ui_element, connection_indicator_ui_element):
        self.contacts_list_ui_element, self.connection_indicator_ui_element = \
            contacts_list_ui_element, connection_indicator_ui_element

    def send_log_in_request(self, username, password):
        """
        This method is used to send HTTP sign in request to the chat server
        :param username: str
        :param password: str
        """

        logging.info(f"App Core: sending a sign in request to the server, username: {username}, password: {password}")

        response = requests.post(url=AppConfig.CHAT_SERVER_BASE_URL.value + "/log_in",
                                 json={"username": username, "password": password})
        sign_in_data = json.loads(response.text)

        if 'result' in sign_in_data.keys():
            if sign_in_data['result'] == 'success':
                self.my_name = username
                self.current_auth_token = sign_in_data['token']
                self.user_logged_in = True
                return {"result": "success"}

            elif sign_in_data['result'] == 'Invalid credentials':
                return {"result": "Invalid credentials"}
            else:
                return {"result": "Unknown server code"}
        else:
            return {"result": "server error"}

    def initiate_connection(self):
        """
        This method can be used to initiate connection to the chat server after the user is logged in.
        The header of each request contains the JWT that was received from the server after log in.
        The connection procedure includes:
            - connection to chat server web socket
            - contacts list request (the response includes all existing contacts, those that are currently online
                                     and a list of room names that the specified user is a member of)
            - sending 'join' request (web socket message) to each room on the rooms list

            - initiating the MessageBox instance.

        After the connection was initiated the server will add the newly connected client to the list
        of users, that are currently online, notify all other users and publish all cached messages
        to the newly joined user that were sent to him while he was offline by other users.

        :return: dict (with all the relevant data).
        """
        try:
            if self.sio is None:
                self.sio = socketio.Client()

            if self.user_logged_in is False:
                logging.warning("Core App: user isn't logged in, can't connect!")
                return False

            headers = {"username": self.my_name, "jwt": self.current_auth_token}

            # GET CONTACTS request
            self.sio.connect(AppConfig.CHAT_SERVER_BASE_URL.value)
            response = requests.get(f"{AppConfig.CHAT_SERVER_BASE_URL.value}/get_contacts_list/{self.my_name}",
                                    headers=headers)
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
                self.sio.emit('join', {"room": conversation_room, "client": self.my_name,
                                       "jwt": self.current_auth_token})

            self.message_box = MessageBox(self)

            # Returning the list of all available contacts received from the server
            logging.info(f"Contacts list received from the server: {self.contacts_list}")
            logging.info(f"Online contacts list received: {self.currently_online_contacts}")

            return {"contacts": self.contacts_list,
                    "currently_online": self.currently_online_contacts, "my_name": self.my_name}

        except Exception as e:
            logging.error(f"Failed to connect: {e}")
            return False

    def start_listening_loop(self):
        """
        When this method is called the client starts listening to the events incoming from the chat server.
        - Once 'received_message' event  is received the message is presented to the user in a Message Box that opens
          in a separate thread

        - Same handling for 'ai_response_received' (message from a bot)

        - Once 'new_user_online' event is received the color of the user name in client UI is changed to GREEN

        - Once 'user_has_gone_offline' event is received the color of the user name in client UI is changed to RED

        All server events that will be added in the future will be handled under this method
        """
        @self.sio.on('received_message')
        def handle_my_custom_event(message):

            if self.my_name != message['sender']:
                logging.info(f"{message['sender']}: {message['content']}")
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
                logging.info(f"Handling: new user is now online: {user_name}")
                # Color the username in 'self.contacts_list_ui_element' in GREEN
                if not self.color_selected_contact(user_name, "green"):
                    logging.warning(f"Warning: failed to color contact {user_name} in GREEN")

        @self.sio.on('user_has_gone_offline')
        def user_has_gone_offline(message):
            user_name = message["username"]

            if user_name != self.my_name:
                logging.info(f"Handling: user has gone offline: {user_name}")
                # Color the username in 'self.contacts_list_ui_element' in RED
                if not self.color_selected_contact(user_name, "red"):
                    logging.warning(f"Warning: failed to color contact {user_name} in RED")

    def sending_keep_alive_loop(self):
        """
        This method continuously sends "connection_alive" events to a server using Socket.IO
        while the user is logged in.
        The function first logs a message indicating that it will send keep-alive signals every
        keep_alive_delay_between_events seconds.

        It then enters an infinite loop using while self.user_logged_in,
        which will run as long as the user_logged_in variable is set to True.
        In each iteration of the loop, the current date and time is retrieved using datetime.now(),
        and a "connection_alive" event is emitted to the server with a dictionary as
        the payload that contains the client's name and the current time.

        Finally, the function uses time.sleep(keep_alive_delay_between_events)
        to pause the loop for keep_alive_delay_between_events seconds before emitting the next "connection_alive" event.
        :return:
        """
        logging.info(f"SENDING KEEP ALIVE SIGNALS EVERY {AppConfig.KEEP_ALIVE_DELAY_BETWEEN_EVENTS.value} seconds")

        # Sending 'connection_alive' event every X seconds while the user is logged in
        while self.user_logged_in:
            try:
                self.sio.emit('connection_alive', {'client': self.my_name})
                time.sleep(AppConfig.KEEP_ALIVE_DELAY_BETWEEN_EVENTS.value)

            except socketio.exceptions.BadNamespaceError as e:
                # Server is down - the handling will START here (temp)
                logging.error(f"Connection terminated - server is unavailable! {e}")
                self.handle_server_connection_lost()

    def handle_server_connection_lost(self):
        # time.sleep(5)
        logging.error(f"Handling critical issue - connection lost with the Chat Server")

        self.user_logged_in = False
        self.connected = False
        self.sio = None

        self.contacts_list_ui_element.delete(0, END)
        self.connection_indicator_ui_element.config(text="Server Error", fg="red4")

        # Presenting the error message defined for given case
        error_message = PopupWindow('SERVER_TEMPORARY_DOWN')
        error_message.show_pop_up()


    def color_online_offline_contacts(self, currently_online_contacts_list: list):
        """
        This method is used to color all contacts in CONTACTS LIST UI ELEMENT that are currently ONLINE
        in GREEN, and all other contacts - in RED.
        :param currently_online_contacts_list: list of str
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

        except Exception as e:
            logging.error(f"Failed to color online/offline contacts: {e}")
            return False

    def color_selected_contact(self, selected_contact, color):
        try:
            for i in range(0, self.contacts_list_ui_element.size()):
                current_item = self.contacts_list_ui_element.get(i)

                if current_item == selected_contact:
                    self.contacts_list_ui_element.itemconfig(i, fg=color)

            return True

        except Exception as e:
            logging.error(f"Failed to color the selected contact: {e}")
            return False

