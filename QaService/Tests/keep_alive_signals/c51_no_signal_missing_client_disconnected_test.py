from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD
keep_alive_time_frame = BaseConfig.KEEP_ALIVE_DELAY_BETWEEN_EVENTS

test_id = 51
test_file_name = os.path.basename(__file__)


@pytest.mark.sanity
@pytest.mark.keep_alive_signals
class TestKeepAliveSignal:
    """
    This test comes to verify that a connection is automatically terminated by Chat Server if
    client doesn't send the 'keep alive' signal in time (every 8 seconds by default configuration).

    Test user logs in, connects. Since no 'keep alive' signal is sent, the user is considered as disconnected
    by Chat Server.

    1. User logs in and connects - verifying he was added to the 'online users' list
    2. User doesn't send the 'keep alive' signal in time - verifying the connection is terminated and the
       user is removed from the 'online users' list.
    """

    test_listener = Listener(sender_username)

    def test_sign_in_connect(self):

        try:
            response = TestKeepAliveSignal.test_listener.send_log_in_request(sender_username, sender_password,
                                                                           return_full_response=True)

            logging.info(response)

            assert 'result' in response, logging.error(f"QA Automation: Invalid response to log in request, "
                                                       f"creds: {sender_username}, {sender_password}")

            TestKeepAliveSignal.test_listener.initiate_connection()

            time.sleep(4)

            connected_users = TestKeepAliveSignal.test_listener.send_get_admin_info_request(admin_username,
                                                                                            admin_password)
            online_users = json.loads(connected_users.content)['online_clients_list']
            logging.info(online_users)

            assert sender_username in online_users, \
                logging.error(f"QA Automation: user {sender_username} isn't on 'online users' list!")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            TestKeepAliveSignal.test_listener.terminate_connection()
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            TestKeepAliveSignal.test_listener.terminate_connection()
            raise e

        logging.info(f"----------------------- Step Passed: User logs in and connects - verifying he was added to the 'online users' list"
                     f" ----------------------------------\n")

    def test_no_signal_connection_terminated(self):

        try:
            # Waiting for the connection to expire without sending 'keep alive' signal
            time.sleep(int(keep_alive_time_frame) * 2)

            # Test user is expected to be logged out by the server at this point.
            connected_users = TestKeepAliveSignal.test_listener.send_get_admin_info_request(admin_username,
                                                                                            admin_password)
            online_users = json.loads(connected_users.content)['online_clients_list']
            logging.info(online_users)

            assert sender_username not in online_users, \
                logging.error(f"QA Automation: user {sender_username} isn't on 'online users' list!")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        finally:
            TestKeepAliveSignal.test_listener.terminate_connection()

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")