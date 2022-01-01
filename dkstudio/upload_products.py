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
    listing_ids = shop_storage.select_keys('products')
    lookups = {}
    for listing_id in listing_ids:
        product = shop_storage.select('products', listing_id)
        for sku in product.get('skus'):
            lookups[sku] = listing_id
            lookups[sku + ' Mug'] = listing_id
            lookups[sku + ' Mug Press'] = listing_id
    return lookups


def upload_product(shop_id, listing_id, zip_path):
    existing_files_response = client.get(f'/application/shops/{shop_id}/listings/{listing_id}/files')
    existing_files = existing_files_response['results']
    listing_file_id = None
    for ef in existing_files:
        if ef.get('filetype').upper() == 'ZIP':
            listing_file_id = ef['listing_file_id']
    filename = os.path.split(zip_path)[1]
    filep = open(zip_path, 'rb')
    upload_response = client.post(f'/application/shops/{shop_id}/listings/{listing_id}/files', data={'listing_file_id': listing_file_id, 'name': filename}, files={'file': filep})
    return upload_response

# UI routines

from tkinter import Button, Tk, HORIZONTAL

from tkinter.ttk import Progressbar
from tkinter.filedialog import askdirectory
from tkinter import messagebox
import threading


class PackageApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("[DKPS]Product Uploader")
        self.btn = Button(
            self,
            text="Upload Products",
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
            shop_id = os.environ['ETSY_SHOP_ID']
            if indir:
                self.progress.grid(row=1, column=0)
                self.progress.start()
                lookups = read_name_mapping_from_product_catalog()
                all_paths = find_project_dirs(indir)
                count = len(all_paths)
                assert len(all_paths), "Project files not found"
                for apath in all_paths:
                    self.progress.step(1)
                    if os.path.isdir(apath):
                        cwd, project_dir = os.path.split(apath)
                        zip_path = os.path.join(apath, project_dir + '.zip')
                        if not os.path.exists(zip_path):
                            messagebox.showwarning("warning", "Could not find zipfile for product '%s'" % product_name)
                            continue
                        product_name = project_dir.replace('_', ' ')
                        listing_id = lookups.get(product_name)
                        if not listing_id:
                            messagebox.showwarning("warning", "Could not find listing id for product '%s'" % product_name)
                            continue
                        upload_product(shop_id, listing_id, zip_path)
                self.progress.stop()
                self.progress.grid_forget()
                messagebox.showinfo("information", "Uploaded %s product(s)" % count)
            self.btn["state"] = "normal"

        self.btn["state"] = "disabled"
        threading.Thread(target=real_traitement).start()


def main():
    app = PackageApp()

    threading.Thread(target=app.traitement).start()
    app.mainloop()
