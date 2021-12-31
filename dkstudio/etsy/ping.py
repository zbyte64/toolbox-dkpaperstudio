import os
import requests


def ping():
    response = requests.get(
        "https://openapi.etsy.com/v3/application/openapi-ping",
        headers={
            "x-api-key": os.environ["ETSY_CLIENT_ID"],
        },
    )

    assert response.ok
    return response.json()


def main():
    from pprint import pprint

    pprint(ping())
