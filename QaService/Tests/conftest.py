import logging
import threading
import time
import json

import pytest
import os

from QaService.Tools.listener import Listener

logging.basicConfig(level=logging.INFO)

admin_username = "Admin"
admin_password = "AdminPassword"


def stop_all_listeners(list_of_listeners):
    for listener in list_of_listeners:
        if listener:
            logging.warning(f"Stopping Listener {listener}")
            listener.stop_listening()


@pytest.fixture(scope="class")
def send_single_message(request):
    """
    This fixture sends a SINGLE message from one user to another.
    Credentials and message content are taken from provided params.

    1. Sender - logs in, connects
    2. Receiver - logs in, connects.
    3. Receiver starts to listen to the web socket event emitted by the Chat Server in a separate thread
    4. Verifying the status of both 'Sender' and  the 'Receiver' is "online" (so the messages won't be cached)
    5. Sender sends a single message (emits a web socket event)
    6. Listening loop is stopped, all the messages that were received by the Receiver are returned to the calling test

    :param request:
    :return:
    """

    test_params = request.param[0]

    sender_username = test_params['sender_username']
    sender_password = test_params['sender_password']

    receiver_username = test_params['receiver_username']
    receiver_password = test_params['receiver_password']

    message_content = test_params['message_content']

    # First user (sender) - log in and connect
    first_user_websocket_listener = Listener(sender_username)
    response = first_user_websocket_listener.send_log_in_request(sender_username, sender_password)

    logging.info(f"First user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = first_user_websocket_listener.initiate_connection()
    logging.info(f"First user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # # Waiting for  user status to change (so he/she will be ONLINE when the message is sent).
    time.sleep(3)

    # Second user (receiver) - log in and connect
    second_user_websocket_listener = Listener(receiver_username)
    response = second_user_websocket_listener.send_log_in_request(receiver_username, receiver_password)

    logging.info(f"Second user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = second_user_websocket_listener.initiate_connection()
    logging.info(
        f"Second user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # Waiting for  user status to change (so he/she will be ONLINE when the message is sent).
    time.sleep(5)

    # Starting listening loop in a separate thread
    listening_thread = threading.Thread(target=second_user_websocket_listener.start_listening_loop)
    listening_thread.start()
    listening_thread.join(timeout=6)

    # Verifying both SENDER and RECEIVER are ONLINE when the test is performed
    response = first_user_websocket_listener.send_get_admin_info_request(admin_username, admin_password)
    data = json.loads(response.content)
    users_online = data['online_clients_list']

    assert sender_username in users_online, logging.error(f"Sender {sender_username} not online")
    assert receiver_username in users_online, logging.error(f"Receiver {receiver_username} not online")

    # Sending a message as Era to Lisa. No client is used.
    first_user_websocket_listener.emit_send_message(
                              sender_username,
                              f'{sender_username}&{receiver_username}',
                              message_content,
                              first_user_websocket_listener.current_auth_token)

    time.sleep(7)

    stop_all_listeners([first_user_websocket_listener, second_user_websocket_listener])

    print("Extracting content")

    result = second_user_websocket_listener.list_recorder_messages()
    print(result)
    return result


@pytest.fixture(scope="class")
def send_several_messages(request):
    """
       This fixture sends a SEVERAL messages from one user to another.
       Credentials and message content are taken from provided params.

       1. Sender - logs in, connects
       2. Receiver - logs in, connects.
       3. Receiver starts to listen to the web socket event emitted by the Chat Server in a separate thread
       4. Verifying the status of both 'Sender' and  the 'Receiver' is "online" (so the messages won't be cached)
       5. Sender sends the first message (emits a web socket event)
       6. Sender sends the second message (emits a web socket event)
       6. Listening loop is stopped, all the messages that were received by the Receiver are returned to the calling test

       :param request:
       :return:
       """
    test_params = request.param[0]

    sender_username = test_params['sender_username']
    sender_password = test_params['sender_password']

    receiver_username = test_params['receiver_username']
    receiver_password = test_params['receiver_password']

    first_message, second_message = test_params['messages_content']

    # First user (sender) - log in and connect
    first_user_websocket_listener = Listener(sender_username)
    response = first_user_websocket_listener.send_log_in_request(sender_username, sender_password)

    logging.info(f"First user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = first_user_websocket_listener.initiate_connection()
    logging.info(f"First user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # # Waiting for  user status to change (so he/she will be ONLINE when the message is sent).
    time.sleep(3)

    # Second user (receiver) - log in and connect
    second_user_websocket_listener = Listener(receiver_username)
    response = second_user_websocket_listener.send_log_in_request(receiver_username, receiver_password)

    logging.info(f"Second user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = second_user_websocket_listener.initiate_connection()
    logging.info(
        f"Second user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # Waiting for  user status to change (so he/she will be ONLINE when the message is sent).
    time.sleep(5)

    # Starting listening loop in a separate thread
    listening_thread = threading.Thread(target=second_user_websocket_listener.start_listening_loop)
    listening_thread.start()
    listening_thread.join(timeout=6)

    # Verifying both SENDER and RECEIVER are ONLINE when the test is performed
    response = first_user_websocket_listener.send_get_admin_info_request(admin_username, admin_password)
    data = json.loads(response.content)
    users_online = data['online_clients_list']

    assert sender_username in users_online, logging.error(f"Sender {sender_username} not online")
    assert receiver_username in users_online, logging.error(f"Receiver {receiver_username} not online")

    # Sending the first message as Era to Lisa.
    first_user_websocket_listener.emit_send_message(
        sender_username,
        f'{sender_username}&{receiver_username}',
        first_message,
        first_user_websocket_listener.current_auth_token)

    # Sending the second message as Era to Lisa.
    first_user_websocket_listener.emit_send_message(
        sender_username,
        f'{sender_username}&{receiver_username}',
        second_message,
        first_user_websocket_listener.current_auth_token)

    time.sleep(7)

    stop_all_listeners([first_user_websocket_listener, second_user_websocket_listener])

    print("Extracting content")

    result = second_user_websocket_listener.list_recorder_messages()
    print(result)
    return result


@pytest.fixture(scope="class")
def send_messages_to_different_users(request):
    """
       ..

       1. Sender - logs in, connects
       2. Receiver - logs in, connects.
       3. Receiver starts to listen to the web socket event emitted by the Chat Server in a separate thread
       4. Verifying the status of both 'Sender' and  the 'Receiver' is "online" (so the messages won't be cached)
       5. Sender sends the first message (emits a web socket event)
       6. Sender sends the second message (emits a web socket event)
       6. Listening loop is stopped, all the messages that were received by the Receiver are returned to the calling test

       :param request:
       :return:
       """

    test_params = request.param[0]

    sender_username = test_params['sender_username']
    sender_password = test_params['sender_password']

    first_receiver_username = test_params['first_receiver_username']
    first_receiver_password = test_params['first_receiver_password']

    second_receiver_username = test_params['second_receiver_username']
    second_receiver_password = test_params['second_receiver_password']

    first_message, second_message = test_params['messages_content']

    # First user (sender) - log in and connect
    first_user_websocket_listener = Listener(sender_username)
    response = first_user_websocket_listener.send_log_in_request(sender_username, sender_password)

    logging.info(f"First user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = first_user_websocket_listener.initiate_connection()
    logging.info(f"First user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # # Waiting for  user status to change (so he/she will be ONLINE when the message is sent).
    time.sleep(3)

    # Second user (receiver) - log in and connect
    second_user_websocket_listener = Listener(first_receiver_username)
    response = second_user_websocket_listener.send_log_in_request(first_receiver_username, first_receiver_password)

    logging.info(f"Second user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = second_user_websocket_listener.initiate_connection()
    logging.info(
        f"Second user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # Third user (receiver) - log in and connect
    third_user_websocket_listener = Listener(second_receiver_username)
    response = third_user_websocket_listener.send_log_in_request(second_receiver_username, second_receiver_password)

    logging.info(f"Third user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = third_user_websocket_listener.initiate_connection()
    logging.info(
        f"Third user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # Waiting for  user status to change (so he/she will be ONLINE when the message is sent).
    time.sleep(5)

    # Starting listening loop in a separate thread
    listening_thread_first = threading.Thread(target=second_user_websocket_listener.start_listening_loop)
    listening_thread_first.start()
    listening_thread_first.join(timeout=6)

    # Starting listening loop in a separate thread
    listening_thread_second = threading.Thread(target=third_user_websocket_listener.start_listening_loop)
    listening_thread_second.start()
    listening_thread_second.join(timeout=6)

    # Verifying both SENDER and BOTH RECEIVERS are ONLINE when the test is performed
    response = first_user_websocket_listener.send_get_admin_info_request(admin_username, admin_password)
    data = json.loads(response.content)
    users_online = data['online_clients_list']

    assert sender_username in users_online, logging.error(f"Sender {sender_username} not online")
    assert first_receiver_username in users_online, logging.error(f"Receiver {first_receiver_username} not online")
    assert second_receiver_username in users_online, logging.error(f"Receiver {second_receiver_password} not online")

    # Sending the first message as Era to Lisa.
    first_user_websocket_listener.emit_send_message(
        sender_username,
        f'{sender_username}&{first_receiver_username}',
        first_message,
        first_user_websocket_listener.current_auth_token)

    # Sending the second message as Era to Tsahi.
    first_user_websocket_listener.emit_send_message(
        sender_username,
        f'{sender_username}&{second_receiver_username}',
        second_message,
        first_user_websocket_listener.current_auth_token)

    time.sleep(7)

    stop_all_listeners([first_user_websocket_listener, second_user_websocket_listener, third_user_websocket_listener])

    print("Extracting content")

    result ={first_receiver_username: second_user_websocket_listener.list_recorder_messages(),
             second_receiver_username: third_user_websocket_listener.list_recorder_messages()}

    print(result)
    return result


@pytest.fixture(scope="class")
def send_messages_to_one_user_out_of_two(request):
    """
       ..


    :param request:
    :return:
    """

    test_params = request.param[0]

    sender_username = test_params['sender_username']
    sender_password = test_params['sender_password']

    first_receiver_username = test_params['first_receiver_username']
    first_receiver_password = test_params['first_receiver_password']

    second_receiver_username = test_params['second_receiver_username']
    second_receiver_password = test_params['second_receiver_password']

    first_message, second_message = test_params['messages_content']

    # First user (sender) - log in and connect
    first_user_websocket_listener = Listener(sender_username)
    response = first_user_websocket_listener.send_log_in_request(sender_username, sender_password)

    logging.info(f"First user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = first_user_websocket_listener.initiate_connection()
    logging.info(f"First user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # # Waiting for  user status to change (so he/she will be ONLINE when the message is sent).
    time.sleep(3)

    # Second user (receiver) - log in and connect
    second_user_websocket_listener = Listener(first_receiver_username)
    response = second_user_websocket_listener.send_log_in_request(first_receiver_username, first_receiver_password)

    logging.info(f"Second user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = second_user_websocket_listener.initiate_connection()
    logging.info(
        f"Second user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # Third user (receiver) - log in and connect
    third_user_websocket_listener = Listener(second_receiver_username)
    response = third_user_websocket_listener.send_log_in_request(second_receiver_username, second_receiver_password)

    logging.info(f"Third user - sending log in request, server responds: {response}")
    assert response['result'] == 'success', logging.error("User sign in failed!")

    response = third_user_websocket_listener.initiate_connection()
    logging.info(
        f"Third user - sending the 'JOIN' event, trying to connect to Chat Server websocket: {response}")

    # Waiting for  user status to change (so he/she will be ONLINE when the message is sent).
    time.sleep(5)

    # Starting listening loop in a separate thread
    listening_thread_first = threading.Thread(target=second_user_websocket_listener.start_listening_loop)
    listening_thread_first.start()
    listening_thread_first.join(timeout=6)

    # Starting listening loop in a separate thread
    listening_thread_second = threading.Thread(target=third_user_websocket_listener.start_listening_loop)
    listening_thread_second.start()
    listening_thread_second.join(timeout=6)

    # Verifying both SENDER and BOTH RECEIVERS are ONLINE when the test is performed
    response = first_user_websocket_listener.send_get_admin_info_request(admin_username, admin_password)
    data = json.loads(response.content)
    users_online = data['online_clients_list']

    assert sender_username in users_online, logging.error(f"Sender {sender_username} not online")
    assert first_receiver_username in users_online, logging.error(f"Receiver {first_receiver_username} not online")
    assert second_receiver_username in users_online, logging.error(f"Receiver {second_receiver_password} not online")

    # Sending the first message as Era to Lisa.
    first_user_websocket_listener.emit_send_message(
        sender_username,
        f'{sender_username}&{first_receiver_username}',
        first_message,
        first_user_websocket_listener.current_auth_token)


    time.sleep(7)

    stop_all_listeners([first_user_websocket_listener, second_user_websocket_listener, third_user_websocket_listener])

    print("Extracting content")

    result ={first_receiver_username: second_user_websocket_listener.list_recorder_messages(),
             second_receiver_username: third_user_websocket_listener.list_recorder_messages()}

    print(result)
    return result



if __name__ == "__main__":
    send_single_message()
