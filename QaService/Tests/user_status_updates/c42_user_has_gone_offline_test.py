from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_duration_seconds = 10


test_id = 42
test_file_name = os.path.basename(__file__)


@pytest.mark.sanity
@pytest.mark.status_updates
class TestStatusUpdates:
    """
    In this this test we verify, that all clients receive status update event via web socket
    once user terminates the connection ('user_has_gone_offline' event that contains the username of the disconnected user).

    Two users needed for this test - the SENDER and the RECEIVER.
    Both are connected.
    While the RECEIVER is connected and listening to new events in a separate thread
    the SENDER terminates the connection and his status is changed to 'offline'.

    The RECEIVER is expected to get the 'user_has_gone_offline' event (which should be published by the Chat Server)
    with the SENDER'S username.

    1. Verifying status change events were received.
    2. Verifying the event 'user_has_gone_offline' with SENDER'S username reached the RECEIVER
    """

    second_listener_events = None


    @pytest.mark.parametrize('status_change_events_has_gone_offline', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password
                                                       }]],
                                                       indirect=True)
    def test_status_update_published_received(self, status_change_events_has_gone_offline):

        try:
            # Both listeners are logged in, the RECEIVER is connected
            sender_listener, receiver_listener = status_change_events_has_gone_offline

            # The RECEIVER listener is set to listen to incoming events and status updates in a separate thread
            listen_for_events(receiver_listener, test_duration_seconds)

            # The SENDER listener TERMINATES the connection (while the RECEIVER is listening for new status updates)
            time.sleep(int(test_duration_seconds/2))
            sender_listener.terminate_connection()
            time.sleep(int(test_duration_seconds/2))

            # The RECEIVER ends the listening cycle, all received status updates are extracted
            TestStatusUpdates.second_listener_events = receiver_listener.list_recorded_status_updates()
            stop_all_listeners([receiver_listener])

            logging.info(TestStatusUpdates.second_listener_events)

            # We are to verify, that at least TWO status update events were received
            assert len(TestStatusUpdates.second_listener_events) > 1, \
                logging.error(f"Status update events weren't received")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            stop_all_listeners([sender_listener, receiver_listener])
            raise e

        logging.info(f"----------------------- Step Passed: Status Update events were published -----"
                     f"-----------------------------\n")

    def test_status_update_events_content_verified(self):

        try:

            relevant_status_update_events = []

            # Verifying 'new_user_online' event was emitted, notifying that the SENDER is online
            for event in TestStatusUpdates.second_listener_events:
                if 'user_has_gone_offline' in event.keys():
                    if 'username' in event['user_has_gone_offline'].keys():
                        if event['user_has_gone_offline']['username'] == sender_username:
                            relevant_status_update_events.append(event)

            logging.info(relevant_status_update_events)

            assert len(relevant_status_update_events) >= 1,  logging.error(f"QA Automation: 'user_has_gone_offline' event "
                                                                          f"wasn't published for {sender_username}")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            raise e

        logging.info(f"----------------------- Test Passed: {test_id} : {test_file_name} ---------------------"
                     f"-------------\n")