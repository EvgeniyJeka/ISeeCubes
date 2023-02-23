from tkinter import *
import logging
import functools
from local_client_config import MessageBoxConfig

logging.basicConfig(level=logging.INFO)


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

    def show_message_box(self, first_message, message_sender):
        """
        This method is used to open the Message Box window (UI).
        It opens a Tkinter window, and it runs in a closed loop until terminated.
        :param first_message: str
        :param message_sender: existing user name, str
        :return: n/a
        """
        # Window size
        size = MessageBoxConfig.MESSAGE_BOX_SIZE.value

        # Window
        message_box_window = Tk()
        message_box_window.geometry(size)
        message_box_window.resizable(0, 0)
        message_box_window.title(f"Coversation between {self.my_name} and {message_sender}")

        # Messages Box - TK 'Text' object
        messages_box = Text(message_box_window, height=18, width=70)
        messages_box.place(x=16, y=8)

        messages_box.option_clear()

        # # Entry box
        created_entry = Entry(message_box_window, width=93)
        created_entry.place(x=17, y=308)

        messages_box.configure(state="normal")
        messages_box.insert(INSERT, first_message)
        messages_box.insert(INSERT, "\n")
        messages_box.configure(state="disabled")

        self.address_book[message_sender] = messages_box

        # SEND button - the text from the entry box will be packed to a WS message and the former will be
        # emitted to the conversation room. (Remove 'not my message' validation?)
        button_send = Button(message_box_window, text="Send", bg='#567', fg='White', height="1", width="15",
                             command=lambda: self.handle_send(created_entry, messages_box, message_sender))
        button_send.place(x=465, y=340)

        message_box_window.bind("<Return>", functools.partial(self.handle_send, created_entry, messages_box, message_sender))

        # CLEAR button - clears the entry box
        button_clear = Button(message_box_window, text="Clear", bg='#567', fg='White', height="1", width="15",
                              command=lambda: self.handle_clear(messages_box))
        button_clear.place(x=17, y=340)

        # Handling WINDOW CLOSED - the value related to current message sender in the ADDRESS BOOK is NONE again,
        # so a NEW WINDOW will be opened once a message from that sender is received
        def on_closing():
            self.address_book[message_sender] = None
            message_box_window.destroy()

        message_box_window.protocol("WM_DELETE_WINDOW", on_closing)
        message_box_window.mainloop()

    def handle_send(self, target_entry, target_messages_box, destination, *args):
        """
        This method is attached to the 'Send' button.
        Once the button is clicked, the content of the entry is packed and send
        as a websocket message to the target contact.

        :param target_entry: Tkinter 'entry' instance
        :param target_messages_box: Tkinter 'text' instance
        :param destination: existing user name, String
        :return: True on success
        """
        message_content = target_entry.get()
        logging.info(f"Handling SEND {message_content} to {destination}")

        if len(message_content) < 1:
            logging.warning("Message box: user tries to send an empty string, blocked")
            return False

        # CLEAR the ENTRY FIELD
        target_entry.delete(0, 'end')

        # ADD the message to the TEXT BOX (MESSAGE BOX)
        target_messages_box.configure(state="normal")

        target_messages_box.insert(INSERT, "\n")
        target_messages_box.insert(INSERT, f"Me: {message_content}")
        target_messages_box.insert(INSERT, "\n")
        target_messages_box.see("end")

        target_messages_box.configure(state="disabled")

        try:
            # Sending the message to the chat room, so the person defined as "destination" will receive it.
            conversation_room_ = self.contacts_list[destination]
            logging.info(f"Sending message {message_content} to {conversation_room_}")

            # SEND the message to the server
            self.sio.emit('client_sends_message', {'sender': self.my_name,
                                                   "content": message_content,
                                                   "conversation_room": conversation_room_,
                                                   "jwt": self.auth_token})

            return True

        except Exception as e:
            logging.error(f"Message Box: failed to send the message {message_content} - {e}")
            target_entry.insert(0, "Error: Failed to send the message!")
            return False

    def handle_clear(self, messages_box):
        """
        This method is attached to the 'Clear' button.
        It deletes all content in the Message Box
        :param messages_box: Tkinter 'Text' element
        :return: True on success
        """
        try:
            messages_box.configure(state="normal")
            messages_box.delete(1.0, END)
            logging.info("Handling CLEAR")
            messages_box.configure(state="disabled")
            return True

        except Exception as e:
            logging.error(f"Message Box: Failed to delete content, the following error has occured: {e}")
            return False


# if __name__ == '__main__':
#     mb = MessageBox()
#     mb.show_message_box("11", "22")