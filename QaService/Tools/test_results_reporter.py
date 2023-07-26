import os
import traceback
from datetime import datetime
import logging


class ResultsReporter:

    # Since we currently have no 3rd party API for tests results reporting
    # those methods will be added to all tests, but won't do a thing (except for printing).
    # In the future each method will send an API request to PractiTest (or TestRail).
    # Perhaps we will choose to send those notifications via Slack or Email

    @staticmethod
    def set_results_file_path():
        project_path = os.path.dirname(__file__)
        folder_name = os.path.basename(project_path)

        while folder_name != 'QaService':
            project_path = os.path.dirname(project_path)
            folder_name = os.path.basename(project_path)

        directories = [name for name in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, name))]

        if 'Logs' not in directories:
            new_dir_path = os.path.join(project_path, "Logs")
            os.makedirs(new_dir_path)

        return os.path.join(project_path, "Logs")

    @staticmethod
    def report_success(test_id):
        base_path = ResultsReporter.set_results_file_path()
        original_path = os.path.join(base_path, 'test_results_report.txt')

        with open(original_path, "a+") as f:
            f.write(f"\nTest {test_id} have PASSED: {datetime.now()}\n")

        logging.info(f"\n\n---------------------- Reporting: TEST {test_id}_ PASSED! ----------------------\n\n")

    @staticmethod
    def report_failure(test_id, exception_):
        base_path = ResultsReporter.set_results_file_path()
        original_path = os.path.join(base_path, 'test_results_report.txt')

        with open(original_path, "a+") as f:
            f.write(f"\nTest {test_id} have FAILED: {datetime.now()}\n")
            f.write(f"\n{exception_}\n")

        logging.error(f"\n\n----------------------Reporting: TEST {test_id}_ FAILED!----------------------\n\n")

    @staticmethod
    def report_broken_test(test_id, exception_):
        base_path = ResultsReporter.set_results_file_path()
        original_path = os.path.join(base_path, 'test_results_report.txt')

        with open(original_path, "a+") as f:
            f.write(f"\nTest {test_id} is BROKEN: {datetime.now()}\n")
            f.write(f"\n{exception_}\n")

        logging.error(f"\n\n----------------------Reporting: TEST {test_id}_ IS BROKEN! {exception_}\n\n----------------------")
