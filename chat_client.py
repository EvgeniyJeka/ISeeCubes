import time
from tkinter import *
from tkinter import ttk
from tkinter import font
from PIL import ImageTk, Image

from chat_room import ChatRoom

import socketio
import requests
import json
import threading

class ChatClient:

    chat_room = None

    def __init__(self):
        # Window size
        hight = 600
        width = 285
        size = '%sx%s' % (width, hight)

        # Window
        message_box_window = Tk()
        message_box_window.geometry(size)
        message_box_window.resizable(0, 0)

        # Header #1 - Label "I See Cubes"
        head_label = Label(message_box_window, text="I See Cubes", fg="white", bg="PaleGreen1", font=("", 20), width=16)
        head_label.place(x=11, y=3)

        # Header #2 - ICQ Image (or Kubernetes Image, or Custom Image)
        frame = Frame(message_box_window, width=30, height=20)
        frame.place(x=93, y=50)

        # Create an object of tkinter ImageTk
        img = ImageTk.PhotoImage(Image.open("flower_blue.png"))

        # Create a Label Widget to display the text or Image
        label = Label(frame, image=img)
        label.pack()

        # Header #3 - Username: Lisa, Status: Connected
        # .. T.B.D.

        # LOG IN button
        button_login = Button(message_box_window, text="Login", bg="RoyalBlue4", fg="cyan", height="1", width="36")
        button_login.place(x=11, y=155)

        # CONNECT button :#chtr = ChatRoom(), perhaps in a separate thread,
        # so the clicked CONNECT button won't block all the other buttons
        button_connect = Button(message_box_window, text="Connect", bg="RoyalBlue4", fg="cyan", height="1", width="36",
                              command=lambda: self.handle_connect())
        button_connect.place(x=11, y=183)

        # Used listbox - for tables presentation and selection : selecting a person to chat with from the Contacts List
        contacts_list = Listbox(message_box_window, selectmode=SINGLE, width=27, height=12, yscrollcommand=True,
                                bd=3, selectbackground="LightSky Blue3", font="Times 13 italic bold")
        contacts_list.place(x=17, y=220)

        # Filling the Contact List with contacts - a STUB, eventually the contacts will be taken from the server feed
        contacts_list.insert(1, "Avi")
        contacts_list.insert(2, "Tsahi")
        contacts_list.insert(3, "Era")

        # CHAT WITH button - MAKE ENABLED ONLY AFTER CONNECTION IS ESTABLISHED !!
        def take_selected_chat_partner_from_ui():
            selected_contact = contacts_list.curselection()
            self.handle_chat_with(contacts_list.get(selected_contact[0]))

        button_chat_with = Button(message_box_window, text="Chat With", bg="SteelBlue4", fg="cyan", height="1", width="36",
                                  command=lambda: take_selected_chat_partner_from_ui())
        button_chat_with.place(x=11, y=490)

        # OPTIONS button
        button_options = Button(message_box_window, text="Options", bg="SteelBlue4", fg="cyan", height="1", width="36")
        button_options.place(x=11, y=520)

        # DISCONNECT button
        button_disconnect = Button(message_box_window, text="Disconnect", bg="SteelBlue4", fg="cyan", height="1", width="36")
        button_disconnect.place(x=11, y=550)

        # Handling WINDOW CLOSED - the value related to current message sender in the ADDRESS BOOK is NONE again,
        # so a NEW WINDOW will be opened once a message from that sender is received
        def on_closing():
            print("Window closed!")
            message_box_window.destroy()

        message_box_window.protocol("WM_DELETE_WINDOW", on_closing)
        message_box_window.mainloop()

    def handle_connect(self):
        print("Button clicked: CONNECT")
        t1 = threading.Thread(target=ChatRoom)
        t1.start()

    def handle_chat_with(self, target_contact):
        print("Button clicked: CHAT WITH")
        # TAKE ARGS !!
        t2 = threading.Thread(target=self.start_chat_thread, args=(target_contact,))
        t2.start()

    # PASS ARGS !!
    def start_chat_thread(self, target_contact=None):
        chat_room = ChatRoom(non_loop_flag=True)
        chat_room.show_message_box(" ", target_contact)


if __name__ == '__main__':
    client = ChatClient()