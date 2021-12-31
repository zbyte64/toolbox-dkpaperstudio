#!/usr/bin/env python3

import glob
import os
import subprocess

# functions for packaging up products

COMMAND = "zip -r {destination} {source} -X"


def package_product(cwd, source, destination):
    """
    Zip up a product folder without hidden/system files
    """
    cmd = COMMAND.format(destination=destination, source=source)
    more_hidden_files = glob.glob(os.path.join(cwd, source, "**/.*"), recursive=True)
    if more_hidden_files:
        more_hidden_files = [path[len(cwd) :] for path in more_hidden_files]
        exclude_options = " -x ".join(more_hidden_files)
        cmd = cmd + " -x " + exclude_options
    print(cmd)
    return subprocess.call(cmd, cwd=cwd, shell=True)


def find_product_dirs(indir):
    if indir.endswith("_FILES"):
        all_paths = [indir]
    else:
        search = "*_FILES"
        for i in range(2):
            all_paths = glob.glob(os.path.join(indir, search))
            if len(all_paths):
                break
            else:
                search = "*/" + search
    return all_paths


# UI routines

from tkinter import Button, Tk, HORIZONTAL

from tkinter.ttk import Progressbar
from tkinter.filedialog import askdirectory
from tkinter import messagebox
import threading


class PackageApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("[DKPS]Product Packager")
        self.btn = Button(
            self,
            text="Package Products",
            command=self.traitement,
            bg="blue",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.btn.grid(row=0, column=0)
        self.progress = Progressbar(
            self, orient=HORIZONTAL, length=100, mode="indeterminate"
        )

    def traitement(self):
        def real_traitement():
            indir = askdirectory(initialdir=os.getcwd(), mustexist=True)
            if indir:
                self.progress.grid(row=1, column=0)
                self.progress.start()
                all_paths = find_product_dirs(indir)
                count = len(all_paths)
                assert len(all_paths), "Project files not found"
                for apath in all_paths:
                    if os.path.isdir(apath):
                        cwd, product_dir = os.path.split(apath)
                        product_name = product_dir[: -len("_FILES")]
                        package_product(cwd, product_dir, product_name + ".zip")
                        self.progress.step(1)
                self.progress.stop()
                self.progress.grid_forget()
                messagebox.showinfo("information", "Packaged %s product(s)" % count)
            self.btn["state"] = "normal"

        self.btn["state"] = "disabled"
        threading.Thread(target=real_traitement).start()


def main():
    app = PackageApp()

    threading.Thread(target=app.traitement).start()
    app.mainloop()
