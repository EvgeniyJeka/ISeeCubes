from ..conftest import *


sender_username = "Era"
sender_password = "Come on"

first_receiver_username = "Lisa"
first_receiver_password = "TestMe"

second_receiver_username = "Tsahi"
second_receiver_password = "Virtual Environment"

test_messages = ['first_message: Hi, Lisa!', 'second_message: Hi, Tsahi!']

test_id = 33
test_file_name = os.path.basename(__file__)


class TestMessaging:
    """
    This test comes to verify, that a message that was sent to from one user to another
    isn't transmitted to all other users - in other words, peer-to-peer communication
    is private.

    For that purpose three users are connected - Era, Lisa and Tsahi.
    Three 'Listener' instances are initiated and running in a listening loop.

    Era sends a message to Lisa. First step verifies, that Lisa receives that message, and the second
    step verifies that Tsahi doesn't.

    1. Verifying the message is forwarded to the receiver
    2. Verifying the message is NOT transmitted to other users.
    """

    messages_received = None

    @pytest.mark.parametrize('send_messages_to_one_user_out_of_two', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "first_receiver_username": first_receiver_username,
                                                       "first_receiver_password": first_receiver_password,
                                                       "second_receiver_username": second_receiver_username,
                                                       "second_receiver_password": second_receiver_password,
                                                       "messages_content": test_messages}]],
                                                       indirect=True)
    def test_messages_sent_first_receiver(self, send_messages_to_one_user_out_of_two):

        try:
            TestMessaging.messages_received = send_messages_to_one_user_out_of_two

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

    def test_no_messages_sent_second_receiver(self):

        try:
            messages_received_second_receiver = TestMessaging.messages_received[second_receiver_username]
            assert len(messages_received_second_receiver) == 0, \
                logging.critical("QA Automation: Message must be sent ONLY to the selected user")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")