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
    name="gumroad",
    client_id=os.environ["GUMROAD_CLIENT_ID"],
    client_secret=os.environ["GUMROAD_CLIENT_SECRET"],
    access_token_url="https://api.gumroad.com/oauth/token",
    access_token_placement="uri",
    authorize_url="https://gumroad.com/oauth/authorize",
    api_base_url="https://api.gumroad.com/v2",
    client_kwargs={
        "scope": "view_profile edit_products view_sales",
    },
)

gumroad = oauth.create_client("gumroad")


@app.route("/login/gumroad")
async def login_via_gumroad(request):
    redirect_uri = request.url_for("authorize_gumroad")
    return await gumroad.authorize_redirect(
        request,
        redirect_uri,
    )


@app.route("/auth/gumroad")
async def authorize_gumroad(request):
    # fetch our API token
    redirect_uri = request.url_for("authorize_gumroad")
    authCode = request.query_params["code"]

    """
    # TODO async
    response = requests.post(
        "https://api.gumroad.com/oauth/token",
        json.dumps(
            {
                "grant_type": "authorization_code",
                "client_id": os.environ["GUMROAD_CLIENT_ID"],
                "redirect_uri": redirect_uri,
                "code": authCode,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    token = response.json()
    """
    # Etsy responds with: Invalid authorization header
    token = await gumroad.authorize_access_token(
        request,
        code=authCode,
        client_id=os.environ["GUMROAD_CLIENT_ID"],
    )
    # """
    print(token)
    if token.get("error"):
        if token in (
            {"error": "invalid_grant", "error_description": "code is expired"},
        ):
            return RedirectResponse(request.url_for("login_via_gumroad"))
        if token == {
            "error": "invalid_grant",
            "error_description": "code has been used previously",
        }:
            return RedirectResponse(request.url_for("login_via_gumroad"))
        raise RuntimeError(token.get("error"), token.get("error_description"))
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    user_id = access_token.split(".", 1)[0]
    shop_storage.update(
        {
            "GUMROAD_ACCESS_TOKEN": access_token,
            "GUMROAD_REFRESH_TOKEN": refresh_token,
            "GUMROAD_USER_ID": user_id,
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

    host = os.environ.get("GUMROAD_AUTH_HOST", "localhost")
    port = int(os.environ.get("GUMROAD_AUTH_PORT", 8000))
    webbrowser.open(f"http://{host}:{port}/login/gumroad")

    uvicorn.run("dkstudio.gumroad.authorize:app", host=host, port=port, reload=True)
