from __future__ import annotations

import uuid
from pathlib import Path
from secrets import token_hex

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.dependencies.auth import get_current_user
from src.models import User
from src.models.media_file import MediaFile
from src.schemas.media import CardMediaUploadResponse, MediaUploadResponse

router = APIRouter(prefix="/media", tags=["media"])

ALLOWED_MEDIA_PREFIXES = ("image/", "audio/")
MEDIA_STORAGE_DIR = Path(__file__).resolve().parents[3] / "uploads"


def _build_media_url(media_id: uuid.UUID) -> str:
    return f"/media/{media_id}"


def _validate_content_type(upload: UploadFile) -> str:
    content_type = upload.content_type or ""
    if not any(content_type.startswith(prefix) for prefix in ALLOWED_MEDIA_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image and audio uploads are supported",
        )
    return content_type


async def _store_upload(session: AsyncSession, upload: UploadFile) -> MediaFile:
    filename = Path(upload.filename or "upload.bin").name
    content_type = _validate_content_type(upload)

    MEDIA_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    suffix = Path(filename).suffix
    stored_name = f"{uuid.uuid4()}_{token_hex(8)}{suffix}"
    stored_path = MEDIA_STORAGE_DIR / stored_name

    try:
        with stored_path.open("wb") as target:
            while chunk := await upload.read(1024 * 1024):
                target.write(chunk)
    finally:
        await upload.close()

    media = MediaFile(
        filename=filename,
        content_type=content_type,
        path=str(stored_path),
    )
    session.add(media)
    await session.commit()
    await session.refresh(media)
    return media


def _to_upload_response(media: MediaFile) -> MediaUploadResponse:
    return MediaUploadResponse(
        id=media.id,
        filename=media.filename,
        content_type=media.content_type,
        url=_build_media_url(media.id),
        created_at=media.created_at,
    )


@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    media = await _store_upload(session, file)
    return _to_upload_response(media)


@router.post("/upload/card-assets", response_model=CardMediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_card_assets(
    front_image: UploadFile | None = File(default=None),
    front_audio: UploadFile | None = File(default=None),
    back_image: UploadFile | None = File(default=None),
    back_audio: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uploads = {
        "front_image": front_image,
        "front_audio": front_audio,
        "back_image": back_image,
        "back_audio": back_audio,
    }

    if all(upload is None for upload in uploads.values()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one file is required")

    results: dict[str, MediaUploadResponse | None] = {}
    for field_name, upload in uploads.items():
        results[field_name] = None if upload is None else _to_upload_response(await _store_upload(session, upload))

    return CardMediaUploadResponse(**results)


@router.get("/{media_id}")
async def get_media(
    media_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(MediaFile).where(MediaFile.id == media_id)
    )
    media = result.scalar_one_or_none()

    if media is None:
        raise HTTPException(status_code=404, detail="Media file not found")

    if media.path is not None:
        path = Path(media.path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Media file missing on disk")

        return FileResponse(
            path=path,
            media_type=media.content_type,
            filename=media.filename,
        )

    raise HTTPException(status_code=500, detail="Media file has neither data nor path")
