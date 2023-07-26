from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_message = 'Test_Auto_Send'

test_id = 35
test_file_name = os.path.basename(__file__)


@pytest.mark.sanity
@pytest.mark.sending_messages
@pytest.mark.end2end
class TestMessaging:
    """
    In this test we verify, that a message that was sent to a user while he was offline is cached
    and forwarded to the user once he is online. Message content is verified (should be unmodified).

    In test preconditions the sender logs in (a 'Listener' instance is initiated),
    the message is sent while the receiver is offline. The message is expected to be cached
    on the server side. Once the receiver logs in (it happens AFTER the message was sent)
    he is expected to the message that was cached for him.

     1. Verifying the message sent by the first user (the sender)  while the second user was offline
        is cached and forwarded to the second user (the receiver) once he connects to the Chat Server.

    """

    @pytest.mark.parametrize('messaging_offline_user', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password,
                                                       "message_content": test_message}]],
                                                       indirect=True)
    def test_message_extracted_from_cache(self, messaging_offline_user):
        try:
            # Checking the messages that were received by the 'receiver' (currently Lisa)  -
            # verifying message sender (Era) and message content against expected.
            messages_forwarded_to_receiver = messaging_offline_user

            assert len(messages_forwarded_to_receiver) == 1, logging.error("QA Automation: Expecting for a ONE message")

            message = messages_forwarded_to_receiver[0]
            assert message['sender'] == sender_username
            assert message['content'] == test_message

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