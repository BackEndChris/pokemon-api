from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile, HTTPException
from PIL import Image, PngImagePlugin
import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

import config
from database import engine
from image_storage import verified_image, cleanup_image
import pokemon_routes
from tests.test_security import account, pokemon, client, register
from auth import create_access_token


def image_bytes(format="PNG", size=(8, 8), metadata=False):
    stream = BytesIO()
    options = {}
    if metadata:
        info = PngImagePlugin.PngInfo()
        info.add_text("private", "remove-this-metadata")
        options["pnginfo"] = info
    Image.new("RGB", size, "red").save(stream, format=format, **options)
    return stream.getvalue()


def upload(headers, pokemon_id, data=None, filename="image.png", content_type="image/png"):
    return client.post(f"/pokemon/{pokemon_id}/image", headers=headers,
                       files={"file": (filename, image_bytes() if data is None else data, content_type)})


@pytest.mark.parametrize("format,extension", [("PNG", ".png"), ("JPEG", ".jpg"), ("WEBP", ".webp")])
def test_verified_format_controls_extension_and_filename(account, format, extension):
    row = pokemon(account).json()
    response = upload(account, row["id"], image_bytes(format), "../../malicious.exe", "application/octet-stream")
    assert response.status_code == 200
    url = response.json()["image_url"]
    name = url.removeprefix("/uploads/")
    assert len(Path(name).stem) == 36
    assert Path(name).suffix == extension
    with Image.open(pokemon_routes.UPLOAD_DIR / name) as stored:
        assert stored.format == format
        stored.load()
    assert client.get(f"/pokemon/{row['id']}").json()["image_url"] == url


def test_upload_drops_metadata_and_trailing_payload(account):
    row = pokemon(account).json()
    response = upload(account, row["id"], image_bytes(metadata=True) + b"trailing-secret-payload")
    path = pokemon_routes.UPLOAD_DIR / response.json()["image_url"].split("/")[-1]
    assert b"trailing-secret-payload" not in path.read_bytes()
    with Image.open(path) as image:
        assert "private" not in image.info


@pytest.mark.parametrize("data,status", [(b"", 400), (b"fake PNG", 400), (b"\x89PNG\r\n\x1a\n", 400), (image_bytes("GIF"), 415)])
def test_invalid_uploads_leave_no_files(account, data, status):
    row = pokemon(account).json()
    response = upload(account, row["id"], data)
    assert response.status_code == status
    assert list(pokemon_routes.UPLOAD_DIR.iterdir()) == []
    assert client.get(f"/pokemon/{row['id']}").json()["image_url"] is None


def test_missing_filename_and_missing_file(account):
    row = pokemon(account).json()
    assert upload(account, row["id"], filename="").status_code == 422
    assert client.post(f"/pokemon/{row['id']}/image", headers=account).status_code == 422
    with pytest.raises(HTTPException) as error:
        verified_image(UploadFile(filename=None, file=BytesIO(image_bytes())))
    assert error.value.status_code == 400


def test_upload_byte_pixel_and_request_body_limits(account, monkeypatch):
    row = pokemon(account).json()
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 100)
    assert upload(account, row["id"], b"x" * 101).status_code == 413
    assert upload(account, row["id"], b"x" * 70000).status_code == 413
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 500000)
    monkeypatch.setattr(config, "MAX_IMAGE_PIXELS", 10)
    assert upload(account, row["id"]).status_code == 413
    assert list(pokemon_routes.UPLOAD_DIR.iterdir()) == []


def test_replacing_and_deleting_images_cleans_files(account):
    row = pokemon(account).json()
    first = upload(account, row["id"]).json()["image_url"]
    first_path = pokemon_routes.UPLOAD_DIR / first.split("/")[-1]
    assert first_path.is_file()
    second = upload(account, row["id"]).json()["image_url"]
    second_path = pokemon_routes.UPLOAD_DIR / second.split("/")[-1]
    assert first != second
    assert not first_path.exists()
    assert second_path.is_file()
    assert client.delete(f"/pokemon/{row['id']}", headers=account).status_code == 200
    assert not second_path.exists()


