import os
import requests


from dkstudio import shop_storage


def refresh_token():
    refresh_token = shop_storage.get("ETSY_REFRESH_TOKEN")
    # TODO async
    response = requests.post(
        "https://api.etsy.com/v3/public/oauth/token",
        {
            "grant_type": "refresh_token",
            "client_id": os.environ["ETSY_CLIENT_ID"],
            "refresh_token": refresh_token,
        },
    )
    if not response.ok:
        m = response.json()
        raise RuntimeError(m.get("error"), m.get("error_description"))
    token = response.json()
    print(token)
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    user_id = access_token.split(".", 1)[0]
    shop_storage.update(
        {
            "ETSY_ACCESS_TOKEN": access_token,
            "ETSY_REFRESH_TOKEN": refresh_token,
            "ETSY_USER_ID": user_id,
        }
    )


def get(path):
    access_token = shop_storage.get("ETSY_ACCESS_TOKEN")
    assert access_token
    api_key = os.environ["ETSY_CLIENT_ID"]
    url = f"https://openapi.etsy.com/v3/{path}"
    response = requests.get(
        url, headers={"x-api-key": api_key, "Authorization": f"Bearer {access_token}"}
    )
    message = response.json()
    if not response.ok:
        if message == {
            "error": "invalid_token",
            "error_description": "access token is expired",
        }:
            refresh_token()
            return get(path)
        else:
            raise RuntimeError(message.get("error"), message.get("error_description"))
    return message
