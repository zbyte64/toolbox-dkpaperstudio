import json
import os
import secrets
from authlib.integrations.starlette_client import OAuth
from authlib.oauth2.rfc7636 import create_s256_code_challenge
import requests
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.config import Config

from dkstudio import shop_storage

app = Starlette(debug=True)
app.add_middleware(
    SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "!secret")
)


config = Config(".env")
oauth = OAuth(config)

oauth.register(
    name="etsy",
    client_id=os.environ["ETSY_CLIENT_ID"],
    client_secret=os.environ["ETSY_CLIENT_SECRET"],
    access_token_url="https://api.etsy.com/v3/public/oauth/token",
    access_token_placement="uri",
    authorize_url="https://www.etsy.com/oauth/connect",
    api_base_url="https://openapi.etsy.com/v3",
    client_kwargs={
        "scope": "listings_r listings_w shops_r shops_w transactions_r email_r",
    },
)

etsy = oauth.create_client("etsy")


def get_code_verifier():
    return shop_storage.get("ETSY_CODE_VERIFIER", secrets.token_urlsafe(48))


def get_code_challenge():
    code_verifier = get_code_verifier()
    code_challenge = create_s256_code_challenge(code_verifier)
    return code_challenge


@app.route("/login/etsy")
async def login_via_etsy(request):
    redirect_uri = request.url_for("authorize_etsy")
    code_challenge = get_code_challenge()
    return await etsy.authorize_redirect(
        request,
        redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )


@app.route("/auth/etsy")
async def authorize_etsy(request):
    # fetch our API token
    code_verifier = get_code_verifier()
    redirect_uri = request.url_for("authorize_etsy")
    authCode = request.query_params["code"]

    # TODO async
    response = requests.post(
        "https://api.etsy.com/v3/public/oauth/token",
        json.dumps(
            {
                "grant_type": "authorization_code",
                "client_id": os.environ["ETSY_CLIENT_ID"],
                "redirect_uri": redirect_uri,
                "code": authCode,
                "code_verifier": code_verifier,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    token = response.json()
    """
    # Etsy responds with: Invalid authorization header
    token = await etsy.authorize_access_token(
        request,
        code_verifier=code_verifier,
        code=authCode,
        client_id=os.environ["ETSY_CLIENT_ID"],
    )
    """
    print(token)
    if token.get("error"):
        if token in (
            {"error": "invalid_grant", "error_description": "code is expired"},
        ):
            return RedirectResponse(request.url_for("login_via_etsy"))
        if token == {
            "error": "invalid_grant",
            "error_description": "code has been used previously",
        }:
            return RedirectResponse(request.url_for("login_via_etsy"))
        raise RuntimeError(token.get("error"), token.get("error_description"))
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
    return RedirectResponse(request.url_for("ready"))


@app.route("/ready")
async def ready(request):
    return HTMLResponse("ready")


def main():
    import logging
    import uvicorn
    import sys
    import webbrowser

    log = logging.getLogger("authlib")
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(logging.DEBUG)

    host = os.environ.get("ETSY_AUTH_HOST", "localhost")
    port = int(os.environ.get("ETSY_AUTH_PORT", 8000))
    webbrowser.open(f"http://{host}:{port}/login/etsy")

    uvicorn.run("dkstudio.etsy.authorize:app", host=host, port=port, reload=True)
