import time
from tkinter import *
from tkinter import ttk
from tkinter import font
from PIL import ImageTk, Image

import socketio
import requests
import json
import threading

# TO DO:
# Add handling ON CONNECT & ON DISCONNECT. KEEP A LIST/DICT OF USERS THAT ARE CURRENTLY CONNECTED.

# Default window size when there are no bookmarks
height = 475
width = 220

# # standard Python
# sio = socketio.Client()
#
# my_name = "Lisa"
#
# sio.connect('http://localhost:5000')
#
# response = requests.get(f"http://localhost:5000/get_contacts_list/{my_name}")
#
# contacts_list = json.loads(response.text)
#
# # Establishing contacts with all persons from the Contacts List
# for contact in contacts_list:
#     conversation_room = contacts_list[contact]
#     sio.emit('join', {"room": conversation_room})

# When choosing the contact we want to converse with
# 'conversation_room' is selected.

# Choosing who do we want to talk with (message target, can be different for each message)
# THINK HOW TO PREVENT THE CONVERSATION ROOM FROM BEING HARDCODED!
# LISA CAN ADDRESS ANY PERSON FROM THE CONTACT LIST, BUT WHEN SHE IS ADDRESSED BY ANOTHER CONTACT
# SHE SHOULD REPLY TO THAT CONTACT.
#conversation_room = contacts_list["tsahi"]


class ChatRoom:

    entry = None
    contacts_list = None

    sio = None
    connected = False

    address_book = {
        "Avi": None,
        "Tsahi": None,
        "Era": None
    }


    def initiate_connection(self):
        # CONNECT method
        try:
            self.sio = socketio.Client()

            self.my_name = "Lisa"

            self.sio.connect('http://localhost:5000')
            response = requests.get(f"http://localhost:5000/get_contacts_list/{self.my_name}")
            self.contacts_list = json.loads(response.text)

            # Establishing contacts with all persons from the Contacts List
            for contact in self.contacts_list:
                conversation_room = self.contacts_list[contact]
                self.sio.emit('join', {"room": conversation_room})

            return True

        except Exception:
            return False


    def start_listening_loop(self):

        @self.sio.on('received_message')
        def handle_my_custom_event(message):

            if self.my_name != message['sender']:
                print(f"{message['sender']}: {message['content']}")
                first_message_conversation = f"{message['sender']}: {message['content']}"

                current_messages_box = self.address_book[message['sender']]

                # First message from given user
                if current_messages_box is None:
                    t1 = threading.Thread(target=self.show_message_box, args=(first_message_conversation, message['sender']))
                    t1.start()
                    time.sleep(6)

                # The conversation with the given user is going on, and a Chat Room is already open
                else:
                    current_messages_box.insert(INSERT, "\n")
                    current_messages_box.insert(INSERT, f"{message['sender']}: {message['content']}")


    # OPEN MESSAGE BOX (method in use)
    def show_message_box(self, first_mesage, message_sender):

        # Window size
        hight = 500
        width = 900
        size = '%sx%s' % (width, hight)

        # Window
        message_box_window = Tk()
        message_box_window.geometry(size)
        message_box_window.resizable(0, 0)

        # Messages Box - TK 'Text' object
        messages_box = Text(message_box_window, height=20, width=105)
        messages_box.grid(row=4, column=0, padx=25, pady=10)
        messages_box.grid(columnspan=10)

        # Entry box
        created_entry = Entry(message_box_window, width="140")
        created_entry.grid(row=7, column=3, padx=25, pady=5, sticky=W)

        messages_box.insert(INSERT, first_mesage)
        messages_box.insert(INSERT, "\n")

        self.address_book[message_sender] = messages_box

        # SEND button - the text from the entry box will be packed to a WS message and the former will be
        # emitted to the conversation room. (Remove 'not my message' validation?)
        button_send = Button(message_box_window, text="Send", bg="purple", fg="white", height="2", width="30",
                             command=lambda :self.handle_send(created_entry, messages_box, message_sender.lower()))
        button_send.place(x=240, y=380)

        # CLEAR button - clears the entry box
        button_clear = Button(message_box_window, text="Clear", bg="green", fg="white", height="2", width="30",
                              command=lambda: self.handle_clear())
        button_clear.place(x=440, y=380)

        # Handling WINDOW CLOSED - the value related to current message sender in the ADDRESS BOOK is NONE again,
        # so a NEW WINDOW will be opened once a message from that sender is received
        def on_closing():
            self.address_book[message_sender] = None
            message_box_window.destroy()

        message_box_window.protocol("WM_DELETE_WINDOW", on_closing)
        message_box_window.mainloop()


    def handle_send(self, target_entry, target_messages_box, destination):
        """
         # IN PROGRESS!
        :param target_entry:
        :param target_messages_box:
        :param destination:
        :return:
        """
        message_content = target_entry.get()
        print(f"Handling SEND {message_content} to {destination}")

        # Sending the message to the chat room, so the person defined as "destination" will receive it.
        conversation_room_ = self.contacts_list[destination]

        # CLEAR the ENTRY FIELD
        target_entry.delete(0, 'end')

        # ADD the message to the TEXT BOX (MESSAGE BOX)
        target_messages_box.insert(INSERT, "\n")
        target_messages_box.insert(INSERT, f"{self.my_name}: {message_content}")
        target_messages_box.insert(INSERT, "\n")

        # SEND the message to the server
        self.sio.emit('client_sends_message', {'sender': self.my_name,
                                          "content": message_content,
                                          "conversation_room": conversation_room_})

    def handle_clear(self):
        print("Handling CLEAR")




