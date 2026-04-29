import uuid
from pathlib import Path

import bleach
import filetype
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

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

STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}


def clean_comment(text: str) -> str:
    return bleach.clean(
        text,
        tags=["b", "i", "u", "em", "strong"],
        attributes={},
        strip=True,
    )


@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self';"
    )
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
            "comments": comments,
        },
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
def delete_file(
    file: dict = Depends(check_file_permissions),
    user: dict = Depends(get_current_user),
) -> dict:
    if user["role"] != "admin" and file["owner"] != user["username"]:
        raise HTTPException(status_code=404, detail="File not found")

    files_db.remove(file)
    return {"msg": "File deleted", "file_id": file["id"]}


@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> dict:
    head = await file.read(2048)
    kind = filetype.guess(head)

    if kind is None or kind.mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG files are allowed")

    await file.seek(0)

    file_ext = ".jpg" if kind.mime == "image/jpeg" else ".png"
    physical_name = f"{uuid.uuid4()}{file_ext}"
    file_path = STORAGE_DIR / physical_name

    total_size = 0

    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    buffer.close()
                    if file_path.exists():
                        file_path.unlink()
                    raise HTTPException(status_code=413, detail="File is too large")

                buffer.write(chunk)

        new_file = {
            "id": max((f["id"] for f in files_db), default=0) + 1,
            "filename": file.filename,
            "original_name": file.filename,
            "owner": user["username"],
            "size": total_size,
            "path": str(file_path),
        }
        files_db.append(new_file)

        return {
            "msg": "File uploaded successfully",
            "file_id": new_file["id"],
            "original_name": new_file["original_name"],
            "stored_as": physical_name,
            "size": total_size,
        }

    finally:
        await file.close()


@app.get("/files/{file_id}/download")
def download_file(file: dict = Depends(check_file_permissions)):
    if "path" not in file or "original_name" not in file:
        raise HTTPException(status_code=404, detail="File is not available for download")

    file_path = Path(file["path"])

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=file["original_name"],
        media_type="application/octet-stream",
    )