from tkinter import Tk, Toplevel, Label, HORIZONTAL
from tkinter import messagebox

from tkinter.ttk import Progressbar
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