if __name__ == '__main__':
    chtr = ChatRoom()

    # Window size
    # hight = 600
    # width = 285
    # size = '%sx%s' % (width, hight)
    #
    # # Window
    # message_box_window = Tk()
    # message_box_window.geometry(size)
    # message_box_window.resizable(0, 0)
    #
    # # Header #1 - Label "I See Cubes"
    # head_label = Label(message_box_window, text="I See Cubes", fg="white", bg="PaleGreen1", font=("", 20), width=16)
    # head_label.place(x=11, y=3)
    #
    # # Header #2 - ICQ Image (or Kubernetes Image, or Custom Image)
    # frame = Frame(message_box_window, width=30, height=20)
    # frame.place(x=93, y=50)
    #
    # # Create an object of tkinter ImageTk
    # img = ImageTk.PhotoImage(Image.open("flower_blue.png"))
    #
    # # Create a Label Widget to display the text or Image
    # label = Label(frame, image=img)
    # label.pack()
    #
    # # Header #3 - Username: Lisa, Status: Connected
    # #.. T.B.D.
    #
    #
    # # LOG IN button
    # button_login = Button(message_box_window, text="Login", bg="RoyalBlue4", fg="cyan", height="1", width="36")
    # button_login.place(x=11, y=155)
    #
    # # CONNECT button :#chtr = ChatRoom(), perhaps in a separate thread,
    # # so the clicked CONNECT button won't block all the other buttons
    # button_login = Button(message_box_window, text="Connect", bg="RoyalBlue4", fg="cyan", height="1", width="36")
    # button_login.place(x=11, y=183)
    #
    # # Used listbox - for tables presentation and selection : selecting a person to chat with from the Contacts List
    # contacts_list = Listbox(message_box_window, selectmode=SINGLE, width=27, height=12, yscrollcommand=True,
    #                         bd=3, selectbackground="LightSky Blue3", font="Times 13 italic bold")
    # contacts_list.place(x=17, y=220)
    #
    # # Filling the Contact List with contacts - a STUB, eventually the contacts will be taken from the server feed
    # contacts_list.insert(1, "Avi")
    # contacts_list.insert(2, "Tsahi")
    # contacts_list.insert(3, "Era")
    #
    # # CHAT WITH button
    # chat_with = Button(message_box_window, text="Chat With", bg="SteelBlue4", fg="cyan", height="1", width="36")
    # chat_with.place(x=11, y=490)
    #
    # # OPTIONS button
    # options = Button(message_box_window, text="Options", bg="SteelBlue4", fg="cyan", height="1", width="36")
    # options.place(x=11, y=520)
    #
    # # DISCONNECT button
    # disconnect = Button(message_box_window, text="Disconnect", bg="SteelBlue4", fg="cyan", height="1", width="36")
    # disconnect.place(x=11, y=550)
    #
    #
    # # Handling WINDOW CLOSED - the value related to current message sender in the ADDRESS BOOK is NONE again,
    # # so a NEW WINDOW will be opened once a message from that sender is received
    # def on_closing():
    #     print("Window closed!")
    #     message_box_window.destroy()
    #
    #
    # message_box_window.protocol("WM_DELETE_WINDOW", on_closing)
    # message_box_window.mainloop()

