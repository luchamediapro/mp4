from __future__ import annotations

import io
from typing import Mapping
from email.message import Message
from http import HTTPStatus


class Response(io.IOBase):
    """
    Abstract base class for HTTP response adapters.

    Interface partially backwards-compatible with addinfourl and http.client.HTTPResponse.

    @param raw: Original response.
    @param url: URL that this is a response of.
    @param headers: response headers.
    @param status: Response HTTP status code. Default is 200 OK.
    @param reason: HTTP status reason. Will use built-in reasons based on status code if not provided.
    """

    def __init__(
            self, raw,
            url: str,
            headers: Mapping[str, str],
            status: int = 200,
            reason: str = None):

        self.raw = raw
        self.headers: Message = Message()
        for name, value in (headers or {}).items():
            self.headers.add_header(name, value)
        self.status = status
        self.reason = reason
        self.url = url
        if not reason:
            try:
                self.reason = HTTPStatus(status).phrase
            except ValueError:
                pass

    def readable(self):
        return True

    def read(self, amt: int = None) -> bytes:
        return self.raw.read(amt)

    def tell(self) -> int:
        return self.raw.tell()

    def close(self):
        self.raw.close()
        return super().close()

    # The following methods are for compatability reasons and are deprecated
    @property
    def code(self):
        """Deprecated, use HTTPResponse.status"""
        return self.status

    def getcode(self):
        """Deprecated, use HTTPResponse.status"""
        return self.status

    def geturl(self):
        """Deprecated, use HTTPResponse.url"""
        return self.url

    def info(self):
        """Deprecated, use HTTPResponse.headers"""
        return self.headers
