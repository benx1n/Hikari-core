from typing import Optional

import httpx
from httpx import AsyncClient, Request, Response
from loguru import logger

from .config import hikari_config
from .data_source import __version__


async def before_request(request: Request):
    logger.info(f"{request.method} {request.url}")


async def after_response(response: Response):
    logger.info(f"本次响应的状态码:{response.status_code} {response.http_version} {response.request}")


_client_yuyuko: AsyncClient = None
_client_wg: AsyncClient = None
_client_default: AsyncClient = None


async def create_client_yuyuko() -> AsyncClient:
    global _client_yuyuko
    _client_yuyuko = httpx.AsyncClient(
        headers={
            'Authorization': hikari_config.token,
            "accept": "application/json",
            "Content-Type": "application/json",
            "Yuyuko-Client-Type": f"BOT;{__version__}",
        },
        event_hooks={
            "request": [
                before_request,
            ],
            "response": [
                after_response,
            ],
        },
        http2=hikari_config.http2,
    )
    return _client_yuyuko


async def create_client_wg() -> AsyncClient:
    if hikari_config.proxy:
        proxy = {"https://": hikari_config.proxy}
    else:
        proxy = {}
    global client_wg
    _client_wg = httpx.AsyncClient(proxies=proxy)
    return _client_wg


async def create_client_default() -> AsyncClient:
    global _client_default
    _client_default = httpx.AsyncClient()
    return _client_default


async def get_client_yuyuko() -> AsyncClient:
    return _client_yuyuko if _client_yuyuko else await create_client_yuyuko()


async def get_client_wg() -> AsyncClient:
    return _client_wg if _client_wg else await create_client_wg()


async def get_client_default() -> AsyncClient:
    return _client_default if _client_default else await create_client_default()
