from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_duration_seconds = 15
first_message, second_message = "first message", "second_message"


test_id = 17
test_file_name = os.path.basename(__file__)


@pytest.mark.authorization
class TestAuthorization:
    """
    This test comes to verify, that server data can be acquired only if the request sent from client to Chat Server
    contains a valid JWT.

    1. Verifying server data is provided when the request for server data contains valid JWT
    2. Verifying server data isn't provided when the request for server data contains invalid JWT

    """

    sender_listener = None
    receiver_listener = None

    @pytest.mark.parametrize('status_change_events_user_goes_online', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password
                                                       }]],
                                                       indirect=True)
    def test_getting_server_data_valid_token(self, status_change_events_user_goes_online):

        try:
            # Both listeners are logged in, the RECEIVER is connected
            TestAuthorization.sender_listener, TestAuthorization.receiver_listener = status_change_events_user_goes_online

            response = TestAuthorization.sender_listener.send_request_for_contacts()
            server_data = json.loads(response.content)
            logging.info(server_data)

            assert 'all_existing_contacts' in server_data.keys()
            assert sender_username in server_data['all_existing_contacts']
            assert 'contacts' in server_data.keys()
            assert 'currently_online' in server_data.keys()

        except AssertionError as e:
            stop_all_listeners([TestAuthorization.sender_listener, TestAuthorization.receiver_listener])
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            stop_all_listeners([TestAuthorization.sender_listener, TestAuthorization.receiver_listener])
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Step Passed: Logging in and establishing a connection with a valid JWT"
                     f" ----------------------------------\n")

    def test_server_data_invalid_token(self):

        try:
            # Using invalid JWT to prompt for server data
            TestAuthorization.sender_listener.current_auth_token = "% Invalid Token "

            response = TestAuthorization.sender_listener.send_request_for_contacts()
            server_data = json.loads(response.content)
            logging.info(server_data)

            assert 'error' in server_data.keys(), \
                logging.error("QA Automation: no error is response to invalid JWT!")
            assert server_data['error'] == 'Invalid JWT', \
                logging.error("QA Automation: no error is response to invalid JWT!")

            assert 'all_existing_contacts' not in server_data.keys()
            assert 'contacts' not in server_data.keys()
            assert 'currently_online' not in server_data.keys()

            TestAuthorization.sender_listener.sio.disconnect()
            TestAuthorization.receiver_listener.sio.disconnect()

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        finally:
            TestAuthorization.sender_listener.sio.disconnect()
            TestAuthorization.receiver_listener.sio.disconnect()

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")