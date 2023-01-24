import time
from tkinter import *
from tkinter import ttk
from tkinter import font
from PIL import ImageTk, Image


import socketio
import requests
import json
import threading

from clients.tsahi.chat_client_app_core import ClientAppCore
from clients.tsahi.login_window import LoginWindow

hight = 600
width = 285

# TO DO:
# Client, UI:
# if the client is ALREADY CONNECTED the CONNECT button should DO NOTHING, OR BE DISABLED (
# chat box size and design
# chat box 'clear' button
# chat box - current user name needs to be colored with green
# Custom 'keep alive' logic both on server and on client side D
#
# Client UI, chatroom header - add the current user name D
# Client UI, chat box header - add the current user name D
#
# Log In window (can take from Bookmarker) with CANCEL and CONFIRMATION D
# Log In request (client side), response parsed. D
# Connect button is enabled only after successful Log In D
# Log in button is disabled after successful login and re-enabled after disconnect

class ChatClient:

    client_app_core = None
    connection_status = False
    listening_loop_thread = None
    sending_keep_alive_thread = None

    contacts_list_ui_element = None
    connect_button_ui_element = None
    connection_indicator_ui_element = None

    main_ui_window = None
    log_in_window = None

    button_connect = None
    button_chat_with = None

    def __init__(self):

        # Chat Client Main UI Window
        self.main_ui_window = Tk()
        self.main_ui_window.geometry(f"{width}x{hight}")
        self.main_ui_window.resizable(0, 0)

        # Header #1 - Label "I See Cubes"
        head_label = Label(self.main_ui_window, text="I See Cubes", fg="white", bg="PaleGreen1", font=("", 20), width=16)
        head_label.place(x=11, y=3)

        # Header #2 - ICQ Image (or Kubernetes Image, or Custom Image)
        frame = Frame(self.main_ui_window, width=30, height=20)
        frame.place(x=93, y=50)

        # Create an object of tkinter ImageTk
        img = ImageTk.PhotoImage(Image.open("flower_blue.png"))

        # Create a Label Widget to display the text or Image
        picture_label = Label(frame, image=img)
        picture_label.pack()

        # Header #3 - Username: Lisa, Status: Connected
        connection_status_label = Label(self.main_ui_window, text="Connection status:", fg="blue", font=("", 13), width=15)
        connection_status_label.place(x=29, y=125)

        self.connection_indicator_ui_element = Label(self.main_ui_window, text="Offline", fg="red", font=("", 13), width=10)
        self.connection_indicator_ui_element.place(x=165, y=125)

        # LOG IN button
        button_login = Button(self.main_ui_window, text="Login", bg="RoyalBlue4", fg="cyan", height="1", width="36",
                              command=lambda: self.open_login_window())
        button_login.place(x=11, y=155)

        # CONNECT button, the operation is handled in a separate thread,
        # so the clicked CONNECT button won't block all the other buttons
        self.button_connect = Button(self.main_ui_window, text="Connect", bg="RoyalBlue4", fg="cyan", height="1", width="36",
                                     command=lambda: self.handle_connect())
        self.button_connect.place(x=11, y=183)

        # Used listbox - for tables presentation and selection : selecting a person to chat with from the Contacts List
        self.contacts_list_ui_element = Listbox(self.main_ui_window, selectmode=SINGLE, width=27, height=12, yscrollcommand=True,
                                                bd=3, selectbackground="LightSky Blue3", font="Times 13 italic bold")
        self.contacts_list_ui_element.place(x=17, y=220)

        # This instance of ClientAppCore will be used to handle connections, disconnections and conversations
        self.client_app_core = ClientAppCore(self.contacts_list_ui_element)

        # Log In window
        self.log_in_window = LoginWindow(self.client_app_core)

        # Default message box windows header
        self.main_ui_window.title(f"Disconnected")

        # CHAT WITH button
        self.button_chat_with = Button(self.main_ui_window, text="Chat With", bg="SteelBlue4", fg="cyan", height="1", width="36",
                                  command=lambda: self.take_selected_chat_partner_from_ui())
        self.button_chat_with.place(x=11, y=490)

        # OPTIONS button
        button_options = Button(self.main_ui_window, text="Options", bg="SteelBlue4", fg="cyan", height="1", width="36")
        button_options.place(x=11, y=520)

        # DISCONNECT button
        button_disconnect = Button(self.main_ui_window, text="Disconnect", bg="SteelBlue4", fg="cyan", height="1", width="36",
                                   command=lambda: self.handle_disconnect())
        button_disconnect.place(x=11, y=550)

        self.button_connect["state"] = DISABLED
        self.button_chat_with["state"] = DISABLED

        # Handling WINDOW CLOSED - the value related to current message sender in the ADDRESS BOOK is NONE again,
        # so a NEW WINDOW will be opened once a message from that sender is received
        def on_closing():
            print("Window closed!")
            self.handle_disconnect()
            self.main_ui_window.destroy()

        self.main_ui_window.protocol("WM_DELETE_WINDOW", on_closing)
        self.main_ui_window.mainloop()

    # CHAT WITH button - MAKE ENABLED ONLY AFTER CONNECTION IS ESTABLISHED !!
    def take_selected_chat_partner_from_ui(self):
        selected_contact = self.contacts_list_ui_element.curselection()
        try:
            self.handle_chat_with(self.contacts_list_ui_element.get(selected_contact[0]))
        except IndexError as e:
            print(f"No contact was selected: {e}")

    def handle_connect(self):
        print("Button clicked: CONNECT")
        # When connection is initiated the list of the available contacts is fetched from the server
        server_initiate_feed = self.client_app_core.initiate_connection()

        if server_initiate_feed is False:
            print("Client App Core: Error, failed to connect")
            return

        contacts_list = server_initiate_feed['contacts']
        online_contacts = server_initiate_feed["currently_online"]

        if contacts_list:
            self.connection_status = True
            self.connection_indicator_ui_element.config(text="Online", fg="green")
        else:
            print("Failed to connect!")

        # Inserting the list of contacts that was fetched into the 'Contact List' UI Element
        self.contacts_list_ui_element.delete(0, END)
        self.contacts_list_ui_element.insert(END, *contacts_list)

        # Color the 'online' contacts in Green (and all others in Red)
        self.client_app_core.color_online_offline_contacts(online_contacts)

        self.button_connect["state"] = DISABLED
        self.button_chat_with["state"] = ACTIVE

        print("Starting Listening Loop")
        self.listening_loop_thread = threading.Thread(target=self.client_app_core.start_listening_loop)
        self.listening_loop_thread.start()

        print("Starting Sending Keep Alive Loop")
        self.sending_keep_alive_thread = threading.Thread(target=self.client_app_core.sending_keep_alive_loop)
        self.sending_keep_alive_thread.start()

    def handle_disconnect(self):
        print("Button clicked: DISCONNECT")
        if self.connection_status is False:
            print("NOT CONNECTED")
            return

        self.button_connect["state"] = NORMAL

        # Connection is terminated, user is logged out
        self.connection_status = False
        self.client_app_core.user_logged_in = False

        self.button_connect["state"] = DISABLED
        self.button_chat_with["state"] = DISABLED

        # Modifying UI on disconnection
        self.connection_indicator_ui_element.config(text="Offline", fg="red")
        self.contacts_list_ui_element.delete(0, END)

        # Removing the user name in window header
        self.main_ui_window.title(f"Please log in")

        # Emitting 'client_disconnection' event to the server
        self.client_app_core.sio.emit('client_disconnection', {"client": self.client_app_core.my_name})

        # Stopping the Listening Loop thread
        self.listening_loop_thread.join(timeout=2)

        # Stopping the Sending Keep Alive Loop thread
        self.sending_keep_alive_thread.join(timeout=2)

    def open_login_window(self):
        if self.client_app_core.user_logged_in is False:
            self.log_in_window.show_login_window(self.main_ui_window, self.button_connect)

    def handle_chat_with(self, target_contact):
        print("Button clicked: CHAT WITH")
        t2 = threading.Thread(target=self.start_chat_thread, args=(target_contact,))
        t2.start()

    def start_chat_thread(self, target_contact=None):
        self.client_app_core.message_box.show_message_box(" ", target_contact)



if __name__ == '__main__':
    client = ChatClient()