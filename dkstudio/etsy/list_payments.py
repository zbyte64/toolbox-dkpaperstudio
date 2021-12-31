from dkstudio.etsy import client


def list_receipts(shop_id):
    return client.get(f"/application/shops/{shop_id}/receipts")


def main():
    from pprint import pprint
    import sys

    pprint(list_receipts(sys.argv[1]))
