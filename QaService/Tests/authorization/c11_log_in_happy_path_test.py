from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

test_id = 11
test_file_name = os.path.basename(__file__)


@pytest.mark.sanity
@pytest.mark.authorization
class TestAuthorization:
    """
    In this test we verify user gets a valid JWT in response to log in request, if the former contains
    valid credentials.
    JWT is validated by sending 'get_contacts_list' request to the Chat Server - the server will provide
    a response that contains a contact list only if the JWT is valid.

    1. Verifying the response to log in request contains a confirmation and a JWT.
    2. Verifying the provided JWT is valid.
    """

    test_listener = Listener(sender_username)

    @pytest.mark.incremental
    def test_sign_in_performed(self):

        try:
            response = TestAuthorization.test_listener.send_log_in_request(sender_username, sender_password,
                                                                           return_full_response=True)

            logging.info(response)

            assert 'result' in response, logging.error(f"QA Automation: Invalid response to log in request, "
                                                       f"creds: {sender_username}, {sender_password}")

            assert 'token' in response, logging.error(f"QA Automation: Invalid response to log in request, "
                                                       f"creds: {sender_username}, {sender_password}")

            assert len(response['token']) > 1, logging.error("QA Automation: Invalid JWT provided.")
            assert response['result'] == 'success'

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e)
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e)
            raise e

        logging.info(f"----------------------- Step Passed: Log In request with valid credentials is responded with JWT"
                     f" ----------------------------------\n")

    @pytest.mark.incremental
    def test_verifying_jwt(self):

        try:
            response = TestAuthorization.test_listener.send_request_for_contacts()

            assert response.status_code == 200, logging.error("QA Automation: invalid JWT is provided on log in")
            parsed_response = json.loads(response.content)

            assert 'all_existing_contacts' in parsed_response
            assert 'contacts' in parsed_response
            assert 'currently_online' in parsed_response

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e)
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e)
            raise e

        ResultsReporter.report_success(test_id)

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")
