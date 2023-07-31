
from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_duration_seconds = 10
first_message, second_message = "first message", "second_message"

expected_error_message = f"Error! User '{sender_username}' must disconnect, re login and reconnect so the " \
    f"conversation can be resumed."


test_id = 14
test_file_name = os.path.basename(__file__)


@pytest.mark.authorization
@pytest.mark.regression
class TestAuthorization:
    """
    This test comes to verify, that messages are declined when the authorization token expires or blocked
    on the server side (meaning - removed from Redis DB in both cases).

    The first user, the Sender, sends two messages, and the JWT is terminated after the first one.
    The second user, the Receiver, is expected to get ONLY the first message. The second one is declined,
    AND an error message is automatically sent to the message sender (from chat Admin).

    1. Sending the first message, terminating the JWT on the server side, sending the second message
    2. Verifying ONLY the first message was forwarded to the Receiver
    3. Verifying relevant error message was sent by Admin to the Sender (expired/deleted JWT used)

    """

    second_listener_messages = None
    receiver_listener = None
    sender_listener = None

    @pytest.mark.incremental
    @pytest.mark.parametrize('status_change_events_user_goes_online', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password
                                                       }]],
                                                       indirect=True)
    def test_sending_messages_before_after_jwt_removal(self, status_change_events_user_goes_online):

        try:

            # Both listeners are logged in, the RECEIVER is connected
            TestAuthorization.sender_listener, TestAuthorization.receiver_listener = status_change_events_user_goes_online

            # The RECEIVER listener is set to listen to incoming events and status updates in a separate thread
            listen_for_events(TestAuthorization.receiver_listener, test_duration_seconds)

            listen_for_events(TestAuthorization.sender_listener, test_duration_seconds)

            # The SENDER listener initiates a connection (while the RECEIVER is listening for new status updates)
            time.sleep(int(test_duration_seconds / 4))

            TestAuthorization.sender_listener.initiate_connection()

            # Sending a message with a valid JWT (before sign out)
            TestAuthorization.sender_listener.emit_send_message(
                sender_username,
                f'{sender_username}&{receiver_username}',
                first_message,
                TestAuthorization.sender_listener.current_auth_token)
            time.sleep(int(test_duration_seconds / 4))

            # Deleting the Sender's JWT on server side (using special Admin request for test purposes)
            TestAuthorization.sender_listener.kill_token_admin_request(admin_username, admin_password, sender_username)

            # Trying to reconnect after the token was DELETED ON SERVER SIDE
            TestAuthorization.sender_listener.initiate_connection()

            # Sending a message with a expired JWT (after sign out)
            TestAuthorization.sender_listener.emit_send_message(
                sender_username,
                f'{sender_username}&{receiver_username}',
                second_message,

                TestAuthorization.sender_listener.current_auth_token)
            time.sleep(int(test_duration_seconds / 4))

        except AssertionError as e:
            stop_all_listeners([TestAuthorization.sender_listener, TestAuthorization.receiver_listener])
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e, test_file_name)
            raise e

        except Exception as e:
            stop_all_listeners([TestAuthorization.sender_listener, TestAuthorization.receiver_listener])
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e, test_file_name)
            raise e

        logging.info(f"----------------------- Step Passed: Sending the first message, terminating the JWT on the server side, sending the second message"
                     f" ----------------------------------\n")

    @pytest.mark.incremental
    def test_verifying_only_first_message_received(self):

        try:
            time.sleep(int(test_duration_seconds / 4))

            messages_received_by_second_user = TestAuthorization.receiver_listener.list_recorder_messages()
            logging.info(messages_received_by_second_user)

            assert len(messages_received_by_second_user) == 1
            assert messages_received_by_second_user[0]['sender'] == sender_username
            assert messages_received_by_second_user[0]['content'] == first_message

            stop_all_listeners([TestAuthorization.sender_listener, TestAuthorization.receiver_listener])

        except AssertionError as e:
            TestAuthorization.sender_listener.sio.disconnect()
            TestAuthorization.receiver_listener.sio.disconnect()
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e, test_file_name)
            raise e

        except Exception as e:
            TestAuthorization.sender_listener.sio.disconnect()
            TestAuthorization.receiver_listener.sio.disconnect()
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e, test_file_name)
            raise e

        logging.info(
            f"----------------------- Step Passed: Verifying ONLY the first message was forwarded to the Receiver"
            f" ----------------------------------\n")

    @pytest.mark.incremental
    def test_sender_receives_error_message(self):

        try:
            messages_received_by_sender = TestAuthorization.sender_listener.list_recorder_messages()
            logging.info(messages_received_by_sender)

            admin_messages = []

            for message in messages_received_by_sender:
                if message['sender'] == 'Admin':
                    admin_messages.append(message)

            assert len(admin_messages) == 1
            assert admin_messages[0]['content'] == expected_error_message

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e, test_file_name)
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e, test_file_name)
            raise e

        finally:
            TestAuthorization.sender_listener = None
            TestAuthorization.receiver_listener = None

        ResultsReporter.report_success(test_id, test_file_name)

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")