def test_authentication_ownership_and_missing_resource_before_writing(account):
    row = pokemon(account).json()
    other = register("misty", "misty@example.com").json()
    other_headers = {"Authorization": f"Bearer {create_access_token(other['id'])}"}
    assert upload({}, row["id"]).status_code == 401
    assert upload(other_headers, row["id"]).status_code == 404
    assert upload(account, 99999).status_code == 404
    assert list(pokemon_routes.UPLOAD_DIR.iterdir()) == []


def test_partial_write_is_cleaned_and_existing_image_preserved(account, monkeypatch):
    row = pokemon(account).json()
    old = upload(account, row["id"]).json()["image_url"]
    original_open = Path.open

    class BrokenWriter:
        def __init__(self, path):
            self.stream = original_open(path, "xb")

        def __enter__(self):
            return self

        def write(self, data):
            self.stream.write(data[:10])
            raise OSError("private-storage-details")

        def __exit__(self, *args):
            self.stream.close()

    def broken_open(path, mode="r", *args, **kwargs):
        return BrokenWriter(path) if mode == "xb" else original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", broken_open)
    response = upload(account, row["id"])
    assert response.status_code == 503
    assert "private-storage-details" not in response.text
    assert client.get(f"/pokemon/{row['id']}").json()["image_url"] == old
    assert len(list(pokemon_routes.UPLOAD_DIR.iterdir())) == 1


def test_database_failure_removes_new_file_and_rolls_back(account, monkeypatch):
    row = pokemon(account).json()
    old = upload(account, row["id"]).json()["image_url"]
    original_begin = engine.begin

    @contextmanager
    def failed_commit():
        with original_begin() as connection:
            yield connection
            raise OperationalError("private-query", {}, Exception("private-db-details"))

    monkeypatch.setattr(engine, "begin", failed_commit)
    response = upload(account, row["id"])
    assert response.status_code == 503
    assert client.get(f"/pokemon/{row['id']}").json()["image_url"] == old
    assert len(list(pokemon_routes.UPLOAD_DIR.iterdir())) == 1


def test_cleanup_never_deletes_outside_upload_directory(tmp_path):
    outside = tmp_path / "keep.png"
    outside.write_bytes(b"keep")
    directory = tmp_path / "uploads"
    directory.mkdir()
    cleanup_image("/uploads/../keep.png", directory)
    cleanup_image(str(outside), directory)
    assert outside.read_bytes() == b"keep"


def test_filename_collision_does_not_delete_existing_image(account, monkeypatch):
    row = pokemon(account).json()
    old_url = upload(account, row["id"]).json()["image_url"]
    filename = old_url.split("/")[-1]
    monkeypatch.setattr(pokemon_routes, "uuid4", lambda: Path(filename).stem)
    assert upload(account, row["id"]).status_code == 503
    assert (pokemon_routes.UPLOAD_DIR / filename).is_file()
    assert client.get(f"/pokemon/{row['id']}").json()["image_url"] == old_url


def test_delete_database_failure_keeps_image_and_pokemon(account, monkeypatch):
    row = pokemon(account).json()
    url = upload(account, row["id"]).json()["image_url"]
    original_begin = engine.begin

    @contextmanager
    def failed_commit():
        with original_begin() as connection:
            yield connection
            raise OperationalError("private", {}, Exception("private"))

    monkeypatch.setattr(engine, "begin", failed_commit)
    response = client.delete(f"/pokemon/{row['id']}", headers=account)
    assert response.status_code == 503
    assert (pokemon_routes.UPLOAD_DIR / url.split("/")[-1]).is_file()
    assert client.get(f"/pokemon/{row['id']}").status_code == 200


def test_cleanup_failure_is_logged_without_leaking_paths(account, monkeypatch, caplog):
    row = pokemon(account).json()
    upload(account, row["id"])

    def denied(*args, **kwargs):
        raise PermissionError("private-path-details")

    monkeypatch.setattr(Path, "unlink", denied)
    response = client.delete(f"/pokemon/{row['id']}", headers=account)
    assert response.status_code == 200
    assert "storage maintenance required" in caplog.text
    assert "private-path-details" not in caplog.text + response.text
