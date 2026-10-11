import httpx
import os
import time
from datetime import datetime
from models.base import TipoObra
from schemas.obra_api import ObraAPI

BASE_URL = (os.getenv("JIKAN_BASE_URL") or "https://api.jikan.moe/v4").strip(" \"'")
INTERVALO = 0.5   # a Jikan permite 2 requisições por segundo

_client = httpx.Client(base_url=BASE_URL, timeout=10)

class JikanError(Exception):
    """Erro ao consultar a API Jikan"""

def get_json(caminho: str, params: dict | None = None) -> dict | None:
    """GET na Jikan. Retorna None se não existir (404)."""
    time.sleep(INTERVALO)
    try:
        resposta = _client.get(caminho, params=params)
    except httpx.HTTPError as erro:
        raise JikanError(f"Falha de conexão com a Jikan: {erro}") from erro

    if resposta.status_code == 404:
        return None
    if resposta.status_code == 429:
        raise JikanError("Limite de requisições da Jikan atingido, tente em instantes")
    if resposta.status_code != 200:
        raise JikanError(f"Jikan indisponível (HTTP {resposta.status_code})")
    return resposta.json()


class JikanService:
    @staticmethod
    def buscarMangas(termo: str, pagina: int = 1, limite: int = 10) -> list[ObraAPI]:
        dados = get_json("/manga", {"q": termo, "page": pagina, "limit": limite, "sfw": "true"})
        if not dados:
            return []
        return [JikanService._mapear(item) for item in dados.get("data") or []]

    @staticmethod
    def buscarMangaPorId(mal_id: int) -> ObraAPI | None:
        dados = get_json(f"/manga/{mal_id}")
        if not dados or not dados.get("data"):
            return None
        return JikanService._mapear(dados["data"])

    # Converte a resposta da Jikan para o formato ObraAPI
    @staticmethod
    def _mapear(item: dict) -> ObraAPI:
        imagens = (item.get("images") or {}).get("jpg") or {}
        inicio = (item.get("published") or {}).get("from")
        return ObraAPI(
            titulo=item.get("title_english") or item["title"],
            sinopse=item.get("synopsis"),
            capa_url=imagens.get("large_image_url") or imagens.get("image_url"),
            tipo_obra=TipoObra.MANGA,
            api_url=item.get("url") or f"https://myanimelist.net/manga/{item['mal_id']}",
            data_publicacao=datetime.strptime(inicio[:10], "%Y-%m-%d") if inicio else None,
            generos=[g["name"] for g in item.get("genres") or []],
            total_volumes=item.get("volumes"))
