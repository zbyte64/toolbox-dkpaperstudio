import time
import glob
import os
from dkstudio import shop_storage
from dkstudio.package_products import package_product
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
from tkinter.ttk import Style

from dkstudio.ux import iterate_with_dialog, asklist


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


class EtsyWorkflow:
    @staticmethod
    def associate_product_dir_with_listing(product_folder: str, config: dict):
        shop_storage.write_file_metadata(product_folder, config)
        shop_storage.persist(
            "etsy-product-dir", config["etsy_listing_id"], product_folder
        )

    @staticmethod
    def get_unmapped_products():
        listing_ids = filter(
            lambda listing_id: shop_storage.select("etsy-product-dir", listing_id)
            is None,
            shop_storage.select_keys("products"),
        )
        available_listings = [
            shop_storage.select("products", listing_id) for listing_id in listing_ids
        ]
        return available_listings


class PackageApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("[DKPS]Product Uploader")
        self.select_folder_btn = Button(
            self,
            text="Upload from Project Folder",
            command=self.select_folder,
        )
        self.select_folder_btn.grid(row=0, column=0, padx=5, pady=5)
        self.select_workspace_btn = Button(
            self,
            text="Upload from Workspace Folder",
            command=self.select_workspace,
        )
        self.select_workspace_btn.grid(row=1, column=0, padx=5, pady=5)
        self.select_zipfile_btn = Button(
            self,
            text="Upload Product Zipfile",
            command=self.select_zipfile,
        )
        self.select_zipfile_btn.grid(row=2, column=0, padx=5, pady=5)
        self.sync_product_catalog_btn = Button(
            self,
            text="Sync Product Catalog",
            command=self.sync_product_catalog,
        )
        self.sync_product_catalog_btn.grid(row=3, column=0, padx=5, pady=5)
        self.lookups = read_name_mapping_from_product_catalog()
        self.shop_id = os.environ["ETSY_SHOP_ID"]

    def sync_product_catalog(self):
        iterate_with_dialog(
            self, map(lambda p: p.get("title"), populate_product_catalog(self.shop_id))
        )
        self.lookups = read_name_mapping_from_product_catalog()

        workspace_dir = askdirectory(
            initialdir=shop_storage.get("workspace_path", os.getcwd()),
            mustexist=True,
            title="Select Workspace",
        )
        product_folders = glob.glob(os.path.join(workspace_dir, "*", "*_FILES"))
        listing_ids = set(shop_storage.select_keys("products"))
        to_resolve = []
        for product_folder in product_folders:
            config = shop_storage.read_file_metadata(product_folder, {})
            product_name = os.path.split(product_folder)[1][: -len("_FILES")].replace(
                "_", " "
            )
            if "etsy_listing_id" in config and config["etsy_listing_id"] in listing_ids:
                listing_ids.remove(config["etsy_listing_id"])
                continue
            if "product_name" not in config:
                config["product_name"] = product_name
            if product_name in self.lookups:
                config["etsy_listing_id"] = self.lookups[product_name]
                EtsyWorkflow.associate_product_dir_with_listing(product_folder, config)
            else:
                # select on of...
                to_resolve.append((config, product_folder))
            shop_storage.write_file_metadata(product_folder, config)
        available_listings = [
            shop_storage.select("products", listing_id) for listing_id in listing_ids
        ]
        for (config, product_folder) in to_resolve:
            product_name = config["product_name"]
            options = [av["title"] for av in available_listings]
            index = asklist(
                "Please map product",
                f'Which esty product is "{product_name}"?',
                options,
            )
            if index is not None:
                config["etsy_listing_id"] = available_listings.pop(index)["listing_id"]
                EtsyWorkflow.associate_product_dir_with_listing(product_folder, config)

        messagebox.showinfo(
            "Updated product catalog", "Mapped %s products" % len(product_folders)
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
        product_dir, project_filename = os.path.split(zip_path)
        product_src = os.path.join(
            product_dir, os.path.splitext(project_filename)[0] + "_FILES"
        )
        if not os.path.exists(product_src):
            messagebox.showwarning(
                "warning",
                "Could not find product directory '%s', skipped product upload"
                % product_src,
            )
            return
        metadata = shop_storage.read_file_metadata(product_src)
        if not metadata:
            available_listings = EtsyWorkflow.get_unmapped_products()
            product_name = project_filename.splate("_", " ")
            metadata = config = {"product_name": product_name}
            options = [av["title"] for av in available_listings]
            index = asklist(
                "Please map product",
                f'Which esty product is "{product_name}"?',
                items=options,
            )
            if index is not None:
                config["etsy_listing_id"] = available_listings.pop(index)["listing_id"]
                EtsyWorkflow.associate_product_dir_with_listing(product_src, config)
            else:
                messagebox.showwarning(
                    "warning",
                    "Could not find product metadata for '%s', skipped product upload"
                    % product_src,
                )
                return

        zip_modified_time = os.path.getmtime(zip_path)
        if zip_modified_time < os.path.getmtime(product_src):
            zip_response = messagebox.askyesnocancel(
                "Zipfile is stale:",
                f"Product '{product_name}' has been modified since the zipfile has been created, should we update the zipfile?",
            )
            if zip_response is None:
                return
            if zip_response:
                # update zip
                package_product(product_dir, product_src, zip_path)
                zip_modified_time = os.path.getmtime(zip_path)

        last_upload = metadata.get("last_upload")
        if last_upload is not None and last_upload >= zip_modified_time:
            confirm = messagebox.askokcancel(
                "Product is already up to date",
                f"Product '{product_name}' has an upload timestamp newer than the zipfile, continue with upload?",
            )
            if not confirm:
                return

        listing_id = metadata.get("etsy_listing_id", None)
        product_name = metadata.get("product_name", None)

        if not listing_id:
            messagebox.showwarning(
                "warning",
                f"Could not find listing id for product {product_name} '{listing_id}', skipped product upload",
            )
            return
        confirm = messagebox.askokcancel(
            "Product Listing Found",
            f"Product '{product_name}' found on etsy: '{listing_id}', continue with upload?",
        )
        if not confirm:
            return
        if upload_product(self.shop_id, listing_id, zip_path) is False:
            return
        metadata["last_upload"] = zip_modified_time
        shop_storage.write_file_metadata(product_src, metadata)
        return product_name


def main():
    app = PackageApp()
    s = Style(app)
    if "aqua" in s.theme_names():
        s.theme_use("aqua")

    app.mainloop()
