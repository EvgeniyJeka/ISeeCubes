from QaService.Tests.conftest import *


sender_username = "Era"
sender_password = "Come on"

receiver_username = "Lisa"
receiver_password = "TestMe"

test_messages = ['first_message', 'second_message']

test_id = 32
test_file_name = os.path.basename(__file__)


class TestMessaging:

    @pytest.mark.parametrize('send_several_messages', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password,
                                                       "messages_content": test_messages}]],
                                                       indirect=True)
    def test_several_messages_sent_and_received(self, send_several_messages):

        try:
            # Checking the messages that were received by the 'receiver' (currently Lisa)  -
            # verifying message sender (Era) and message content against expected.
            messages_forwarded_to_receiver = send_several_messages
            assert len(messages_forwarded_to_receiver) == 2, logging.error("QA Automation: Expecting for a TWO messages")

            messages_content = []

            for message in messages_forwarded_to_receiver:
                assert message['sender'] == sender_username, \
                    logging.error('QA Automation: Message sender username is incorrect')

                messages_content.append(message['content'])

            assert test_messages[0] in messages_content, logging.error('QA Automation: First message is missing')
            assert test_messages[1] in messages_content, logging.error('QA Automation: Second message is missing')

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")