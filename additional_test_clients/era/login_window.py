from tkinter import *
import logging
import requests

from additional_test_clients.era.local_client_config import LoginWindowConfig, LoginWindowErrorMessages


class LoginWindow:

    client_app_core = None
    main_ui_window = None
    button_connect = None

    def __init__(self, client_app_core):
        self.client_app_core = client_app_core

    def show_login_window(self, main_ui_window, button_connect):
        """
        This method opens the Log In window.
        The Log In window contains 2 entry boxes and 2 buttons, once the user enter his credentials
        and clicks on the 'Confirm' button the client sends a 'Log In' request to the server.
        If the log in attempt was successful, the 'Connect' button on the main UI window is unlocked,
        and the user can connect.
        :param main_ui_window: Tkinter window object, main UI window
        :param button_connect: TKinter button, 'Connect'
        """

        self.main_ui_window = main_ui_window
        self.button_connect = button_connect

        login_window = Tk()
        login_window.geometry(LoginWindowConfig.LOGIN_WINDOW_SIZE.value)

        username_label = Label(login_window, text="Username:", fg="blue", font=("", 11))
        username_entry = Entry(login_window, width="70")

        password_label = Label(login_window, text="Password: ", fg="blue", font=("", 11))
        password_entry = Entry(login_window, width="70")

        confirm_button = Button(login_window, text="Confirm", command=lambda:
                                self.handle_confirm(login_window, username_entry, password_entry),
                                width=20, bg="blue",
                                fg="white")
        cancel_button = Button(login_window, text="Cancel", command=lambda: self.close_window(login_window), width=20,
                               bg="red", fg="white")

        # TEMPORARY STUB !! Remove on Prod
        username_entry.insert(0, "Era")
        password_entry.insert(0, "Come on")

        username_label.grid(row=0, column=0, sticky=E)
        username_entry.grid(row=0, column=1)

        password_label.grid(row=1, column=0, sticky=E)
        password_entry.grid(row=1, column=1)

        confirm_button.grid(row=3, column=1, pady=6, sticky=W)
        cancel_button.grid(row=3, column=1, pady=6, sticky=E)

        login_window.mainloop()

    def handle_confirm(self, login_window, username_entry, password_entry):
        """
        This method is used to process the 'Confirm' button click.
        It accepts the Tkinter login window, the username and the password entries,
        extract the user creds from those entries and use the 'client_app_core' instance
        to send the 'log in' request.
        If the request is responded with a confirmation and a JWT token the window closes
        and the 'connect' button is unblocked (the token is assigned to 'client_app_core' instance  variable).

        :param login_window: TK window instance (current login window)
        :param username_entry: TK entry
        :param password_entry: TK entry
        :return: True on successs
        """
        username = username_entry.get()
        password = password_entry.get()

        try:
            logging.info(f"Log In Window: sending Log In request, username: {username}, password: {password}")
            response = self.client_app_core.send_log_in_request(username, password)

            # Successful login
            if response['result'] == "success":
                self.main_ui_window.title(f"Hello, {username}")
                self.button_connect["state"] = NORMAL
                login_window.destroy()

            # Invalid credentials
            elif response['result'] == "Invalid credentials":
                username_entry.delete(0, 'end')
                password_entry.delete(0, 'end')
                password_entry.insert(0, LoginWindowErrorMessages.WRONG_CREDENTIALS.value)

            # Unexpected response
            elif response['result'] == "Unknown server code":
                username_entry.delete(0, 'end')
                password_entry.delete(0, 'end')
                password_entry.insert(0, "Log In failed. Please restart the client and verify internet connection")

            return True

        except requests.exceptions.ConnectionError as e:
            logging.error(f"Login window: Failed to log in, server unavailable - {e}")
            logging.error(f"Login window: Failed to log in - {e}")
            username_entry.delete(0, 'end')
            password_entry.delete(0, 'end')
            password_entry.insert(0, LoginWindowErrorMessages.SERVER_UNAVAILABLE.value)
            return False

        except Exception as e:
            logging.error(f"Login window: Failed to log in - {e}")
            username_entry.delete(0, 'end')
            password_entry.delete(0, 'end')
            password_entry.insert(0, LoginWindowErrorMessages.UNKNOWN_SERVER_CODE.value)
            return False

    def close_window(self, window):
        window.destroy()



