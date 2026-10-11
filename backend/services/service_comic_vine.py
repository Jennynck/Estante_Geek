import html
import httpx
import os
import re
import time
from datetime import datetime
from models.base import TipoObra
from schemas.obra_api import ObraAPI

BASE_URL = "https://comicvine.gamespot.com/api"
INTERVALO = 1.1   # o Comic Vine bloqueia requisições muito rápidas
CAMPOS = "id,name,deck,description,image,count_of_issues,publisher,start_year,site_detail_url"

# O Comic Vine bloqueia requisições sem um User-Agent próprio
_client = httpx.Client(base_url=BASE_URL, timeout=10,
                       headers={"User-Agent": "EstanteGeek/0.1"})

class ComicVineError(Exception):
    """Erro ao consultar a API Comic Vine"""

def get_json(caminho: str, params: dict) -> dict | None:
    """GET no Comic Vine. Retorna None se o objeto não existir."""
    chave = os.getenv("COMIC_VINE_API")
    if not chave:
        raise ComicVineError("COMIC_VINE_API não está configurada no .env")

    time.sleep(INTERVALO)
    try:
        resposta = _client.get(caminho, params={**params, "api_key": chave, "format": "json"})
    except httpx.HTTPError as erro:
        raise ComicVineError(f"Falha de conexão com o Comic Vine: {erro}") from erro

    if resposta.status_code == 404:
        return None
    if resposta.status_code in (420, 429):
        raise ComicVineError("Limite de requisições do Comic Vine atingido, tente mais tarde")
    if resposta.status_code != 200:
        raise ComicVineError(f"Comic Vine indisponível (HTTP {resposta.status_code})")

    # status_code do Comic Vine: 1 = OK, 101 = objeto não encontrado
    dados = resposta.json()
    if dados.get("status_code") == 101:
        return None
    if dados.get("status_code") != 1:
        raise ComicVineError(f"Erro do Comic Vine: {dados.get('error')}")
    return dados

# A descrição do Comic Vine vem em HTML
def limparHtml(texto: str | None) -> str | None:
    if not texto:
        return None
    texto = html.unescape(re.sub(r"<[^>]+>", " ", texto))
    return re.sub(r"\s+", " ", texto).strip() or None


class ComicVineService:
    @staticmethod
    def buscarHqs(termo: str, pagina: int = 1, limite: int = 10) -> list[ObraAPI]:
        dados = get_json("/search/", {
            "query": termo,
            "resources": "volume",
            "limit": limite,
            "offset": (pagina - 1) * limite,
            "field_list": CAMPOS,
        })
        if not dados:
            return []
        return [ComicVineService._mapear(item) for item in dados.get("results") or []]

    @staticmethod
    def buscarHqPorId(volume_id: int) -> ObraAPI | None:
        # No Comic Vine, o id de um volume vem com o prefixo 4050-
        dados = get_json(f"/volume/4050-{volume_id}/", {"field_list": CAMPOS})
        if not dados or not dados.get("results"):
            return None
        return ComicVineService._mapear(dados["results"])

    # Converte a resposta do Comic Vine para o formato ObraAPI
    @staticmethod
    def _mapear(item: dict) -> ObraAPI:
        imagem = item.get("image") or {}
        ano = str(item.get("start_year") or "")[:4]
        data = datetime(int(ano), 1, 1) if ano.isdigit() and int(ano) > 0 else None  # só vem o ano
        return ObraAPI(
            titulo=item["name"],
            sinopse=limparHtml(item.get("description")) or item.get("deck"),
            capa_url=imagem.get("medium_url") or imagem.get("original_url"),
            tipo_obra=TipoObra.HQ,
            api_url=item.get("site_detail_url") or f"https://comicvine.gamespot.com/volume/4050-{item['id']}/",
            data_publicacao=data,
            editora=(item.get("publisher") or {}).get("name"),
            total_volumes=item.get("count_of_issues"))
    