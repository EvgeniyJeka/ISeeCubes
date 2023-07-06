from QaService.Tests.conftest import *


sender_username = "Era"
sender_password = "Come on"

receiver_username = "Lisa"
receiver_password = "TestMe"

test_message = 'Test_Auto_Send'

test_id = 35
test_file_name = os.path.basename(__file__)


class TestMessaging:
    """
    In this test we verify, that a message that was sent to a user while he was offline is cached
    and forwarded to the user once he is online. Message content is verified (should be unmodified).
    """

    @pytest.mark.parametrize('messaging_offline_user', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password,
                                                       "message_content": test_message}]],
                                                       indirect=True)
    def test_message_extracted_from_cache(self, messaging_offline_user):
        pass
        # messages_forwarded_to_receiver = messaging_offline_user
        # print(messages_forwarded_to_receiver)