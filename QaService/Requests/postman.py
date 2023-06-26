import time

import requests
import socketio
import logging
import json

KEEP_ALIVE_DELAY_BETWEEN_EVENTS = 6


class Postman:

    # HTTP REQUESTS

    # POST
    def send_login_request(self, username, password):
        pass

    # GET
    def send_get_rooms_contacts_request(self, username, jwt):
        pass

    # POST
    def send_get_admin_info_request(self, username, password):
        pass

    # POST
    def send_admin_kill_token_request(self, username, password, token_to_terminate):
        pass

    # WEB SOCKET MESSAGES EMITTED
    def emit_join_event(self, conversation_room, client_name, jwt):

        try:
            sio = socketio.Client()
            sio.emit('join', {"room": conversation_room, "client": client_name, "jwt": jwt})
            return True

        except Exception as e:
            logging.error(f"Failed to emit websocket event JOIN: {e}")
            return False

    def emit_keep_alive_event_loop(self, client_name, iterations):
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
        logging.info(f"SENDING KEEP ALIVE SIGNALS EVERY {KEEP_ALIVE_DELAY_BETWEEN_EVENTS} seconds")

        counter = 0

        # Sending 'connection_alive' event every X seconds while the user is logged in
        while counter < iterations:
            sio = socketio.Client()
            sio.emit('connection_alive', {'client': client_name})
            time.sleep(KEEP_ALIVE_DELAY_BETWEEN_EVENTS)
            counter += 1



    def emit_send_message(self, client_name, conversation_room_, message_content, jwt):

        try:

            # SEND the message to the server
            sio = socketio.Client()
            sio.emit('client_sends_message', {"sender": client_name,
                                              "content": message_content,
                                              "conversation_room": conversation_room_,
                                              "jwt": jwt})

            return True

        except Exception as e:
            logging.error(f"Failed to emit websocket event CLIENT SENDS MESSAGE - {e}")
            return False
