import time

import socketio
import requests
import json
import queue
import threading
import logging
import socketio

from QaService.Requests.postman import Postman

CHAT_SERVER_BASE_URL = "http://localhost:5000"

class Listener:

    # A connection to Chat Server will be established (same way as the client does).
    # The method 'start_listening_loop' will run in a separate thread.
    # Every new received event will be inserted into the class variable 'events_received'
    # After test preconditions and test steps are performed the thread with 'start_listening_loop' will stop,
    # and all the events stored in 'events_received' queue will be fetched from the 'Listener' instance and verified.

    events_received = None
    sio = None
    user_logged_in = False

    entry = None
    contacts_list = None
    currently_online_contacts = None
    message_box = None

    connected = False
    my_name = None

    contacts_list_ui_element = None
    current_auth_token = None

    conversation_rooms_list = None

    address_book = {}

    def __init__(self):
        self.events_received = queue.Queue()

        if self.sio is None:
            self.sio = socketio.Client()


    def send_log_in_request(self, username, password):
        """
        This method is used to send HTTP sign in request to the chat server
        :param username: str
        :param password: str
        """

        logging.info(f"App Core: sending a sign in request to the server, username: {username}, password: {password}")

        response = requests.post(url=CHAT_SERVER_BASE_URL + "/log_in",
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
            self.sio.connect(CHAT_SERVER_BASE_URL)
            response = requests.get(f"{CHAT_SERVER_BASE_URL}/get_contacts_list/{self.my_name}",
                                    headers=headers)
            server_contacts_data = json.loads(response.text)

            # All existing contacts
            self.contacts_list = server_contacts_data["contacts"]
            contacts_names = server_contacts_data["all_existing_contacts"]

            for contact in contacts_names:
                self.address_book[contact] = None

            # Contacts that are currently online
            self.currently_online_contacts = server_contacts_data["currently_online"]

            self.conversation_rooms_list = []

            # Establishing contacts with all persons from the Contacts List
            for contact in self.contacts_list:
                conversation_room = self.contacts_list[contact]
                self.conversation_rooms_list.append(conversation_room)
                self.sio.emit('join', {"room": conversation_room, "client": self.my_name,
                                       "jwt": self.current_auth_token})

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
            self.events_received.put(message)

            #print(message)


            # if self.my_name != message['sender']:
            #     logging.info(f"{message['sender']}: {message['content']}")
            #     first_message_conversation = f"{message['sender']}: {message['content']}"
            #
            #     current_messages_box = self.address_book[message['sender']]
            #
            #     # First message from given user
            #     if current_messages_box is None:
            #         t1 = threading.Thread(target=self.message_box.show_message_box,
            #                               args=(first_message_conversation, message['sender']))
            #         t1.start()
            #         time.sleep(6)
            #
            #     # The conversation with the given user is going on, and a Chat Room is already open
            #     else:
            #         current_messages_box.configure(state="normal")
            #         current_messages_box.insert(INSERT, "\n")
            #         current_messages_box.insert(INSERT, f"{message['sender']}: {message['content']}")
            #         current_messages_box.insert(INSERT, "\n")
            #         current_messages_box.see("end")
            #         current_messages_box.configure(state="disabled")

        @self.sio.on('ai_response_received')
        def handle_my_custom_event(message):
            pass

            # print(f"{message['sender']}: {message['content']}")
            # first_message_conversation = f"{message['sender']}: {message['content']}"
            #
            # current_messages_box = self.address_book[message['sender']]
            #
            # # First message from given user
            # if current_messages_box is None:
            #     t1 = threading.Thread(target=self.message_box.show_message_box,
            #                           args=(first_message_conversation, message['sender']))
            #     t1.start()
            #     time.sleep(6)
            #
            # # The conversation with the given user is going on, and a Chat Room is already open
            # else:
            #     current_messages_box.configure(state="normal")
            #     current_messages_box.insert(INSERT, "\n")
            #     current_messages_box.insert(INSERT, f"{message['sender']}: {message['content']}")
            #     current_messages_box.insert(INSERT, "\n")
            #     current_messages_box.see("end")
            #     current_messages_box.configure(state="disabled")

        @self.sio.on('new_user_online')
        def handle_new_user_online(message):
            pass

            # user_name = message["username"]
            #
            # if user_name != self.my_name:
            #     logging.info(f"Handling: new user is now online: {user_name}")
            #     # Color the username in 'self.contacts_list_ui_element' in GREEN
            #     if not self.color_selected_contact(user_name, "green"):
            #         logging.warning(f"Warning: failed to color contact {user_name} in GREEN")

        @self.sio.on('user_has_gone_offline')
        def user_has_gone_offline(message):
            pass

            # user_name = message["username"]
            #
            # if user_name != self.my_name:
            #     logging.info(f"Handling: user has gone offline: {user_name}")
            #     # Color the username in 'self.contacts_list_ui_element' in RED
            #     if not self.color_selected_contact(user_name, "red"):
            #         logging.warning(f"Warning: failed to color contact {user_name} in RED")

    def stop_listening(self):
        self.sio.disconnect()

    def list_recorder_messages(self):
        result = []

        while not self.events_received.empty():
            result.append(self.events_received.get())

        return result

    def get_conversaion_rooms_list(self):
        return self.conversation_rooms_list



if __name__ == '__main__':
    lstn = Listener()
    name = 'Era'
    password = "Come on"
    #jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiTGlzYSJ9.9Jg1IkKdvCGszkyRM5VIKtw-mE4qY57WjZ0YLOPghcE"

    # Logging in, initiating a connection (getting contacts, statuses)
    print(lstn.send_log_in_request(name, password))
    first_response = lstn.initiate_connection()
    print(first_response)

    second_listener = Listener()
    second_listener.send_log_in_request("Lisa", "TestMe")
    second_listener.initiate_connection()



    # Starting listening loop in a separate thread
    t1 = threading.Thread(target=lstn.start_listening_loop)
    t1.start()

    # Sending a message as Lisa to Era. No client is used. 
    postman = Postman()
    postman.emit_send_message(second_listener.sio, "Lisa", 'Era&Lisa', "Test_Auto_Send" , second_listener.current_auth_token)



    t1.join(timeout=10)
    time.sleep(10)

    lstn.stop_listening()
    second_listener.stop_listening()

    print("Extracting content")

    print(lstn.list_recorder_messages())
    print(lstn.get_conversaion_rooms_list())


