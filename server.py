import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI()

ALLOWED_DOMAINS = [
    "vipleiloes.com.br",
    "leilaovip.com.br",
    "correios.vipleiloes.com.br",
]

def is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)

@app.get("/")
def health():
    return {"ok": True, "service": "VIP Fetch API"}

@app.get("/fetch")
def fetch_page(url: str):
    if not is_allowed(url):
        raise HTTPException(status_code=403, detail="URL não permitida")

    resp = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "VIP-MCP-Server/1.0"},
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")
    return {"content": text[:15000]}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
