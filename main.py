# from PySide6 import QtCore as QC 
# from PySide6 import QtWidgets as QW

# class MainWindow(QW.QWidget):
#     def __init__(self):
#         super().__init__()

#         self.setWindowTitle("Thinking Space")
        

from tkinter import *
from PIL import Image, ImageTk
import os
import sys
from typing import final

if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(app_dir)

FADE_COLORS = ("#030303", "#121212", "#212121", "#313131", "#474747", "#656565", "#8f8f8f", "#aeaeae", "#cacaca") #, "#e7e7e7", "#ffffff"

@final
class App:
    def __init__(self):
        self.root = Tk()
        self.root.option_add('*relief', 'flat')

        self.root.title("Thinking Space")
        self.root.geometry("960x810")
        self.root.update_idletasks()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.space_idx = -1

        self.local_data = {}

        self.menu = Frame(self.root, bg="grey")
        self.menu.place(width=200, relheight=1)

        self.menu_label = Label(self.menu, text="𝚃𝚑𝚒𝚗𝚔𝚒𝚗𝚐 𝚂𝚙𝚊𝚌𝚎", font=("Arial", 12))
        self.menu_label.place(relwidth=1, width=-50, height=50)

        self.add_button = Button(self.menu, text="+", font=("Arial", 24), command=self.new_space)
        self.add_button.place(relx=1, x=-50, width=50, height=50)

        self.space_frame = Frame(self.root, bg="grey")
        self.space_frame.place(x=200, relwidth=1, width=-200, relheight=1)

        self.welcome_label = Label(self.space_frame, text="𝚆𝚎𝚕𝚌𝚘𝚖𝚎!\n𝙰𝚍𝚍 𝚊 𝚂𝚙𝚊𝚌𝚎 𝚝𝚘 𝚋𝚎𝚐𝚒𝚗.", justify=CENTER, font=("Arial", 24))
        self.welcome_label.place(relwidth=1, relheight=1)

        self.root.mainloop()

    def on_close(self):
        self.root.destroy()

    def new_space(self):
        self.space_idx += 1
        button = Button(self.menu, text=self.space_idx + 1)
        button.index = self.space_idx
        button["command"] = lambda idx=button.index: self.print_idx(idx)
        button.place(y=50 * (self.space_idx + 1), relwidth=1, height=50)

        # self.save_data(button.index)

        if self.welcome_label is not None:
            self.fade(self.welcome_label, 0)
            self.welcome_label = None

    def fade(self, widget, value):
        if value < len(FADE_COLORS):
            widget["fg"] = FADE_COLORS[value]
            self.root.after(50, self.fade, widget, value + 1)
        else:
            widget.destroy()

    def print_idx(self, idx):
        print(idx)

App()