from dkstudio.etsy import client
from dkstudio import shop_storage


def list_products(shop_id):
    return client.paginate(f"/application/shops/{shop_id}/listings")


def main():
    from pprint import pprint
    import sys

    for i, page in enumerate(list_products(sys.argv[1])):
        pprint(page)
        for p in page['results']:
            shop_storage.persist('products', str(p['listing_id']), p)
        print('page:', i)
        
