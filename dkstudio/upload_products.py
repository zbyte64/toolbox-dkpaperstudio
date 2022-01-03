import glob
import os
from dkstudio import shop_storage
from dkstudio.etsy import client
from dkstudio.etsy.list_products import populate_product_catalog

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
    print("known listing_ids", listing_ids)
    lookups = {}
    for listing_id in listing_ids:
        product = shop_storage.select("products", listing_id)
        assert product, listing_id
        tags = set(map(lambda x: x.lower(), product.get("tags")))
        is_mug_press = "cricut mug press svg" in tags
        for sku in product.get("skus"):
            lookups[sku] = listing_id
            if is_mug_press:
                lookups[sku + " Mug"] = listing_id
                lookups[sku + " Mug Press"] = listing_id
        lookups[product["title"]] = listing_id
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
        if ef.get("filetype") == "application/zip":
            listing_file_id = ef["listing_file_id"]
    filename = os.path.split(zip_path)[1]
    print("uploading", zip_path)
    filep = open(zip_path, "rb")
    try:
        upload_response = client.post(
            f"/application/shops/{shop_id}/listings/{listing_id}/files",
            data={"name": filename},
            files={"file": (filename, filep, "application/zip")},
        )
    except Exception as e:
        if listing_file_id:
            if (
                e.args[0]
                == f"File {listing_file_id} is already attached to this listing."
            ):
                messagebox.showinfo(
                    "Zipfile already uploaded", f"{filename} is already uploaded"
                )
                return False
        raise
    if listing_file_id:
        print("Removing previous zipfile")
        client.delete(
            f"/application/shops/{shop_id}/listings/{listing_id}/files/{listing_file_id}"
        )
    return upload_response


# UI routines

from tkinter import Button, Tk

from tkinter.filedialog import askdirectory, askopenfilename
from tkinter import messagebox

from dkstudio.ux import iterate_with_dialog


def find_zip_paths(project_dirs):
    for apath in project_dirs:
        cwd, project_dir = os.path.split(apath)
        zip_file = os.path.join(apath, project_dir + ".zip")
        if os.path.isfile(zip_file):
            yield zip_file
        else:
            messagebox.showerror(
                "Could not find product file", "Zip file not found %s" % zip_file
            )


class PackageApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("[DKPS]Product Uploader")
        self.select_folder_btn = Button(
            self,
            text="Upload from Project Folder",
            command=self.select_folder,
            bg="black",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.select_folder_btn.grid(row=0, column=0, padx=5, pady=5)
        self.select_workspace_btn = Button(
            self,
            text="Upload from Workspace Folder",
            command=self.select_workspace,
            bg="black",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.select_workspace_btn.grid(row=1, column=0, padx=5, pady=5)
        self.select_zipfile_btn = Button(
            self,
            text="Upload Product Zipfile",
            command=self.select_zipfile,
            bg="black",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.select_zipfile_btn.grid(row=2, column=0, padx=5, pady=5)
        self.sync_product_catalog_btn = Button(
            self,
            text="Sync Product Catalog",
            command=self.sync_product_catalog,
            bg="black",
            fg="black",
            highlightbackground="#3E4149",
        )
        self.sync_product_catalog_btn.grid(row=3, column=0, padx=5, pady=5)
        self.lookups = read_name_mapping_from_product_catalog()
        self.shop_id = os.environ["ETSY_SHOP_ID"]

    def sync_product_catalog(self):
        iterate_with_dialog(
            self, map(lambda p: p.get("title"), populate_product_catalog(self.shop_id))
        )
        self.lookups = read_name_mapping_from_product_catalog()
        messagebox.showinfo(
            "Updated product catalog", "%s products on file" % len(self.lookups)
        )

    def select_workspace(self):
        self.select_workspace_btn["state"] = "disabled"
        try:
            indir = askdirectory(
                initialdir=shop_storage.get("workspace_path", os.getcwd()),
                mustexist=True,
                title="Select Workspace",
            )
            if indir:
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
                zip_paths = find_zip_paths(all_paths)
                iterate_with_dialog(self, map(self.upload_product, zip_paths), count)
                messagebox.showinfo("Done", "Uploaded %s product(s)" % count)
                shop_storage.set("workspace_path", indir)
        finally:
            self.select_workspace_btn["state"] = "normal"

    def select_folder(self):
        self.select_folder_btn["state"] = "disabled"
        try:
            indir = askdirectory(
                initialdir=shop_storage.get("workspace_path", os.getcwd()),
                mustexist=True,
                title="Select Project Folder",
            )
            if indir:
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
                zip_paths = find_zip_paths(all_paths)
                iterate_with_dialog(
                    self, map(self.upload_product_with_message, zip_paths), count
                )
        finally:
            self.select_folder_btn["state"] = "normal"

    def select_zipfile(self):
        self.select_zipfile_btn["state"] = "disabled"
        try:
            zip_path = askopenfilename(
                title="Select Product Zipfile",
                initialdir=shop_storage.get("workspace_path", os.getcwd()),
                filetypes=[("Zip files", ".zip")],
            )
            if zip_path:
                iterate_with_dialog(
                    self, map(self.upload_product_with_message, [zip_path])
                )
        finally:
            self.select_zipfile_btn["state"] = "normal"

    def upload_product_with_message(self, zip_path):
        product_name = self.upload_product(zip_path)
        if product_name:
            messagebox.showinfo("Done", "Uploaded %s" % product_name)
        return product_name

    def upload_product(self, zip_path):
        _, project_filename = os.path.split(zip_path)

        product_name = project_filename[: -len(".zip")].replace("_", " ")
        listing_id = self.lookups.get(product_name)
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
        if upload_product(self.shop_id, listing_id, zip_path) is False:
            return
        return product_name


def main():
    app = PackageApp()

    app.mainloop()
