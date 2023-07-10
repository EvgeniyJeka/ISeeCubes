import configparser
import os


def get_parser(config):
    parser = configparser.ConfigParser()
    with open(config, mode='r', buffering=-1, closefd=True):
        parser.read(config)
        return parser

class BaseConfig(object):

    config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini')
    parser = get_parser(config_file)
    print(os.getcwd())

    # Running locally
    if os.getenv('BASE_URL') is None:
        BASE_URL = parser.get('URL', 'BASE_URL')

        SENDER_USERNAME = parser.get('TEST_DATA', 'SENDER_NAME')
        SENDER_PASSWORD = parser.get('TEST_DATA', 'SENDER_PASSWORD')

        RECEIVER_USERNAME = parser.get('TEST_DATA', 'RECEIVER_NAME')
        RECEIVER_PASSWORD = parser.get('TEST_DATA', 'RECEIVER_PASSWORD')

        SECOND_RECEIVER_NAME = parser.get('TEST_DATA', 'SECOND_RECEIVER_NAME')
        SECOND_RECEIVER_PASSWORD = parser.get('TEST_DATA', 'SECOND_RECEIVER_PASSWORD')


    # Running in Docker container
    else:
        BASE_URL = os.getenv('BASE_URL')

        SENDER_USERNAME = os.getenv('SENDER_NAME')
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

        RECEIVER_USERNAME = os.getenv('RECEIVER_NAME')
        RECEIVER_PASSWORD = os.getenv('RECEIVER_PASSWORD')

        SECOND_RECEIVER_NAME = os.getenv('SECOND_RECEIVER_NAME')
        SECOND_RECEIVER_PASSWORD = os.getenv('SECOND_RECEIVER_PASSWORD')






if __name__ == '__main__':
    bc = BaseConfig()
    print(bc.BASE_URL)