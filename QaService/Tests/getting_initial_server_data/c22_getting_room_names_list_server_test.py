from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

test_id = 22
test_file_name = os.path.basename(__file__)


@pytest.mark.server_data_provided
@pytest.mark.regression
class TestServerDataReceived:
    """
    This test comes to verify, that the data received from Chat Server contains valid room names required for client.
    A room name must be generated for each contact, the username of the current user must be part of each
    room name that was provided to the client.

    1. Verifying Chat Server provides server data to client upon request
    2. Validating room names.
    """

    test_listener = Listener(sender_username)
    server_data = None

    @pytest.mark.incremental
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

            assert 'contacts' in TestServerDataReceived.server_data, \
                logging.error("QA Automation: Contacts List is missing in server data!")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e, test_file_name)
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e, test_file_name)
            raise e

        logging.info(
            f"----------------------- Step Passed: verifying Chat Server provides server data to client upon request"
            f" ----------------------------------\n")

    @pytest.mark.incremental
    def test_verifying_room_names_list(self):

        try:
           rooms_data = TestServerDataReceived.server_data['contacts']
           room_names_list_from_server = list(rooms_data.keys())
           logging.info(room_names_list_from_server)

           for user in test_users_list:
               if user != sender_username:
                   assert user in room_names_list_from_server, \
                       logging.error(f"QA Automation: room for user {user} is missing!")

                   room_name = rooms_data[user]
                   assert sender_username in room_name, logging.error(f"QA Automation: invalid room name: {room_name}")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e, test_file_name)
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e, test_file_name)
            raise e

        ResultsReporter.report_success(test_id, test_file_name)

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")



