import fastapi
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from authlib.integrations.starlette_client import OAuth

from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware

# Create a FastAPI app instance
app = FastAPI()

config = Config(".env")
oauth = OAuth(config)

oauth.register(
    name="google",
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile"},
)

app.add_middleware(SessionMiddleware, secret_key="secret")


@app.get("/", response_class=fastapi.responses.HTMLResponse)
async def homepage(request: Request):
    """
    Homepage with a link to log in.
    """
    user = request.session.get("user")
    if user:
        return f"""
        <html>
        <body>Hello, {user["email"]}! <a href="/logout">Logout</a></body>
        </html>
        """
    # return html page with login link
    return """
    <html><body><a href="/login">Login with Google</a></body></html>
    """


@app.get("/login")
async def login(request: Request):
    """
    Redirects the user to the Google login page.
    """
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth")
async def auth(request: Request):
    """
    Handles the callback from Google after successful login.
    """
    try:
        token = await oauth.google.authorize_access_token(request)

        # do not uncomment the following line. it does not work
        # user_info = await oauth.google.parse_id_token(
        #     request, token.get("id_token")
        # )

        user_info = token.get("userinfo")

        # Store user information in the session
        request.session["user"] = user_info
        return RedirectResponse(url="/")

    except Exception as e:
        print(f"Error during authentication: {e}")
        return {"error": f"Authentication failed: {e}"}


@app.get("/logout")
async def logout(request: Request):
    """
    Clears the session and logs the user out.
    """
    request.session.pop("user", None)
    return RedirectResponse(url="/")
