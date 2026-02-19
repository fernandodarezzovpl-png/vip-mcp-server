import os
import contextlib
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
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


# MCP server (stateless_http + json_response costuma casar bem com conectores via URL)
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


async def health(request):
    # Isso é só pra você “ver algo” no navegador
    return JSONResponse({
        "ok": True,
        "service": "VIP MCP Server",
        "mcp_path": "/mcp",
        "hint": "Configure o conector com https://SEU_DOMINIO.onrender.com/mcp"
    })


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    # Necessário pro streamable_http_app funcionar direito
    async with mcp.session_manager.run():
        yield


async def mcp_info(request):
    return JSONResponse({
        "ok": True,
        "service": "VIP MCP Server",
        "mcp_path": "/mcp",
        "hint": "Use a URL base do conector: https://vip-mcp-server.onrender.com/mcp"
    })

app = Starlette(
    routes=[
        Route("/", health, methods=["GET"]),
        Route("/mcp", mcp_info, methods=["GET"]),         # <- garante 200 no /mcp
        Mount("/mcp", app=mcp.streamable_http_app()),     # <- MCP de verdade fica aqui
    ],
    lifespan=lifespan,
)


# Evita broncas de Host header dependendo de proxy/plataforma
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS (útil se o cliente for browser-based)
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
    uvicorn.run(app, host="0.0.0.0", port=port, proxy_headers=True, forwarded_allow_ips="*")
