from tkinter import *

#from clients.lisa.chat_client_app_core import ClientAppCore


class MessageBox:

    my_name = None
    address_book = None
    contacts_list = None
    sio = None
    auth_token = None

    def __init__(self, client_app_core):

        self.my_name = client_app_core.my_name
        self.address_book = client_app_core.address_book
        self.contacts_list = client_app_core.contacts_list
        self.sio = client_app_core.sio
        self.auth_token = client_app_core.current_auth_token


    # OPEN MESSAGE BOX (method in use)
    def show_message_box(self, first_mesage, message_sender):
        # Window size
        hight = 400
        width = 600
        size = '%sx%s' % (width, hight)

        # Window
        message_box_window = Tk()
        message_box_window.geometry(size)
        message_box_window.resizable(0, 0)
        message_box_window.title(f"Coversation between {self.my_name} and {message_sender}")

        # Messages Box - TK 'Text' object
        messages_box = Text(message_box_window, height=18, width=70)
        messages_box.place(x=16, y=8)

        # # Entry box
        created_entry = Entry(message_box_window, width=93)
        created_entry.place(x=17, y=308)

        messages_box.configure(state="normal")
        messages_box.insert(INSERT, first_mesage)
        messages_box.insert(INSERT, "\n")
        messages_box.configure(state="disabled")

        self.address_book[message_sender] = messages_box

        # SEND button - the text from the entry box will be packed to a WS message and the former will be
        # emitted to the conversation room. (Remove 'not my message' validation?)
        button_send = Button(message_box_window, text="Send", bg='#567', fg='White', height="1", width="15",
                             command=lambda: self.handle_send(created_entry, messages_box, message_sender))
        button_send.place(x=465, y=340)
        #
        # CLEAR button - clears the entry box
        button_clear = Button(message_box_window, text="Clear", bg='#567', fg='White', height="1", width="15",
                              command=lambda: self.handle_clear())
        button_clear.place(x=17, y=340)


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
        target_messages_box.configure(state="normal")
        target_messages_box.insert(INSERT, "\n")
        target_messages_box.insert(INSERT, f"Me: {message_content}")
        target_messages_box.insert(INSERT, "\n")
        target_messages_box.see("end")
        target_messages_box.configure(state="disabled")

        # SEND the message to the server
        self.sio.emit('client_sends_message', {'sender': self.my_name,
                                               "content": message_content,
                                               "conversation_room": conversation_room_,
                                               "jwt": self.auth_token})

    def handle_clear(self):
        print("Handling CLEAR")


# if __name__ == '__main__':
#     mb = MessageBox()
#     mb.show_message_box("11", "22")