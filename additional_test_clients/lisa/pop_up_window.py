from tkinter import *
import logging

from additional_test_clients.lisa.local_client_config import ErrorTypes, ErrorMessagePopConfig

logging.basicConfig(level=logging.INFO)


class PopupWindow:

    pop_up_type = None
    pop_up_window = None
    message_text = 0
    errors_map = ErrorTypes.errors_map()

    def __init__(self, pop_up_type):
        self.pop_up_type = pop_up_type
        self.message_text = self.errors_map[pop_up_type]

    def show_pop_up(self):

        # Window size
        size = ErrorMessagePopConfig.ERROR_POP_UP_SIZE.value

        # Window
        self.pop_up_window = Tk()
        self.pop_up_window.geometry(size)
        self.pop_up_window.resizable(0, 0)
        self.pop_up_window.title(f"Notification")

        # Error message text
        connection_status_label = Label(self.pop_up_window, text=self.message_text,
                                        fg="black", font=("", 13), width=35)
        connection_status_label.place(x=15, y=20)

        # OK button
        button_login = Button(self.pop_up_window, text="OK", bg="RoyalBlue4", fg="cyan", height="1", width="36",
                              command=self.close_error_message)
        button_login.place(x=45, y=115)

        def on_closing():
            self.pop_up_window.destroy()

        self.pop_up_window.protocol("WM_DELETE_WINDOW", on_closing)
        self.pop_up_window.mainloop()

    def close_error_message(self):
        self.pop_up_window.destroy()


if __name__ == "__main__":
    pp = PopupWindow("ERROR_SERVER_DOWN")
    pp.show_pop_up()
