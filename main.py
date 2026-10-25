from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import sys
from typing import final
import json
import time
from tkinter import ttk


if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(app_dir)

DATA_DIR = os.path.join(app_dir, "data")
DATA_FILE = os.path.join(DATA_DIR, "data.json")
SAVE_DELAY_MS = 1000

FADE_COLORS = ("#030303","#0b0b0b", "#121212", "#1a1a1a", "#212121", "#292929", "#313131", "#3c3c3c", "#474747", "#565656", "#656565", "#7a7a7a", "#8f8f8f", "#9f9f9f", "#aeaeae", "#bcbcbc", "#cacaca") #, "#e7e7e7", "#ffffff"

TEXT_BAR_HEIGHT = 100

FRAME_MS = 8

BUTTON_SIZE = 50
SCROLLBAR_WIDTH = 16

THOUGHT_PAD_X = 12
THOUGHT_PAD_Y = 6
THOUGHT_BG = "#f0f0f0"

@final
class App:
    def __init__(self):
        self.root = Tk()
        self.root.option_add('*relief', 'flat')
        self.root.option_add('*font', ("JetBrainsMono NF ExtraLight", 12))

        self.root.title("Thinking Space")
        self.root.geometry("960x810")
        self.root.minsize(600, 400)
        self.root.update_idletasks()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.space_idx = -1

        self.text_bars = {}

        self.thoughts = {}

        self.thought_areas = {}

        self.containers = {} 

        self.space_rows = {}

        self.space_buttons = {}

        self.active_idx = None
        self.save_job = None

        self.menu = Frame(self.root, bg="light grey")
        self.menu.place(width=200, relheight=1)

        self.scroll_targets = []

        self.menu_label = Label(self.menu, text="Thinking Space", bg="#a8a8a8")
        self.menu_label.place(relwidth=1, width=-50, height=50)

        self.add_button = Button(self.menu, text="+", bg="#a8a8a8", highlightthickness=0, font=("Quilka", 24), command=self.new_space)
        self.add_button.place(relx=1, x=-50, width=50, height=50)

        self.menu_list = Frame(self.menu, bg="light grey")
        self.menu_list.place(y=50, relwidth=1, relheight=1, height=-50)

        self.menu_canvas = Canvas(self.menu_list, bg="light grey", highlightthickness=0, bd=0)
        self.menu_canvas.place(relwidth=1, relheight=1)

        self.menu_inner = Frame(self.menu_canvas, bg="light grey")
        menu_window = self.menu_canvas.create_window((0, 0), window=self.menu_inner, anchor="nw")
        self.menu_inner.bind("<Configure>",
                             lambda e: self.menu_canvas.configure(scrollregion=self.menu_canvas.bbox("all")))
        self.menu_canvas.bind("<Configure>",
                              lambda e: self.menu_canvas.itemconfigure(menu_window, width=e.width))
        self.register_scroll(self.menu_list, self.menu_canvas)

        self.space_frame = Frame(self.root)
        self.space_frame.place(x=200, relwidth=1, width=-200, relheight=1)

        self.welcome_label = Label(self.space_frame, text="Welcome!\nAdd a Space to begin.", justify=CENTER, font=("JetBrainsMono NF ExtraLight", 24))
        self.welcome_label.place(relwidth=1, relheight=1)

        self.root.bind("<Button-1>", self.on_click_anywhere)

        self.root.bind_all("<MouseWheel>", self.on_wheel)
        self.root.bind_all("<Button-4>", self.on_wheel)
        self.root.bind_all("<Button-5>", self.on_wheel)

        self.load()

        self.root.mainloop()

    def schedule_save(self):
        if self.save_job is not None:
            self.root.after_cancel(self.save_job)
        self.save_job = self.root.after(SAVE_DELAY_MS, self.save)

    def save(self):
        if self.save_job is not None:
            self.root.after_cancel(self.save_job)
            self.save_job = None

        order = sorted(self.thoughts)
        spaces = [{"thoughts": self.thoughts[i], "draft": self.text_bars[i].get("1.0", "end-1c")} for i in order]
        active = order.index(self.active_idx) if self.active_idx in order else None
        data = {"version": 1, "active": active, "spaces": spaces}

        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp_file = DATA_FILE + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_file, DATA_FILE)
        except OSError as e:
            print("could not save data:", e)

    def load(self):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                data = json.load(f)
            spaces = data["spaces"]
            active = data.get("active")
        except FileNotFoundError:
            return
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            try:
                os.replace(DATA_FILE, DATA_FILE + ".corrupt")
            except OSError:
                pass
            return

        if not isinstance(spaces, list) or not spaces:
            return

        for space in spaces:
            if not isinstance(space, dict):
                space = {}
            thoughts = [t for t in space.get("thoughts", []) if isinstance(t, str)]
            draft = space.get("draft", "")
            self.create_space(thoughts, draft if isinstance(draft, str) else "")

        if self.welcome_label is not None:
            self.welcome_label.destroy()
            self.welcome_label = None

        if not isinstance(active, int) or not 0 <= active <= self.space_idx:
            active = self.space_idx
        self.switch_space(active)

    def on_click_anywhere(self, event):
        if event.widget not in self.text_bars.values():
            self.root.focus_set()

    def on_close(self):
        self.save()
        self.root.destroy()

    def register_scroll(self, frame, canvas):
        self.scroll_targets.append((frame, canvas))

    def on_wheel(self, event):
        try:
            widget = self.root.winfo_containing(event.x_root, event.y_root)
        except KeyError:
            return

        if event.num == 4:
            pixels = -40
        elif event.num == 5:
            pixels = 40
        elif sys.platform == "darwin":
            pixels = -event.delta * 3
        else:
            pixels = -event.delta / 120 * 40

        while widget is not None:
            for frame, canvas in self.scroll_targets:
                if widget is frame:
                    self.scroll_canvas(canvas, pixels)
                    return
            widget = widget.master

    @staticmethod
    def scroll_canvas(canvas, pixels):
        bbox = canvas.bbox("all")
        if not bbox:
            return
        total = bbox[3] - bbox[1]
        view = canvas.winfo_height()
        if total <= view:
            return
        top = canvas.canvasy(0) - bbox[1]
        new_top = max(0, min(total - view, top + pixels))
        canvas.yview_moveto(new_top / total)

    def create_thought_area(self, i):
        """Scrollable list of sent thoughts for space i (sits above the text bar)."""
        frame = Frame(self.space_frame)

        canvas = Canvas(frame, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(frame, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        inner = Frame(canvas)
        window = canvas.create_window((0, 0), window=inner, anchor="nw")

        area = {"frame": frame, "canvas": canvas, "inner": inner, "labels": []}

        inner.bind("<Configure>",
                   lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))

        def on_canvas_resize(e, a=area, w=window):
            a["canvas"].itemconfigure(w, width=e.width)
            for lbl in a["labels"]:
                lbl.configure(wraplength=max(50, e.width - 4 * THOUGHT_PAD_X - 4))

        canvas.bind("<Configure>", on_canvas_resize)

        self.register_scroll(frame, canvas)

        self.thought_areas[i] = area
        return area

    def add_thought_label(self, index, contents):
        area = self.thought_areas[index]
        width = area["canvas"].winfo_width()
        lbl = Label(area["inner"], text=contents, bg=THOUGHT_BG, anchor="w",
                    justify=LEFT, wraplength=max(50, width - 4 * THOUGHT_PAD_X - 4),
                    padx=THOUGHT_PAD_X, pady=THOUGHT_PAD_Y)
        lbl.pack(fill=X, padx=THOUGHT_PAD_X, pady=(THOUGHT_PAD_Y, 0))
        area["labels"].append(lbl)

    def send(self, index, contents):
        contents = contents.strip()
        if not contents:
            return

        self.thoughts[index].append(contents)
        self.add_thought_label(index, contents)

        self.text_bars[index].delete("1.0", "end")
        area = self.thought_areas[index]
        area["canvas"].update_idletasks()
        area["canvas"].yview_moveto(1.0)

        self.save()

    def create_space(self, thoughts=None, draft=""):
        self.space_idx += 1
        idx = self.space_idx

        row = Frame(self.menu_inner, height=50)
        row.pack(fill=X)
        row.pack_propagate(False)

        button = Button(row, text=idx + 1)
        button.index = idx
        button["command"] = lambda i=idx: self.switch_space(i)
        button.place(relwidth=1, relheight=1, width=-30)

        delete_button = Button(row, text="×", command=lambda i=idx: self.delete_space(i))
        delete_button.place(relx=1, x=-30, relheight=1, width=30)

        self.space_rows[idx] = row
        self.space_buttons[idx] = button
        self.relabel_spaces()

        self.thoughts[idx] = []
        self.create_thought_area(idx)
        self.create_text_bar(idx)

        for thought in thoughts or []:
            self.thoughts[idx].append(thought)
            self.add_thought_label(idx, thought)

        if draft:
            self.text_bars[idx].insert("1.0", draft)
            self.text_bars[idx].mark_set("insert", "end-1c")

        return idx

    def delete_space(self, idx):
        if idx not in self.containers:
            return

        if not messagebox.askyesno("Delete space", "Delete this space and all its thoughts?"):
            return

        area_frame = self.thought_areas[idx]["frame"]
        widgets = (self.containers[idx], area_frame, self.space_rows.get(idx))
        self.scroll_targets = [t for t in self.scroll_targets if t[0] is not area_frame]

        for d in (self.containers, self.thought_areas, self.text_bars,
                  self.thoughts, self.space_rows, self.space_buttons):
            d.pop(idx, None)

        for w in widgets:
            if w is not None:
                w.destroy()

        self.relabel_spaces()

        if idx == self.active_idx:
            self.active_idx = None
            remaining = sorted(self.containers)
            if remaining:
                earlier = [i for i in remaining if i < idx]
                self.switch_space(earlier[-1] if earlier else remaining[0])
            else:
                self.welcome_label = Label(self.space_frame, text="Welcome!\nAdd a Space to begin.", justify=CENTER, font=("JetBrainsMono NF ExtraLight", 24))
                self.welcome_label.place(relwidth=1, relheight=1)

        self.save()

    def relabel_spaces(self):
        for n, i in enumerate(sorted(self.space_buttons), 1):
            self.space_buttons[i]["text"] = n

    def new_space(self):
        idx = self.create_space()

        if self.welcome_label is not None:
            self.welcome_label.lift(self.thought_areas[idx]["frame"])
            self.fade(self.welcome_label, 0)
            self.welcome_label = None

        self.switch_space(idx, animate=True)

    def fade(self, widget, value):
        if value < len(FADE_COLORS):
            widget["fg"] = FADE_COLORS[value]
            self.root.after(10, self.fade, widget, value + 1)
        else:
            widget.destroy()

    def create_text_bar(self, i):
        container = Frame(self.space_frame)

        text_bar = Text(container, borderwidth=0, font=("Arial", 14), wrap="word")
        text_bar.index_id = i

        text_bar.place(x=0, y=0, relheight=1, relwidth=1, width=-(BUTTON_SIZE + SCROLLBAR_WIDTH))

        scrollbar = ttk.Scrollbar(container, command=text_bar.yview)
        scrollbar.place(relx=1, x=-(BUTTON_SIZE + SCROLLBAR_WIDTH), y=0,
                        width=SCROLLBAR_WIDTH, relheight=1)
        text_bar.configure(yscrollcommand=scrollbar.set)

        keep_cursor_visible = lambda e, t=text_bar: t.after_idle(t.see, "insert")
        text_bar.bind("<KeyRelease>", keep_cursor_visible)
        text_bar.bind("<ButtonRelease-1>", keep_cursor_visible)
        text_bar.bind("<KeyRelease>", lambda e: self.schedule_save(), add="+")

        def send_shortcut(e, i=i):
            self.on_send_button(i)
            return "break"
        text_bar.bind("<Control-Return>", send_shortcut)

        button = Button(container, text="✓", command=lambda i=i: self.on_send_button(i))

        button.place(relx=1, rely=1, x=-BUTTON_SIZE, y=-BUTTON_SIZE,
                     width=BUTTON_SIZE, height=BUTTON_SIZE)

        button2 = Button(container, text="🗑", command=lambda i=i: self.on_erase_button(i))
        button2.place(relx=1, rely=1, x=-BUTTON_SIZE, y=-(BUTTON_SIZE*2),
                             width=BUTTON_SIZE, height=BUTTON_SIZE)

        self.text_bars[i] = text_bar
        self.containers[i] = container
        return text_bar

    def on_send_button(self, i):
        self.send(i, self.text_bars[i].get("1.0", "end-1c"))

    def on_erase_button(self, index):
        self.text_bars[index].delete("1.0", "end")

    def switch_space(self, idx, animate=False):
        if idx == self.active_idx or idx not in self.text_bars:
            return

        if self.active_idx is not None:
            self.containers[self.active_idx].place_forget()
            self.thought_areas[self.active_idx]["frame"].place_forget()

        self.active_idx = idx
        widget = self.containers[idx]

        self.thought_areas[idx]["frame"].place(x=0, y=0, relwidth=1, relheight=1,
                                               height=-TEXT_BAR_HEIGHT)

        if animate:
            widget.place(x=0, rely=1, y=TEXT_BAR_HEIGHT, relwidth=1,
                         height=TEXT_BAR_HEIGHT, anchor="sw")
            self.reveal(widget, 0)
        else:
            widget.place(x=0, rely=1, y=0, relwidth=1,
                         height=TEXT_BAR_HEIGHT, anchor="sw")

        self.text_bars[idx].focus_set()

        area = self.thought_areas[idx]
        if not area.get("positioned"):
            area["positioned"] = True
            self.root.after(50, lambda c=area["canvas"]: c.winfo_exists() and c.yview_moveto(1.0))

        self.schedule_save()

    def reveal(self, widget, value):
        if self.containers.get(self.active_idx) is not widget:
            return
        steps = 120
        if value < steps:
            progress = (value + 1) / steps
            eased = 1 - (1 - progress) ** 2
            widget.place_configure(y=round(TEXT_BAR_HEIGHT * (1 - eased)))
            self.root.after(5, self.reveal, widget, value + 1)

App()