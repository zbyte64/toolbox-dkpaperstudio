from tkinter import Button, Listbox, Tk, Toplevel, Label, StringVar, HORIZONTAL
from tkinter import messagebox
from tkinter.simpledialog import Dialog

from tkinter.ttk import Combobox, Progressbar
from typing import Iterable


def iterate_with_dialog(root: Tk, iterable: Iterable, maximum: int = None):
    """
    Present a dialog that iterates through a generator
    """
    t = Toplevel(root)
    status = Label(t, text="processing")
    bar = Progressbar(
        t,
        orient=HORIZONTAL,
        length=100,
        maximum=maximum,
        mode="indeterminate" if maximum is None else "determinate",
    )
    status.grid(row=0)
    bar.grid(row=1)
    bar.start()
    root.update()
    try:
        for msg in iterable:
            status["text"] = str(msg)
            bar.step(1)
            root.update()
    except Exception as e:
        messagebox.showerror("Unhandled exception", str(e))
    finally:
        t.destroy()


class ListDialog(Dialog):
    def __init__(self, title, prompt, items, parent=None):
        self.prompt = prompt
        self.items = items

        super().__init__(parent, title)

    def body(self, master):
        l = Label(master, text=self.prompt)
        l.pack()
        s = StringVar(master)
        self.string_var = s
        self.entry = Combobox(master, values=self.items, textvariable=s)
        self.entry.pack()
        return self.entry

    def validate(self):
        self.result = self.getresult()
        return 1

    def getresult(self):
        return self.entry.get()


def asklist(
    title: str,
    prompt: str,
    options: list[str],
    **kw,
):
    ld = ListDialog(title, prompt, options, **kw)
    return ld.result
