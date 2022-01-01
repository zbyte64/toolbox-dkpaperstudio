from dkstudio.etsy import client
from dkstudio import shop_storage


def list_receipts(shop_id):
    return client.paginate(f"/application/shops/{shop_id}/receipts")


def main():
    from pprint import pprint
    import sys
    import time

    shop_id = sys.argv[1]

    start = time.time()
    for page in list_receipts(shop_id):
        pprint(page)
        
        for receipt in page['results']:
            shop_storage.persist('receipts', str(receipt['receipt_id']), receipt)
        # read 1 page every 5 seconds
        gap = time.time() - start
        tts = 5 - gap
        if tts > 0:
            time.sleep(tts)
        start = time.time()
