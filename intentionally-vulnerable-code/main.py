from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Hard-coded secret key for sessions (intentional vulnerability)
app.add_middleware(SessionMiddleware, secret_key="hard-coded-secret-key-12345")

# Intentionally exposed API key to demonstrate secret leakage
HARDCODED_API_KEY = "sk_live_ABC1234567890SECRET"

templates = Jinja2Templates(directory="templates")


@app.get("/home", response_class=HTMLResponse)
async def home_get(request: Request) -> HTMLResponse:
    next_url = request.query_params.get("next")
    if next_url:
        try:
            return RedirectResponse(url=next_url)
        except Exception:
            return templates.TemplateResponse(
                "home.html",
                {
                    "request": request,
                    "search_term": None,
                    "error_message": "Unable to redirect to the requested location.",
                },
            )

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "search_term": None,
            "error_message": None,
        },
    )


@app.post("/home", response_class=HTMLResponse)
async def home_post(request: Request) -> HTMLResponse:
    search_term = None
    error_message = None

    try:
        form = await request.form()
        search_term = form.get("search")
    except Exception:
        error_message = "We couldn't process your search submission."

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "search_term": search_term,
            "error_message": error_message,
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request) -> HTMLResponse:
    redirect_target = request.query_params.get("next", "/secret")

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "message": None,
            "redirect_target": redirect_target,
        },
    )


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request) -> HTMLResponse:
    redirect_target = request.query_params.get("next", "/secret")
    try:
        form = await request.form()
    except Exception:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "message": "Unable to process your submission.",
                "redirect_target": redirect_target,
            },
        )

    provided_code = form.get("code", "")
    redirect_target = form.get("next", redirect_target)
    today_code = datetime.now(timezone.utc).strftime("%y%m%d")

    if provided_code == today_code:
        request.session["authenticated"] = True
        return RedirectResponse(url=redirect_target, status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "message": "Incorrect code.",
            "redirect_target": redirect_target,
        },
    )


@app.get("/secret", response_class=HTMLResponse)
async def secret(request: Request) -> HTMLResponse:
    if not request.session.get("authenticated"):
        return RedirectResponse(url=f"/login", status_code=302)
    request.session.pop("authenticated", None)

    return templates.TemplateResponse(
        "secret.html",
        {
            "request": request,
        },
    )


@app.get("/secrets")
async def secrets() -> PlainTextResponse:
    return PlainTextResponse("This is yet another page with secret information that needs to be behind authentication!")
