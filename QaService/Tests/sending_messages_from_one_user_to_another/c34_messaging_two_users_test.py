from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

first_receiver_username = BaseConfig.RECEIVER_USERNAME
first_receiver_password = BaseConfig.RECEIVER_PASSWORD

second_receiver_username = BaseConfig.SECOND_RECEIVER_NAME
second_receiver_password = BaseConfig.SECOND_RECEIVER_PASSWORD

test_messages = ['first_message: Hi, Lisa!', 'second_message: Hi, Tsahi!']

test_id = 34
test_file_name = os.path.basename(__file__)


@pytest.mark.sending_messages
@pytest.mark.end2end
class TestMessaging:

    messages_received = None

    @pytest.mark.parametrize('send_messages_to_different_users', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "first_receiver_username": first_receiver_username,
                                                       "first_receiver_password": first_receiver_password,
                                                       "second_receiver_username": second_receiver_username,
                                                       "second_receiver_password": second_receiver_password,
                                                       "messages_content": test_messages}]],
                                                       indirect=True)
    def test_messages_sent_first_receiver(self, send_messages_to_different_users):

        try:
            TestMessaging.messages_received = send_messages_to_different_users

            messages_received_first_receiver = TestMessaging.messages_received[first_receiver_username]
            assert len(messages_received_first_receiver) == 1, \
                logging.error("QA Automation: Expecting for a ONE message")

            logging.info(f"QA Automation: messages received by the first user: {messages_received_first_receiver}")

            message = messages_received_first_receiver[0]
            assert message['sender'] == sender_username, logging.error("QA Automation: Incorrect message sender")
            assert message['content'] == test_messages[0], logging.error("QA Automation: Incorrect message content")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Step Passed: Verifying messages received by the first user -----"
                     f"-----------------------------\n")

    def test_messages_sent_second_receiver(self):

        try:
            messages_received_second_receiver = TestMessaging.messages_received[second_receiver_username]
            assert len(messages_received_second_receiver) == 1, \
                logging.error("QA Automation: Expecting for a ONE message")

            logging.info(f"QA Automation: messages received by the second user: {messages_received_second_receiver}")

            message = messages_received_second_receiver[0]
            assert message['sender'] == sender_username, logging.error("QA Automation: Incorrect message sender")
            assert message['content'] == test_messages[1], logging.error("QA Automation: Incorrect message content")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")