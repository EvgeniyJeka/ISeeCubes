from tkinter import *

class LoginWindow:

    client_app_core = None
    main_ui_window = None
    button_connect = None

    def __init__(self, client_app_core):
        self.client_app_core = client_app_core


    def show_login_window(self, main_ui_window, button_connect):

        self.main_ui_window = main_ui_window
        self.button_connect = button_connect

        login_window = Tk()
        login_window.geometry("550x100")

        label_1 = Label(login_window, text="Username:", fg="blue", font=("", 11))
        username_entry = Entry(login_window, width="70")

        # TEMPORARY STUB !! Remove on Prod
        username_entry.insert(0, "Avi")

        label_2 = Label(login_window, text="Password: ", fg="blue", font=("", 11))
        password_entry = Entry(login_window, width="70")

        confirm_button = Button(login_window, text="Confirm", command=lambda: self.handle_confirm(login_window, username_entry, password_entry),
                                width=20, bg="blue",
                                fg="white")
        cancel_button = Button(login_window, text="Cancel", command=lambda: self.close_window(login_window), width=20,
                               bg="red", fg="white")

        label_1.grid(row=0, column=0, sticky=E)
        username_entry.grid(row=0, column=1)

        label_2.grid(row=1, column=0, sticky=E)
        password_entry.grid(row=1, column=1)

        confirm_button.grid(row=3, column=1, pady=6, sticky=W)
        cancel_button.grid(row=3, column=1, pady=6, sticky=E)

        login_window.mainloop()


    def handle_confirm(self, login_window, username_entry, password_entry):
        # IN PROGRESS!
        username = username_entry.get()
        password = password_entry.get()

        print(f"Log In Window: sending Log In request, username: {username}, password: {password}")
        result = self.client_app_core.send_log_in_request(username, password)
        print(result)
        self.main_ui_window.title(f"Hello, {username}")
        self.button_connect["state"] = NORMAL

        login_window.destroy()


    def close_window(self, window):
        window.destroy()

# if __name__ == "__main__":
#     login = LoginWindow()
#     login.show_login_window()


