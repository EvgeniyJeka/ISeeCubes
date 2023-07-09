from ..conftest import *


sender_username = "Era"
sender_password = "Come on"

receiver_username = "Lisa"
receiver_password = "TestMe"

test_message = 'Test_Auto_Send'

test_id = 37
test_file_name = os.path.basename(__file__)


class TestMessaging:
    """
    This test comes to verify, that a message that was sent to non-existing user
    doesn't disrupt the workflow of the Chat Server (negative test).
    For that purpose TWO messages are sent - the first message is sent to NON EXISTING user,
    and the second message to a valid user. The test verifies, that the second message
    is received, meaning - the system works as expected AFTER receiving an invalid message
    to non existing user.

    In Chat Server logs the following line will be printed:
    ERROR:root:Trying to send a message to non-existing user.

    NOTE: The native client allows to send messages only to user from a contact list,
    but it is assumed that third party client that connects to the Chat Server might
    publish an invalid message..

    1. Verifying the message sent by the first user (the sender) is forwarded to the second user (the receiver)
       providing both users are online.
    """

    @pytest.mark.parametrize('messaging_non_existing_user', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password,
                                                       "message_content": test_message}]],
                                                       indirect=True)
    def test_single_message_sent_and_received(self, messaging_non_existing_user):

        try:
            # Checking the messages that were received by the 'receiver' (currently Lisa)  -
            # verifying message sender (Era) and message content against expected.
            messages_forwarded_to_receiver = messaging_non_existing_user

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