from tkinter import *

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

        self.root.mainloop()

    def add_new_boomark_window(self):
        secondary = Tk()
        secondary.geometry("550x100")

        label_1 = Label(secondary, text=f"Entry {self.cnt}:", fg="blue", font=("", 11))
        entry = Entry(secondary, width="70")
        entry.num = self.cnt

        confirm_button = Button(secondary, text="Send", command=lambda: self.handle_send(entry),
                                width=20, bg="blue",
                                fg="white")

        label_1.grid(row=0, column=0, sticky=E)
        entry.grid(row=0, column=1)

        self.cnt +=1


        confirm_button.grid(row=3, column=1, pady=6, sticky=W)

        secondary.mainloop()

    def handle_send(self, entry):
        content = entry.get()
        print(f"Sending content from {entry.num}:\n {content}")



if __name__ == '__main__':
    chesk = ChatSkin()