import requests
import socketio
import logging


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





