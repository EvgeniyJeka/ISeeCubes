from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_message = 'Test_Auto_Send'

test_id = 31
test_file_name = os.path.basename(__file__)


@pytest.mark.sanity
@pytest.mark.sending_messages
@pytest.mark.end2end
class TestMessaging:
    """
    In this test we verify, that a chat message is forwarded to the selected contact.
    In test preconditions both the sender and the receiver log in (2 'Listener' instances are initiated),
    the message is sent while the receiver is listening in a separate thread.

    After the message is sent the connection is terminated and all received messages are verified
    in the test.

    1. Verifying the message sent by the first user (the sender) is forwarded to the second user (the receiver)
       providing both users are online.
    """

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