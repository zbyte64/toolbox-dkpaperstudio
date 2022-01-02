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

from tkinter import Button, Tk

from tkinter.filedialog import askdirectory
from tkinter import messagebox

from dkstudio.ux import iterate_with_dialog


class PackageApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("[DKPS]Product Packager")
        self.package_folder_btn = Button(
            self,
            text="Select Project Folder",
            command=self.package_folder,
            bg="blue",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.package_workspace_btn = Button(
            self,
            text="Select Workspace Folder",
            command=self.package_workspace,
            bg="blue",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.package_folder_btn.grid(row=0, column=0, padx=5, pady=5)
        self.package_workspace_btn.grid(row=1, column=0, padx=5, pady=5)

    def package_workspace(self):
        self.package_workspace_btn["state"] = "disabled"
        try:
            indir = askdirectory(initialdir=os.getcwd(), mustexist=True)
            if indir:
                all_paths = find_product_dirs(indir)
                count = len(all_paths)
                confirm = messagebox.askokcancel(
                    "Projects found", f"Found {count} projects"
                )
                if not confirm:
                    return
                iterate_with_dialog(self, map(self.package_product, all_paths), count)
                messagebox.showinfo("information", "Packaged %s product(s)" % count)
        finally:
            self.package_workspace_btn["state"] = "normal"

    def package_folder(self):
        self.package_folder_btn["state"] = "disabled"
        try:
            indir = askdirectory(initialdir=os.getcwd(), mustexist=True)
            if indir:
                all_paths = find_product_dirs(indir)
                count = len(all_paths)
                if count != 1:
                    messagebox.showerror("error", "Could not find product folder")
                    return

                iterate_with_dialog(
                    self, map(self.package_product_with_message, all_paths), count
                )
        finally:
            self.package_folder_btn["state"] = "normal"

    def package_product(self, apath):
        if not os.path.isdir(apath):
            messagebox.showerror("invalid path", "Path is not a directory %s" % apath)
            return
        cwd, product_dir = os.path.split(apath)
        product_name = product_dir[: -len("_FILES")]
        filename = product_name + ".zip"
        package_product(cwd, product_dir, filename)
        return filename

    def package_product_with_message(self, apath):
        filename = self.package_product(apath)
        messagebox.showinfo("information", "Packaged %s" % filename)
        return filename


def main():
    app = PackageApp()
    app.mainloop()
