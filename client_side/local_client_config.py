from enum import Enum


class LoginWindowConfig(Enum):
    LOGIN_WINDOW_SIZE = "550x100"


class LoginWindowErrorMessages(Enum):
    WRONG_CREDENTIALS = "Wrong credentials. Please re login with your credentials."
    SERVER_UNAVAILABLE = "Log In failed. Chat server isn't available at the moment."
    UNKNOWN_SERVER_CODE = "Log In failed. Server side error."


class MainWindowConfig(Enum):
    MAIN_UI_WINDOW_SIZE = "285x600"


class MessageBoxConfig(Enum):
    MESSAGE_BOX_SIZE = "600x400"

class ErrorMessagePopConfig(Enum):
    ERROR_POP_UP_SIZE = "350x180"


class ErrorTypes:

    @staticmethod
    def errors_map():
        result = {"SERVER_TEMPORARY_DOWN": "Error: Chat Server is temporary down.\nPlease re login and re connect.",
                  "LOGIN_REQUEST_FAILED": "Error: Log In failed.\n Chat Server isn't available at the moment.",
                  "CONNECTION_ATTEMPT_FAILED": "Error: Couldn't connect to the server.\n Chat Server isn't available at the moment.",
                  "INVALID_CREDENTIALS": "Error: Wrong credentials.\n Please re login with your credentials.",
                  "UNEXPECTED_SERVER_RESPONSE": "Error: Log In failed. Server side error."}

        return result


class AppConfig(Enum):
    KEEP_ALIVE_DELAY_BETWEEN_EVENTS = 6
    CHAT_SERVER_BASE_URL = "http://localhost:5000"