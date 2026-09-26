from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import settings
from app.deps import current_user
from app.models import User
from app.services.storage import get_storage
from app.services.rate_limit import allow_request

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
MAX_BYTES = 5 * 1024 * 1024
MAX_WIDTH = 6000
MAX_HEIGHT = 6000
MAX_PHOTOS_PER_LISTING = 6
ALLOWED = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


def _validate_image(content_type: str, data: bytes) -> tuple[str, int, int]:
    extension = ALLOWED.get(content_type)
    if not extension:
        raise HTTPException(415, "Use a JPEG, PNG, WebP or GIF image")
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
            if width < 80 or height < 80:
                raise HTTPException(422, "Listing images must be at least 80×80 pixels")
            if width > MAX_WIDTH or height > MAX_HEIGHT:
                raise HTTPException(422, f"Listing images must be no larger than {MAX_WIDTH}×{MAX_HEIGHT} pixels")
    except UnidentifiedImageError as exc:
        raise HTTPException(415, "The uploaded file is not a valid image") from exc
    return extension, width, height


@router.post("/listing-image")
async def upload_listing_image(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(current_user),
):
    if not allow_request(f"cc:upload:{user.id}", 60, 3600):
        raise HTTPException(429, "Too many image uploads. Please try again later")
    if not any(m.verified for m in user.memberships):
        raise HTTPException(403, "Verify your campus membership before uploading listing photos")
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED:
        raise HTTPException(415, "Use a JPEG, PNG, WebP or GIF image")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Listing images must be 5 MB or smaller")
    extension, width, height = _validate_image(content_type, data)
    key, stored_url = get_storage().save(data, content_type, extension)
    if settings.storage_provider.lower() == "local":
        url = f"{str(request.base_url).rstrip('/')}/uploads/{key}"
    else:
        url = stored_url
    return {
        "url": url,
        "filename": key,
        "content_type": content_type,
        "size": len(data),
        "width": width,
        "height": height,
    }
