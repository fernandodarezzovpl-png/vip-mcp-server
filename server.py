from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

mcp = FastMCP("VIP Leilões MCP")

ALLOWED_DOMAINS = [
    "vipleiloes.com.br",
    "leilaovip.com.br",
    "correios.vipleiloes.com.br"
]

def is_allowed(url):
    parsed = urlparse(url)
    return any(domain in parsed.netloc for domain in ALLOWED_DOMAINS)

@mcp.tool()
def vip_fetch(url: str) -> str:
    if not is_allowed(url):
        return "URL não permitida."

    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(separator="\n")
    return text[:15000]

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
