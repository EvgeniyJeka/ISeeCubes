from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD
keep_alive_time_frame = BaseConfig.KEEP_ALIVE_DELAY_BETWEEN_EVENTS

test_id = 52
test_file_name = os.path.basename(__file__)


@pytest.mark.sanity
@pytest.mark.keep_alive_signals
class TestKeepAliveSignal:
    """
    This test comes to verify, that client isn't disconnected by Chat Server while he is sending
    the 'keep alive' signal in a required frequency (every 8 seconds by default config).

    1. User logs in and connects - verifying he was added to the 'online users' list
    2. User sends the 'keep alive' signal in time - verifying the connection is intact and the user is
       on "online users" list.

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

    def test_signal_sent(self):

        try:

            time.sleep(int(keep_alive_time_frame))

            # Sending keep alive signal to keep the connection intact
            TestKeepAliveSignal.test_listener.emit_keep_alive()

            time.sleep(int(keep_alive_time_frame) - 1)

            # Verifying client is still online
            connected_users = TestKeepAliveSignal.test_listener.send_get_admin_info_request(admin_username,
                                                                                            admin_password)
            online_users = json.loads(connected_users.content)['online_clients_list']
            logging.info(online_users)

            assert sender_username in online_users, \
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