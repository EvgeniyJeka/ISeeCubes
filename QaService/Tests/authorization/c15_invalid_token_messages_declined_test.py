
from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_duration_seconds = 10
first_message, second_message, third_message = "first message", "second_message", "third_message"

expected_error_message = f"Error! User '{sender_username}' must disconnect, re login and reconnect so the " \
    f"conversation can be resumed."


test_id = 15
test_file_name = os.path.basename(__file__)


@pytest.mark.authorization
@pytest.mark.regression
class TestAuthorization:
    """
    This test comes to verify, that messages with an invalid or blank JWT will be declined.
    Valid JWT must be attached to EACH message.
    The first user, the Sender, sends three messages (while the Receiver is listening in a separate thread):
    - First message with valid JWT
    - Second message with invalid JWT
    - Third message with blank JWT

    Only the FIRST message is expected to be forwarded to the receiver.

    1. Emitting a WS message with valid JWT
    2. Emitting a WS message with invalid JWT
    3. Emitting a WS message with blank JWT
    4. Verifying ONLY the first message was forwarded to the receiver

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
    def test_sending_messages_valid_token(self, status_change_events_user_goes_online):

        try:
            # time.sleep(10)
            # Both listeners are logged in, the RECEIVER is connected
            TestAuthorization.sender_listener, TestAuthorization.receiver_listener = status_change_events_user_goes_online

            # The RECEIVER listener is set to listen to incoming events and status updates in a separate thread
            listen_for_events(TestAuthorization.receiver_listener, test_duration_seconds)

            # The SENDER listener initiates a connection (while the RECEIVER is listening for new status updates)
            time.sleep(int(test_duration_seconds / 4))
            # TestAuthorization.sender_listener.sio.disconnect()
            # time.sleep(3)
            TestAuthorization.sender_listener.initiate_connection()

            # Sending a message with a valid JWT (before sign out)
            TestAuthorization.sender_listener.emit_send_message(
                sender_username,
                f'{sender_username}&{receiver_username}',
                first_message,
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

        logging.info(f"----------------------- Step Passed: Emitting a WS message with valid JWT"
                     f" ----------------------------------\n")

    @pytest.mark.incremental
    def test_sending_messages_invalid_token(self):

        try:
            # Sending a message with INVALID JWT
            TestAuthorization.sender_listener.current_auth_token = "%invalid token%"

            TestAuthorization.sender_listener.emit_send_message(
                sender_username,
                f'{sender_username}&{receiver_username}',
                first_message,
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

        logging.info(f"----------------------- Step Passed: Emitting a WS message with invalid JWT"
                     f" ----------------------------------\n")

    @pytest.mark.incremental
    def test_sending_messages_blank_token(self):

        try:
            # Sending a message with INVALID JWT
            TestAuthorization.sender_listener.current_auth_token = ""

            TestAuthorization.sender_listener.emit_send_message(
                sender_username,
                f'{sender_username}&{receiver_username}',
                first_message,
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

        logging.info(
            f"----------------------- Step Passed: Emitting a WS message with blank JWT"
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
            stop_all_listeners([TestAuthorization.sender_listener, TestAuthorization.receiver_listener])
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e, test_file_name)
            raise e

        except Exception as e:
            stop_all_listeners([TestAuthorization.sender_listener, TestAuthorization.receiver_listener])
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e, test_file_name)
            raise e

        finally:
            TestAuthorization.sender_listener = None
            TestAuthorization.receiver_listener = None

        ResultsReporter.report_success(test_id, test_file_name)

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")