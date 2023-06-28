from QaService.Tests.conftest import *


sender_username = "Era"
sender_password = "Come on"

receiver_username = "Lisa"
receiver_password = "TestMe"

test_message = 'Test_Auto_Send'

test_id = 31
test_file_name = os.path.basename(__file__)



class TestMessaging:


    @pytest.mark.parametrize('send_single_message', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password,
                                                       "message_content": test_message}]],
                                                       indirect=True)
    def test_single_message_sent_and_received(self, send_single_message):

        try:
            # Checking the messages that were received by the 'receiver' (currently Lisa)  -
            # verifying message sender (Era) and message content against expected.
            messages_forwarded_to_receiver = send_single_message

            assert len(messages_forwarded_to_receiver) == 1, logging.error("QA Automation: Expecting for a ONE message")

            message = messages_forwarded_to_receiver[0]
            assert message['sender'] == sender_username
            assert message['content'] == test_message

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")