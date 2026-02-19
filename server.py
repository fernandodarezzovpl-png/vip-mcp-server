import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
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

# Render fornece a porta em PORT
PORT = int(os.environ.get("PORT", "8000"))

# 👇 Aqui sim: host/port na criação do FastMCP
mcp = FastMCP("VIP Leilões MCP", host="0.0.0.0", port=PORT)

@mcp.tool()
def vip_fetch(url: str) -> str:
    if not is_allowed(url):
        return "URL não permitida. Use apenas domínios do grupo VIP Leilões."

    resp = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "VIP-MCP-Server/1.0"},
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")
    return text[:15000]

if __name__ == "__main__":
    # 👇 run() sem host/port
    mcp.run(transport="http")
