import glob
import os
from dkstudio import shop_storage
from dkstudio.etsy import client

# functions for finding an uploading products


def find_project_dirs(indir):
    # project dir contains an _FILES product folder
    # TODO: and a zip file
    search = "*_FILES"
    for i in range(2):
        all_paths = glob.glob(os.path.join(indir, search))
        if len(all_paths):
            return [os.path.split(p)[0] for p in all_paths]
        else:
            search = "*/" + search
    return None


def read_name_mapping_from_product_catalog():
    listing_ids = shop_storage.select_keys("products")
    lookups = {}
    for listing_id in listing_ids:
        product = shop_storage.select("products", listing_id)
        assert product, listing_id
        tags = set(product.get("tags"))
        is_mug_press = "Cricut Mug Press SVG" in tags or "Cricut Mug Press svg" in tags
        for sku in product.get("skus"):
            lookups[sku] = listing_id
            if is_mug_press:
                lookups[sku + " Mug"] = listing_id
                lookups[sku + " Mug Press"] = listing_id
    return lookups


def upload_product(shop_id, listing_id, zip_path):
    existing_files_response = client.get(
        f"/application/shops/{shop_id}/listings/{listing_id}/files"
    )
    existing_files = existing_files_response["results"]
    print("Existing files:")
    print(existing_files)
    listing_file_id = None
    for ef in existing_files:
        if ef.get("filetype").upper().endswith("ZIP"):
            listing_file_id = ef["listing_file_id"]
    filename = os.path.split(zip_path)[1]
    filep = open(zip_path, "rb")
    upload_response = client.post(
        f"/application/shops/{shop_id}/listings/{listing_id}/files",
        data={"listing_file_id": listing_file_id, "name": filename}
        if listing_file_id is not None
        else {"name": filename},
        files={"file": filep},
    )
    return upload_response


# UI routines

from tkinter import Button, Tk, HORIZONTAL

from tkinter.ttk import Progressbar
from tkinter.filedialog import askdirectory, askopenfilename
from tkinter import messagebox


class PackageApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("[DKPS]Product Uploader")
        self.select_folder_btn = Button(
            self,
            text="Select Project Folder",
            command=self.select_folder,
            bg="black",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.select_folder_btn.grid(row=0, column=0, padx=5, pady=5)
        self.select_workspace_btn = Button(
            self,
            text="Select Workspace Folder",
            command=self.select_workspace,
            bg="black",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.select_workspace_btn.grid(row=1, column=0, padx=5, pady=5)
        self.select_zipfile_btn = Button(
            self,
            text="Select Product Zipfile",
            command=self.select_zipfile,
            bg="black",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.select_zipfile_btn.grid(row=2, column=0, padx=5, pady=5)
        self.progress = Progressbar(
            self, orient=HORIZONTAL, length=100, mode="indeterminate"
        )

    def select_workspace(self):
        self.select_workspace_btn["state"] = "disabled"
        try:
            indir = askdirectory(
                initialdir=os.getcwd(), mustexist=True, title="Select Workspace"
            )
            shop_id = os.environ["ETSY_SHOP_ID"]
            if indir:
                self.progress.grid(row=3, column=0)
                self.progress.start()
                lookups = read_name_mapping_from_product_catalog()
                all_paths = find_project_dirs(indir)
                if not all_paths:
                    messagebox.showerror(
                        "Project files not found", "Project files not found"
                    )
                    return
                count = len(all_paths)
                confirm = messagebox.askokcancel(
                    "Projects found", f"Found {count} projects, continue with upload?"
                )
                if not confirm:
                    return
                for apath in all_paths:
                    self.progress.step(1)
                    if os.path.isdir(apath):
                        cwd, project_dir = os.path.split(apath)
                        zip_path = os.path.join(apath, project_dir + ".zip")
                        if not os.path.exists(zip_path):
                            messagebox.showwarning(
                                "warning",
                                "Could not find zipfile for product '%s'" % project_dir,
                            )
                            continue
                        product_name = project_dir.replace("_", " ")
                        listing_id = lookups.get(product_name)
                        if not listing_id:
                            messagebox.showwarning(
                                "warning",
                                "Could not find listing id for product '%s'"
                                % product_name,
                            )
                            continue
                        upload_product(shop_id, listing_id, zip_path)
                messagebox.showinfo("Done", "Uploaded %s product(s)" % count)
        finally:
            self.progress.stop()
            self.progress.grid_forget()
            self.select_workspace_btn["state"] = "normal"

    def select_folder(self):
        self.select_folder_btn["state"] = "disabled"
        try:
            indir = askdirectory(
                initialdir=os.getcwd(), mustexist=True, title="Select Project Folder"
            )
            shop_id = os.environ["ETSY_SHOP_ID"]
            if indir:
                self.progress.grid(row=3, column=0)
                self.progress.start()
                lookups = read_name_mapping_from_product_catalog()
                all_paths = find_project_dirs(indir)
                if not all_paths:
                    messagebox.showerror(
                        "Project files not found", "Project files not found"
                    )
                    return
                count = len(all_paths)
                if not count == 1:
                    messagebox.showerror(
                        "Project files not found", "Project files not found"
                    )
                    return
                for apath in all_paths:
                    self.progress.step(1)
                    if os.path.isdir(apath):
                        project_dir = os.path.split(apath)[1]
                        zip_path = os.path.join(apath, project_dir + ".zip")
                        if not os.path.exists(zip_path):
                            messagebox.showwarning(
                                "warning",
                                "Could not find zipfile for product '%s'" % project_dir,
                            )
                            continue
                        product_name = project_dir.replace("_", " ")
                        listing_id = lookups.get(product_name)
                        if not listing_id:
                            messagebox.showwarning(
                                "warning",
                                "Could not find listing id for product '%s'"
                                % product_name,
                            )
                            continue
                        confirm = messagebox.askokcancel(
                            "Product Listing Found",
                            "Product found on etsy, continue with upload?",
                        )
                        if not confirm:
                            return
                        upload_product(shop_id, listing_id, zip_path)
                        messagebox.showinfo("Done", "Uploaded %s" % product_name)
        finally:
            self.progress.stop()
            self.progress.grid_forget()
            self.select_folder_btn["state"] = "normal"

    def select_zipfile(self):
        self.select_zipfile_btn["state"] = "disabled"
        try:
            zip_path = askopenfilename(
                title="Select Product Zipfile",
                initialdir=os.getcwd(),
                filetypes=[("Zip files", ".zip")],
            )
            shop_id = os.environ["ETSY_SHOP_ID"]
            if zip_path:
                self.progress.grid(row=3, column=0)
                self.progress.start()
                lookups = read_name_mapping_from_product_catalog()

                self.progress.step(1)
                _, project_filename = os.path.split(zip_path)

                product_name = project_filename[: -len(".zip")].replace("_", " ")
                listing_id = lookups.get(product_name)
                if not listing_id:
                    messagebox.showwarning(
                        "warning",
                        "Could not find listing id for product '%s'" % product_name,
                    )
                    return
                confirm = messagebox.askokcancel(
                    "Product Listing Found",
                    "Product found on etsy, continue with upload?",
                )
                if not confirm:
                    return
                upload_product(shop_id, listing_id, zip_path)
                messagebox.showinfo("Done", "Uploaded %s" % product_name)
        finally:
            self.progress.stop()
            self.progress.grid_forget()
            self.select_zipfile_btn["state"] = "normal"


def main():
    app = PackageApp()

    app.mainloop()
