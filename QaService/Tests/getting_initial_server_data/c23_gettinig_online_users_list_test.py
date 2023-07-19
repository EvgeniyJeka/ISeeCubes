from QaService.Tests.conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

test_id = 23
test_file_name = os.path.basename(__file__)


@pytest.mark.server_data_provided
class TestServerDataReceived:
    """
    This test comes to verify, that the data received from Chat Server contains a list of users that are
    online at the moment, and that list is updated when a user goes offline.

    Test user connects and gets the initial data. Since the test user is connected, his name should be
    on the "online users" list.

    After we verify that the connection is terminated, and the request for server data is sent again.
    This time it is expected that the username of the test user will be removed from the list.

    1. Verifying Chat Server provides server data to client upon request
    2. Test user is online - verifying he is on the list
    3. Test user is offline - verifying he was removed from the list
    """

    test_listener = Listener(sender_username)
    server_data = None

    def test_getting_initial_data(self):

        try:
            response = TestServerDataReceived.test_listener.send_log_in_request(sender_username, sender_password,
                                                                           return_full_response=True)
            logging.info(response)

            assert 'result' in response, logging.error(f"QA Automation: Invalid response to log in request, "
                                                       f"creds: {sender_username}, {sender_password}")

            response = TestServerDataReceived.test_listener.send_request_for_contacts()
            TestServerDataReceived.server_data = json.loads(response.content)
            logging.info(TestServerDataReceived.server_data)

            assert 'currently_online' in TestServerDataReceived.server_data, \
                logging.error("QA Automation: Online Users List is missing in server data!")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(
            f"----------------------- Step Passed: verifying Chat Server provides server data to client upon request"
            f" ----------------------------------\n")

    def test_getting_online_users_test_user_online(self):

        try:
            TestServerDataReceived.test_listener.initiate_connection()
            time.sleep(4)

            response = TestServerDataReceived.test_listener.send_request_for_contacts()
            TestServerDataReceived.server_data = json.loads(response.content)
            logging.info(TestServerDataReceived.server_data)

            online_users = TestServerDataReceived.server_data['currently_online']
            assert sender_username in online_users

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        finally:
            TestServerDataReceived.test_listener.terminate_connection()

        logging.info(
            f"----------------------- Step Passed: Test user is online - verifying he is on the list"
            f" ----------------------------------\n")

    def test_getting_online_users_test_user_offline(self):

        try:
            time.sleep(4)
            response = TestServerDataReceived.test_listener.send_log_in_request(sender_username, sender_password,
                                                                                return_full_response=True)

            logging.info(response)

            assert 'result' in response, logging.error(f"QA Automation: Invalid response to log in request, "
                                                       f"creds: {sender_username}, {sender_password}")

            response = TestServerDataReceived.test_listener.send_request_for_contacts()
            TestServerDataReceived.server_data = json.loads(response.content)
            logging.info(TestServerDataReceived.server_data)

            online_users = TestServerDataReceived.server_data['currently_online']
            assert sender_username not in online_users, \
                logging.error(f"QA Automation: test user {sender_username} wasn't removed from the "
                              f"'online users' list after disconnection!")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")

