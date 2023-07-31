from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_duration_seconds = 10
first_message, second_message = "first message", "second_message"


test_id = 12
test_file_name = os.path.basename(__file__)


@pytest.mark.authorization
@pytest.mark.regression
class TestAuthorization:
    """
    This test comes to verify the SIGN OUT functionality.
    When user signs out, the connection to web socket is terminated and the JWT is expired
    (the record is modified on server side).
    In order to reconnect and message other users user must re login, so a new JWT will be created.

    In order to verify, that the 'sign out' functionality works properly one user, the Sender,
    sends to messages to the Receiver - one of them BEFORE the sign out and one of them AFTER
    (in this test we emulate the native client behaviour - WS connection is terminated and  'client_disconnection'
    event is emitted by the client). we expect the Receiver to get only the FIRST message (that was sent before
    sing out).

    1. Sending the first message, signing out, sending the second message
    2. Verifying ONLY the first message was received
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
    def test_sending_messages_before_after_sign_out(self, status_change_events_user_goes_online):

        try:
            # Both listeners are logged in, the RECEIVER is connected
            TestAuthorization.sender_listener, TestAuthorization.receiver_listener = status_change_events_user_goes_online

            # The RECEIVER listener is set to listen to incoming events and status updates in a separate thread
            listen_for_events(TestAuthorization.receiver_listener, test_duration_seconds)

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

            # Signing out
            TestAuthorization.sender_listener.terminate_connection()

            # Trying to reconnect with an EXPIRED token
            TestAuthorization.sender_listener.initiate_connection()

            # Sending a message with a expired JWT (after sign out)
            TestAuthorization.sender_listener.emit_send_message(
                sender_username,
                f'{sender_username}&{receiver_username}',
                second_message,

                TestAuthorization.sender_listener.current_auth_token)
            time.sleep(int(test_duration_seconds / 4))

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

        logging.info(f"----------------------- Step Passed: Sending the first message, signing out, sending the second message"
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

            TestAuthorization.receiver_listener.terminate_connection()

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

        ResultsReporter.report_success(test_id, test_file_name)

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")



