"""Bound request streams before multipart/JSON parsing, including chunked bodies."""
import re

from fastapi import HTTPException
from fastapi.responses import JSONResponse
import config


class RequestSizeLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        maximum = None
        if path in ("/register", "/login"):
            maximum = 16 * 1024
        elif re.fullmatch(r"/pokemon/[^/]+/image", path):
            maximum = config.MAX_UPLOAD_BYTES + 64 * 1024  # Multipart headers/boundaries.
        if maximum is None:
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        if b"content-length" in headers:
            try:
                length = int(headers[b"content-length"])
                if length < 0:
                    raise ValueError()
            except ValueError:
                return await JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)(scope, receive, send)
            if length > maximum:
                return await JSONResponse({"detail": "Request body exceeds the size limit"}, status_code=413)(scope, receive, send)
        consumed = 0

        async def bounded_receive():
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > maximum:
                    raise HTTPException(413, "Request body exceeds the size limit")
            return message

        await self.app(scope, bounded_receive, send)
