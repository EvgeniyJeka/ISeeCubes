from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_message = 'Test_Auto_Send'

test_id = 36
test_file_name = os.path.basename(__file__)


@pytest.mark.sending_messages
@pytest.mark.end2end
@pytest.mark.regression
class TestMessaging:
    """
    In this test we verify, that messages can be sent after relogin.
    In preconditions the sender logs in, then logs out (and terminates the connection).
    It is validated, that the connection is terminated.

    Then the sender reconnects, and sends a message to the receiver.
    In the test we verify, that the message was received.

     1. Verifying the message sent by the first user AFTER RE LOGIN(the sender) is forwarded to the second user
        (the receiver).
    """

    @pytest.mark.parametrize('send_message_after_relogin', [[{"sender_username": sender_username,
                                                              "sender_password": sender_password,
                                                              "receiver_username": receiver_username,
                                                              "receiver_password": receiver_password,
                                                              "message_content": test_message}]],
                                                               indirect=True)
    def test_single_message_sent_and_received(self, send_message_after_relogin):
        try:
            # Checking the messages that were received by the 'receiver' (currently Lisa)  -
            # verifying message sender (Era) and message content against expected.
            messages_forwarded_to_receiver = send_message_after_relogin

            assert len(messages_forwarded_to_receiver) == 1, logging.error("QA Automation: Expecting for a ONE message")

            message = messages_forwarded_to_receiver[0]
            assert message['sender'] == sender_username
            assert message['content'] == test_message

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