from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import bleach

from src.schemas import UserCreate

app = FastAPI(title="Corporate File Manager API")
templates = Jinja2Templates(directory="templates")

comments: list[str] = []


def clean_comment(text: str) -> str:
    return bleach.clean(
        text,
        tags=["b", "i", "u", "em", "strong"],
        attributes={},
        strip=True
    )


@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self';"
    return response


@app.post("/registration")
def registration(user: UserCreate) -> dict[str, str]:
    return {
        "msg": "User created",
        "user": user.username,
    }


@app.get("/comments")
def get_comments(request: Request):
    return templates.TemplateResponse(
        "comments.html",
        {
            "request": request,
            "comments": comments
        }
    )


@app.post("/comments")
def post_comments(text: str = Form(...)):
    safe_text = clean_comment(text)
    comments.append(safe_text)
    return RedirectResponse(url="/comments", status_code=303)