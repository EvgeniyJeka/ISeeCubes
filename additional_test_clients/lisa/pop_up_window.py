from tkinter import *
import logging

logging.basicConfig(level=logging.INFO)


class PopupWindow:

    pop_up_type = None
    pop_up_window = None
    message_text = 0


    def __init__(self, pop_up_type):
        self.pop_up_type = pop_up_type
        self.message_text = "Error: Chat Server is temporary down.\nPlease re login and re connect."

    def show_pop_up(self):

        # Window size
        size = "350x200"

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

        def on_closing():
            self.pop_up_window.destroy()

        self.pop_up_window.protocol("WM_DELETE_WINDOW", on_closing)
        self.pop_up_window.mainloop()



if __name__ == "__main__":
    pp = PopupWindow("ERROR_SERVER_DOWN")
    pp.show_pop_up()
