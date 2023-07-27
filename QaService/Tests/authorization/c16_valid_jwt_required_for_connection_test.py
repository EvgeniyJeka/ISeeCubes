from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_duration_seconds = 15
first_message, second_message = "first message", "second_message"


test_id = 16
test_file_name = os.path.basename(__file__)


@pytest.mark.authorization
@pytest.mark.regression
class TestAuthorization:
    """
    This test comes to verify, that user can establish a connection ONLY with a valid authorization token
    that was created after a successful log in.

    In the first test step the users logs in and connects with a valid token. An Admin 'get_info'
    request is used to get the list of all users that are currently online, and it is verified,
    that the test user has the 'online' status.

    In the second test step the connection is terminated, the user logs in and tries to reconnect
    with an INVALID JWT. This attempt is expected to fail, and we verify that test user is NOT
    on the list of the online users.

    In Chat Server logs the following record is added:

    INFO:root:Received a request for contacts, username: 'Era', JWT: %Invalid Token%
    ERROR:root:Invalid JWT: %Invalid Token%

    1. Logging in and establishing a connection with a valid JWT
    2. Terminating the connection. Logging in and establishing a connection with an INVALID JWT.
    """

    sender_listener = None
    receiver_listener = None

    @pytest.mark.incremental
    @pytest.mark.parametrize('status_change_events_user_goes_online', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password
                                                       }]],
                                                       indirect=True)
    def test_initiating_connection_valid_token(self, status_change_events_user_goes_online):

        try:
            # Both listeners are logged in, the RECEIVER is connected
            TestAuthorization.sender_listener, TestAuthorization.receiver_listener = status_change_events_user_goes_online

            # The SENDER listener initiates a connection
            TestAuthorization.sender_listener.initiate_connection()
            time.sleep(int(test_duration_seconds / 3))

            connected_users = TestAuthorization.sender_listener.send_get_admin_info_request(admin_username, admin_password)
            online_users = json.loads(connected_users.content)['online_clients_list']
            logging.info(online_users)

            assert sender_username in online_users, \
                logging.error(f"QA Automation: user {sender_username} has failed to "
                              f"initiate a connection with a valid JWT!")

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

        logging.info(f"----------------------- Step Passed: Logging in and establishing a connection with a valid JWT"
                     f" ----------------------------------\n")

    @pytest.mark.incremental
    def test_initiating_connection_invalid_token(self):

        try:

            # Terminating the connection that was previously established
            TestAuthorization.sender_listener.terminate_connection()
            time.sleep(int(test_duration_seconds / 3))

            # Trying to establish a new connection - this time with an INVALID JWT
            TestAuthorization.sender_listener.send_log_in_request(sender_username, sender_password)
            TestAuthorization.sender_listener.current_auth_token = "%Invalid Token%"
            TestAuthorization.sender_listener.initiate_connection()

            # Verifying the connection wasn't established and the user isn't in 'online users' list
            time.sleep(int(test_duration_seconds / 3))

            connected_users = TestAuthorization.sender_listener.send_get_admin_info_request(admin_username,
                                                                                            admin_password)
            online_users = json.loads(connected_users.content)['online_clients_list']
            logging.info(online_users)

            assert sender_username not in online_users

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

        ResultsReporter.report_success(test_id, test_file_name)

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")



