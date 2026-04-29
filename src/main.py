from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import bleach

from src.schemas import UserCreate

app = FastAPI(title="Corporate File Manager API")
templates = Jinja2Templates(directory="templates")

comments: list[str] = []

users_db = {
    "alice": {"username": "alice", "role": "user"},
    "bob": {"username": "bob", "role": "user"},
    "admin": {"username": "admin", "role": "admin"},
}

files_db = [
    {"id": 1, "filename": "report_alice.pdf", "owner": "alice", "size": 1024},
    {"id": 2, "filename": "photo_bob.jpg", "owner": "bob", "size": 2048},
    {"id": 3, "filename": "admin_keys.txt", "owner": "admin", "size": 12},
]


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


def get_current_user(request: Request) -> dict:
    username = request.headers.get("X-User")
    if not username or username not in users_db:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return users_db[username]


def check_file_permissions(file_id: int, user: dict = Depends(get_current_user)) -> dict:
    file = next((f for f in files_db if f["id"] == file_id), None)

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    is_owner = file["owner"] == user["username"]
    is_admin = user["role"] == "admin"

    if not (is_owner or is_admin):
        raise HTTPException(status_code=404, detail="File not found")

    return file


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


@app.get("/files/my")
def get_my_files(user: dict = Depends(get_current_user)) -> list[dict]:
    return [f for f in files_db if f["owner"] == user["username"]]


@app.get("/files/all")
def get_all_files(user: dict = Depends(get_current_user)) -> list[dict]:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return files_db


@app.get("/files/{file_id}")
def get_file(file: dict = Depends(check_file_permissions)) -> dict:
    return file


@app.delete("/files/{file_id}")
def delete_file(file: dict = Depends(check_file_permissions), user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin" and file["owner"] != user["username"]:
        raise HTTPException(status_code=404, detail="File not found")

    files_db.remove(file)
    return {"msg": "File deleted", "file_id": file["id"]}