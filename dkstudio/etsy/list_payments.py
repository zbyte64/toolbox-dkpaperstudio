from dkstudio.etsy import client
from dkstudio import shop_storage


def list_receipts(shop_id):
    return client.get(f"/application/shops/{shop_id}/receipts")


def main():
    from pprint import pprint

    pprint(list_receipts(shop_storage.get("ETSY_USER_ID")))
