from tkinter import *
import socketio
import requests
import json
import threading

# Default window size when there are no bookmarks
height = 475
width = 220


class ChatSkin:

    def __init__(self):
        self.root = Tk()
        self.cnt = 0

        # The actual window size
        size = '%sx%s' % (width, height)

        self.root.geometry(size)

        # Increase window heigh (test
        add_button = Button(self.root, command=lambda: self.add_new_boomark_window(), text="Test", width=20)
        add_button.grid(row=0, column=0, padx=12, pady=2)

        # Increase window heigh (test
        add_button = Button(self.root,  text="Start Chat", width=20)
        add_button.grid(row=1, column=0, padx=12, pady=2)

        self.root.mainloop()

    def add_new_boomark_window(self):
        secondary = Tk()
        secondary.geometry("550x100")

        label_1 = Label(secondary, text=f"Entry {self.cnt}:", fg="blue", font=("", 11))
        entry = Entry(secondary, width="70")
        entry.num = self.cnt

        # confirm_button = Button(secondary, text="Handle Read", command=lambda: self.handle_read(entry),
        #                         width=20, bg="blue",
        #                         fg="white")

        label_1.grid(row=0, column=0, sticky=E)
        entry.grid(row=0, column=1)

        self.cnt +=1


        # confirm_button.grid(row=3, column=1, pady=6, sticky=W)

        t1 = threading.Thread(target=self.engage, args=(entry,))
        t1.start()

        secondary.mainloop()

    # def handle_read(self, entry):
    #     t1 = threading.Thread(target=self.engage, args=(entry,))
    #     t1.start()


    def engage(self, entry: Entry):
        ##standard Python
        sio = socketio.Client()

        my_name = "Lisa"

        sio.connect('http://localhost:5000')

        response = requests.get(f"http://localhost:5000/get_contacts_list/{my_name}")

        contacts_list = json.loads(response.text)

        # Establishing contacts with all persons from the Contacts List
        for contact in contacts_list:
            conversation_room = contacts_list[contact]
            sio.emit('join', {"room": conversation_room})

        # When choosing the contact we want to converse with
        # 'conversation_room' is selected.

        # Choosing who do we want to talk with (message target, can be different for each message)
        conversation_room = contacts_list["tsahi"]

        while True:

            @sio.on('received_message')
            def handle_my_custom_event(message):

                if my_name != message['sender']:
                    print(f"{message['sender']}: {message['content']}")
                    entry.delete(0, 'end')
                    entry.insert(0, f"{message['sender']}: {message['content']}")


            message = input()
            sio.emit('client_sends_message',
                     {'sender': my_name, "content": message, "conversation_room": conversation_room})




if __name__ == '__main__':
    chesk = ChatSkin()