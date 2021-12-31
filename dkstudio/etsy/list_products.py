from dkstudio.etsy import client
from dkstudio import shop_storage


def list_payments(shop_id):
    return client.get(f"/application/shops/{shop_id}/listings")


def main():
    from pprint import pprint

    pprint(list_payments(shop_storage.get("ETSY_USER_ID")))
