from QaService.Tests.conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

test_id = 21
test_file_name = os.path.basename(__file__)


@pytest.mark.server_data_provided
class TestServerDataReceived:
    """
    This test comes to verify, that Chat Server provides the Contacts List to client upon request.
    It is also verified, that all test users are on that list (those are the default users).

    1. Verifying Chat Server provides server data to client upon request
    2. Verifying the provided contacts list - all test users must be on it.
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

            assert 'all_existing_contacts' in TestServerDataReceived.server_data, \
                logging.error("QA Automation: Contacts List is missing in server data!")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(
            f"----------------------- Step Passed: verifying Chat Server provides server data to client upon request"
            f" ----------------------------------\n")

    def test_verifying_contacts_list(self):

        try:
           for user in test_users_list:
               assert user in TestServerDataReceived.server_data['all_existing_contacts'], \
                   logging.error(f"QA Automation: user is missing: {user}")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")



