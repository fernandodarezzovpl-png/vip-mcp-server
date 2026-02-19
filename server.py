import os
import contextlib
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from mcp.server.fastmcp import FastMCP


ALLOWED_DOMAINS = [
    "vipleiloes.com.br",
    "leilaovip.com.br",
    "correios.vipleiloes.com.br",
]


def is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)


# MCP server (stateless + JSON recomendado)
mcp = FastMCP("VIP Leilões MCP", stateless_http=True, json_response=True)


@mcp.tool()
def vip_fetch(url: str) -> dict:
    """Busca conteúdo (texto) de páginas públicas do grupo VIP Leilões."""
    if not is_allowed(url):
        return {"error": "URL não permitida. Use apenas domínios do grupo VIP Leilões."}

    resp = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "VIP-MCP-Server/1.0"},
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")
    return {"content": text[:15000]}


def healthcheck(request):
    return JSONResponse(
        {
            "ok": True,
            "service": "VIP MCP Server",
            "mcp_url": "/mcp",
            "hint": "Configure o conector com https://SEU_DOMINIO.onrender.com/mcp",
        }
    )


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    # Mantém o session manager do MCP ativo durante a vida do app
    async with mcp.session_manager.run():
        yield


# App Starlette:
# - Healthcheck na raiz "/"
# - MCP montado em "/mcp"
app = Starlette(
    routes=[
        Route("/", endpoint=healthcheck, methods=["GET"]),
        Mount("/mcp", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)

# Corrige "Invalid host header" (Render/proxies podem mandar Host diferente)
# Para produção, você pode restringir depois, ex:
# allowed_hosts=["vip-mcp-server.onrender.com", "*.onrender.com"]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS (se o cliente for browser-based, costuma precisar expor Mcp-Session-Id)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
