from ..conftest import *


sender_username = BaseConfig.SENDER_USERNAME
sender_password = BaseConfig.SENDER_PASSWORD

receiver_username = BaseConfig.RECEIVER_USERNAME
receiver_password = BaseConfig.RECEIVER_PASSWORD

test_duration_seconds = 10


test_id = 41
test_file_name = os.path.basename(__file__)


@pytest.mark.sanity
@pytest.mark.status_updates
@pytest.mark.regression
class TestStatusUpdates:
    """
    In this this test we verify, that all clients receive status update event via web socket
    once new user is online ('new_user_online' event that contains the username of the newly connected user).

    Two users needed for this test - the SENDER and the RECEIVER.
    While the RECEIVER is connected and listening to new events in a separate thread
    the SENDER establishes a connection and his status is changed to 'online'.

    The RECEIVER is expected to get the 'new_user_online' event (which should be published by the Chat Server)
    with the SENDER'S username.

    1. Verifying status change events were received.
    2. Verifying the event 'new_user_online' with SENDER'S username reached the RECEIVER
    """

    second_listener_events = None

    @pytest.mark.incremental
    @pytest.mark.parametrize('status_change_events_user_goes_online', [[{"sender_username": sender_username,
                                                       "sender_password": sender_password,
                                                       "receiver_username": receiver_username,
                                                       "receiver_password": receiver_password
                                                       }]],
                                                       indirect=True)
    def test_status_update_published_received(self, status_change_events_user_goes_online):

        try:
            # Both listeners are logged in, the RECEIVER is connected
            sender_listener, receiver_listener = status_change_events_user_goes_online

            # The RECEIVER listener is set to listen to incoming events and status updates in a separate thread
            listen_for_events(receiver_listener, test_duration_seconds)

            # The SENDER listener initiates a connection (while the RECEIVER is listening for new status updates)
            time.sleep(int(test_duration_seconds/2))
            sender_listener.initiate_connection()
            time.sleep(int(test_duration_seconds/2))

            # The RECEIVER ends the listening cycle, all received status updates are extracted
            TestStatusUpdates.second_listener_events = receiver_listener.list_recorded_status_updates()
            stop_all_listeners([sender_listener, receiver_listener])

            logging.info(TestStatusUpdates.second_listener_events)

            # We are to verify, that at least TWO status update events were received
            assert len(TestStatusUpdates.second_listener_events) > 1, \
                logging.error(f"QA Automation: Status update events weren't received")

        except AssertionError as e:
            logging.warning(f"Test {test_file_name} - step failed: {e}")
            stop_all_listeners([sender_listener, receiver_listener])
            ResultsReporter.report_failure(test_id, e, test_file_name)
            raise e

        except Exception as e:
            logging.warning(f"Test {test_file_name} is broken: {e}")
            stop_all_listeners([sender_listener, receiver_listener])
            ResultsReporter.report_broken_test(test_id, e, test_file_name)
            raise e

        logging.info(f"----------------------- Step Passed: Status Update events were published -----"
                     f"-----------------------------\n")

    @pytest.mark.incremental
    def test_status_update_events_content_verified(self):

        relevant_status_update_events = []

        try:

            # Verifying 'new_user_online' event was emitted, notifying that the SENDER is online
            for event in TestStatusUpdates.second_listener_events:
                if 'new_user_online' in event.keys():
                    if 'username' in event['new_user_online'].keys():
                        if event['new_user_online']['username'] == sender_username:
                            relevant_status_update_events.append(event)

            logging.info(relevant_status_update_events)

            assert len(relevant_status_update_events) == 1, logging.error(f"QA Automation: 'new_user_online' event "
                                                                          f"wasn't published for {sender_username}")

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

