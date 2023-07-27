from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_messages = ['first_message', 'second_message']

test_id = 35.1
test_file_name = os.path.basename(__file__)


@pytest.mark.sending_messages
@pytest.mark.end2end
@pytest.mark.regression
class TestMessaging:
    """
    This test comes to verify, that message caching mechanism doesn't disrupt
    the normal message delivering flow.
    Two messages are send to the receiver - one is sent when he is offline (and cached), one is sent when
    he is online (the sender and the receiver are both online).
    It is expected, that the receiver will get both messages in the right order - the message that was cached
    will come first.
    """

    messages_forwarded_to_receiver = None

    @pytest.mark.incremental
    @pytest.mark.parametrize('messaging_user_offline_online', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password,
                                                       "messages_content": test_messages}]],
                                                       indirect=True)
    def test_verifying_cached_message_forwarded(self, messaging_user_offline_online):

        try:
            # Checking the messages that were received by the 'receiver' (currently Lisa)  -
            # verifying message sender (Era) and message content against expected.
            TestMessaging.messages_forwarded_to_receiver = messaging_user_offline_online
            assert len(TestMessaging.messages_forwarded_to_receiver) == 2, logging.error("QA Automation: Expecting for a TWO messages")

            messages_content = []

            for message in TestMessaging.messages_forwarded_to_receiver:
                assert message['sender'] == sender_username, \
                    logging.error('QA Automation: Message sender username is incorrect')

                messages_content.append(message['content'])

            assert test_messages[0] in messages_content, logging.error('QA Automation: First message is missing')
            # assert test_messages[1] in messages_content, logging.error('QA Automation: Second message is missing')

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            ResultsReporter.report_failure(test_id, e, test_file_name)
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            ResultsReporter.report_broken_test(test_id, e, test_file_name)
            raise e

        logging.info(f"----------------------- Step Passed: Message that was cached in Redis is forwarded to the "
                     f"receiver once he is online ----------------------------------\n")

    @pytest.mark.incremental
    def test_verifying_second_message_forwarded(self):

        try:

            assert test_messages[1] == TestMessaging.messages_forwarded_to_receiver[1]["content"], \
                logging.error('QA Automation: First message is missing')

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