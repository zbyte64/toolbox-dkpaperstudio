from dkstudio.etsy import client


def list_products(shop_id):
    return client.paginate(f"/application/shops/{shop_id}/listings")


def main():
    from pprint import pprint
    import sys

    for p in list_products(sys.argv[1]):
        pprint(p)
