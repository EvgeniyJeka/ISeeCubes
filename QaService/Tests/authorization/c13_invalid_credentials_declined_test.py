from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_id = 13
test_file_name = os.path.basename(__file__)


class TestAuthorization:
    """
    This test comes to verify, that invalid log in request will be declined by the Chat Server.

    1. Verifying log in request with no username is declined.
    2. Verifying log in request with no password is declined.
    3. Verifying log in request with no username and no password is declined.
    4. Verifying log in request with invalid (non existing) username is declined.
    5. Verifying log in request is declined when there is a mismatch between username and password
    """

    test_listener = Listener(sender_username)

    def test_sign_in_no_username(self):

        try:
            response = TestAuthorization.test_listener.send_log_in_request(None, sender_password,
                                                                           return_full_response=True)

            logging.info(response)

            assert response['result'] == 'Invalid credentials'


        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Step Passed: Verifying log in request with no username is declined -----"
                     f"-----------------------------\n")

    def test_sign_in_no_password(self):

        try:
            response = TestAuthorization.test_listener.send_log_in_request(sender_username, None,
                                                                           return_full_response=True)

            logging.info(response)

            assert response['result'] == 'server error'


        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Step Passed: Verifying log in request with no password is declined. -----"
                     f"-----------------------------\n")

    def test_sign_in_no_username_no_password(self):

        try:
            response = TestAuthorization.test_listener.send_log_in_request(None, None,
                                                                           return_full_response=True)

            logging.info(response)

            assert response['result'] == 'Invalid credentials'


        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(
            f"----------------------- Step Passed: Verifying log in request with no username and no password is declined. -----"
            f"-----------------------------\n")

    def test_sign_in_invalid_username(self):

        try:
            response = TestAuthorization.test_listener.send_log_in_request(sender_username + "X", sender_password,
                                                                           return_full_response=True)

            logging.info(response)

            assert response['result'] == 'Invalid credentials'


        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(
            f"----------------------- Step Passed: Verifying log in request with invalid (non existing) username is declined. -----"
            f"-----------------------------\n")

    def test_sign_in_other_user_password(self):

        try:
            response = TestAuthorization.test_listener.send_log_in_request(sender_username, receiver_password,
                                                                           return_full_response=True)

            logging.info(response)

            assert response['result'] == 'Invalid credentials'


        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")