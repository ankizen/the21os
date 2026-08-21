"""Image and video upload. Image upload is live-verified against the real
ad account (base64 `bytes` param — the SDK's documented single-image path,
distinct from the bulk {filename: bytes} map used for uploading many at
once). Video upload uses the SDK's `source` file param, which its own
TypeChecker declares type 'file' — the standard documented path for
POST /act_<id>/advideos — but isn't live-verified the same way: there's no
test video file in this environment to exercise it against. If it needs a
fix, that'll surface the first time someone uploads a real one."""

import base64
import tempfile
from pathlib import Path

from facebook_business.adobjects.advideo import AdVideo as FbAdVideo

from the21os.meta.client import call_meta, get_account

_MAX_IMAGE_BYTES = 10 * 1024 * 1024
_MAX_VIDEO_BYTES = 500 * 1024 * 1024


class AssetTooLarge(ValueError):
    pass


async def upload_image(file_bytes: bytes, account_id: str | None = None) -> dict:
    if len(file_bytes) > _MAX_IMAGE_BYTES:
        raise AssetTooLarge(f"Image is {len(file_bytes) / 1_048_576:.1f}MB — max is 10MB.")
    account = get_account(account_id)

    def fetch() -> dict:
        result = account.create_ad_image(params={"bytes": base64.b64encode(file_bytes).decode()})
        return dict(result)

    return await call_meta(fetch)


async def upload_video(file_bytes: bytes, name: str, account_id: str | None = None) -> dict:
    if len(file_bytes) > _MAX_VIDEO_BYTES:
        raise AssetTooLarge(f"Video is {len(file_bytes) / 1_048_576:.1f}MB — max is 500MB.")
    account = get_account(account_id)

    def fetch() -> dict:
        # The SDK's file-upload path needs a real path on disk, not bytes.
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        try:
            result = account.create_ad_video(params={"source": tmp_path, "name": name})
            return dict(result)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return await call_meta(fetch)


async def get_video_status(video_id: str) -> dict:
    def fetch() -> dict:
        video = FbAdVideo(video_id)
        video.api_get(fields=[FbAdVideo.Field.status, FbAdVideo.Field.id])
        return dict(video)

    return await call_meta(fetch)
