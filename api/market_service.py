"""
Serviço de dados de mercado financeiro brasileiro.
Usa a API brapi.dev (v2) para cotações, indicadores macro,
histórico, FIIs, cripto, câmbio e fundamentos.
Cache em memória de 5 minutos para respeitar rate limits.

Documentação: https://brapi.dev/docs
"""

import os
import time
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BRAPI_BASE_URL = "https://brapi.dev/api"
BRAPI_TOKEN = os.environ.get("BRAPI_TOKEN", "")

# Cache simples em memória: { key: { "data": ..., "timestamp": ... } }
_cache: dict = {}
CACHE_TTL = 300  # 5 minutos


def _get_cache(key: str) -> Optional[dict]:
    """Retorna dados do cache se ainda válidos."""
    entry = _cache.get(key)
    if entry and (time.time() - entry["timestamp"]) < CACHE_TTL:
        return entry["data"]
    return None


def _set_cache(key: str, data: dict):
    """Armazena dados no cache."""
    _cache[key] = {"data": data, "timestamp": time.time()}


def _headers() -> dict:
    """Retorna headers de autenticação para brapi."""
    if BRAPI_TOKEN:
        return {"Authorization": f"Bearer {BRAPI_TOKEN}"}
    return {}


def _extract_quote(result: dict) -> dict:
    """Extrai dados de cotação de um resultado da brapi v2.
    Na v2 os dados ficam em results[].data para /v2/stocks/quote,
    mas em /api/quote/ ficam diretamente em results[].
    Esta função trata ambos os formatos.
    """
    # Se tem chave "data" aninhada (formato v2), usa ela
    data = result.get("data", result)
    return {
        "symbol": result.get("symbol", data.get("symbol", "")),
        "shortName": data.get("shortName", ""),
        "longName": data.get("longName", ""),
        "price": data.get("regularMarketPrice", 0),
        "change": data.get("regularMarketChange", 0),
        "changePercent": data.get("regularMarketChangePercent", 0),
        "previousClose": data.get("regularMarketPreviousClose", 0),
        "volume": data.get("regularMarketVolume", 0),
        "marketCap": data.get("marketCap", 0),
        "logo": data.get("logourl", ""),
        "updatedAt": data.get("regularMarketTime", ""),
    }


# ==========================================
# AÇÕES, ETFs, BDRs
# ==========================================

async def get_stock_quotes(symbols: list[str]) -> dict:
    """
    Busca cotações de ações/ETFs/BDRs na B3.
    Endpoint: GET /api/v2/stocks/quote?symbols=PETR4,VALE3
    """
    cache_key = f"quotes_{'_'.join(sorted(symbols))}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    symbols_str = ",".join(symbols)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BRAPI_BASE_URL}/v2/stocks/quote",
                headers=_headers(),
                params={"symbols": symbols_str}
            )
            response.raise_for_status()
            data = response.json()

            quotes = [_extract_quote(r) for r in data.get("results", [])]
            result_data = {"quotes": quotes, "requestedAt": time.time()}
            _set_cache(cache_key, result_data)
            return result_data

    except httpx.HTTPStatusError as e:
        return {"error": f"Erro na API brapi: {e.response.status_code}", "quotes": []}
    except Exception as e:
        return {"error": f"Erro ao buscar cotações: {str(e)}", "quotes": []}


async def get_stock_history(symbol: str, range_period: str = "1mo") -> dict:
    """
    Busca histórico de preços de um ativo.
    Endpoint: GET /api/v2/stocks/historical?symbols=PETR4&range=1mo&interval=1d
    """
    cache_key = f"history_{symbol}_{range_period}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BRAPI_BASE_URL}/v2/stocks/historical",
                headers=_headers(),
                params={
                    "symbols": symbol,
                    "range": range_period,
                    "interval": "1d",
                }
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return {"symbol": symbol, "history": [], "error": "Nenhum dado encontrado"}

            result = results[0]
            # Na v2, os dados ficam aninhados
            result_data_inner = result.get("data", result)
            history_prices = result_data_inner.get("historicalDataPrice", [])

            history = []
            for point in history_prices:
                history.append({
                    "date": point.get("date", 0),
                    "open": point.get("open", 0),
                    "high": point.get("high", 0),
                    "low": point.get("low", 0),
                    "close": point.get("close", 0),
                    "volume": point.get("volume", 0),
                })

            result_data = {
                "symbol": symbol,
                "shortName": result_data_inner.get("shortName", symbol),
                "history": history,
                "currentPrice": result_data_inner.get("regularMarketPrice", 0),
            }
            _set_cache(cache_key, result_data)
            return result_data

    except Exception as e:
        return {"symbol": symbol, "history": [], "error": str(e)}


async def get_stock_dividends(symbol: str) -> dict:
    """
    Busca dividendos e JCP de uma ação.
    Endpoint: GET /api/v2/stocks/dividends?symbols=ITUB4
    """
    cache_key = f"dividends_{symbol}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BRAPI_BASE_URL}/v2/stocks/dividends",
                headers=_headers(),
                params={"symbols": symbol}
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            dividends = []
            if results:
                result_data_inner = results[0].get("data", results[0])
                for d in result_data_inner.get("dividends", []):
                    dividends.append({
                        "date": d.get("paymentDate", d.get("date", "")),
                        "value": d.get("value", 0),
                        "type": d.get("type", "Dividendo"),
                    })

            result_data = {"symbol": symbol, "dividends": dividends}
            _set_cache(cache_key, result_data)
            return result_data

    except Exception as e:
        return {"symbol": symbol, "dividends": [], "error": str(e)}


# ==========================================
# FUNDOS IMOBILIÁRIOS (FIIs)
# ==========================================

async def get_fii_dividends(symbols: list[str]) -> dict:
    """
    Busca rendimentos de Fundos Imobiliários (FIIs).
    Endpoint: GET /api/v2/fii/dividends?symbols=MXRF11
    """
    cache_key = f"fii_div_{'_'.join(sorted(symbols))}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    symbols_str = ",".join(symbols)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BRAPI_BASE_URL}/v2/fii/dividends",
                headers=_headers(),
                params={"symbols": symbols_str}
            )
            response.raise_for_status()
            data = response.json()

            fiis = []
            for result in data.get("results", []):
                result_data_inner = result.get("data", result)
                fiis.append({
                    "symbol": result.get("symbol", ""),
                    "dividends": result_data_inner.get("dividends", []),
                })

            result_data = {"fiis": fiis, "requestedAt": time.time()}
            _set_cache(cache_key, result_data)
            return result_data

    except Exception as e:
        return {"error": str(e), "fiis": []}


# ==========================================
# TICKERS (BUSCA E AUTOCOMPLETE)
# ==========================================

async def search_tickers(query: str = "", ticker_type: str = "") -> dict:
    """
    Busca e filtra tickers disponíveis na B3.
    Endpoint: GET /api/v2/tickers
    
    Args:
        query: Texto para busca (nome ou símbolo)
        ticker_type: Filtro por tipo (stock, fund, bdr, etc.)
    """
    cache_key = f"tickers_{query}_{ticker_type}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    try:
        params = {}
        if query:
            params["search"] = query
        if ticker_type:
            params["type"] = ticker_type

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BRAPI_BASE_URL}/v2/tickers",
                headers=_headers(),
                params=params
            )
            response.raise_for_status()
            data = response.json()

            tickers = []
            for t in data.get("results", data.get("tickers", []))[:50]:
                tickers.append({
                    "symbol": t.get("symbol", t.get("ticker", "")),
                    "name": t.get("name", t.get("shortName", "")),
                    "type": t.get("type", ""),
                    "sector": t.get("sector", ""),
                })

            result_data = {"tickers": tickers, "total": len(tickers)}
            _set_cache(cache_key, result_data)
            return result_data

    except Exception as e:
        return {"error": str(e), "tickers": [], "total": 0}


# ==========================================
# INDICADORES MACROECONÔMICOS
# ==========================================

async def get_macro_indicators() -> dict:
    """
    Busca indicadores macroeconômicos: Selic, CDI, IPCA, Ibovespa, Dólar.
    Combina dados da brapi.dev e da API do Banco Central (SGS).
    """
    cached = _get_cache("macro_indicators")
    if cached:
        return cached

    indicators = {}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # --- Ibovespa via brapi v2 ---
            try:
                ibov_resp = await client.get(
                    f"{BRAPI_BASE_URL}/v2/stocks/quote",
                    headers=_headers(),
                    params={"symbols": "^BVSP"}
                )
                if ibov_resp.status_code == 200:
                    ibov_data = ibov_resp.json()
                    results = ibov_data.get("results", [])
                    if results:
                        d = results[0].get("data", results[0])
                        indicators["ibovespa"] = {
                            "name": "Ibovespa",
                            "value": d.get("regularMarketPrice", 0),
                            "change": d.get("regularMarketChange", 0),
                            "changePercent": d.get("regularMarketChangePercent", 0),
                            "type": "index"
                        }
            except Exception:
                pass

            # --- Dólar via brapi v2 ---
            try:
                usd_resp = await client.get(
                    f"{BRAPI_BASE_URL}/v2/currency",
                    headers=_headers(),
                    params={"currency": "USD-BRL"}
                )
                if usd_resp.status_code == 200:
                    usd_data = usd_resp.json()
                    currencies = usd_data.get("currency", [])
                    if currencies:
                        c = currencies[0]
                        indicators["dolar"] = {
                            "name": "Dólar (USD/BRL)",
                            "value": float(c.get("bidPrice", 0)),
                            "change": 0,
                            "changePercent": float(c.get("pctChange", 0)),
                            "type": "currency"
                        }
            except Exception:
                pass

        # --- Selic, CDI, IPCA via API do Banco Central (SGS) ---
        # Estas APIs são 100% gratuitas, sem token
        async with httpx.AsyncClient(timeout=10.0) as client:
            bcb_series = {
                "selic": {"id": "432", "name": "Taxa Selic (a.a.)"},
                "cdi": {"id": "4391", "name": "CDI (a.a.)"},
                "ipca": {"id": "433", "name": "IPCA (mensal)"},
            }
            for key, serie in bcb_series.items():
                try:
                    resp = await client.get(
                        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie['id']}/dados/ultimos/1?formato=json"
                    )
                    if resp.status_code == 200:
                        resp_data = resp.json()
                        if resp_data:
                            indicators[key] = {
                                "name": serie["name"],
                                "value": float(resp_data[-1].get("valor", 0)),
                                "change": 0,
                                "changePercent": 0,
                                "type": "rate"
                            }
                except Exception:
                    pass

        result_data = {"indicators": indicators, "requestedAt": time.time()}
        _set_cache("macro_indicators", result_data)
        return result_data

    except Exception as e:
        return {"error": f"Erro ao buscar indicadores: {str(e)}", "indicators": {}}


# ==========================================
# CRIPTOMOEDAS
# ==========================================

async def get_crypto_quotes(symbols: list[str] = None) -> dict:
    """
    Busca cotações de criptomoedas.
    Usa brapi v2 para buscar cripto como ativos normais.
    """
    if not symbols:
        symbols = ["BTC", "ETH"]
    
    cache_key = f"crypto_{'_'.join(sorted(symbols))}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BRAPI_BASE_URL}/v2/crypto",
                headers=_headers(),
                params={"coin": ",".join(symbols), "currency": "BRL"}
            )
            response.raise_for_status()
            data = response.json()

            coins = []
            for result in data.get("coins", []):
                coins.append({
                    "symbol": result.get("coin", ""),
                    "name": result.get("coinName", ""),
                    "price": float(result.get("regularMarketPrice", 0)),
                    "change": float(result.get("regularMarketChange", 0)),
                    "changePercent": float(result.get("regularMarketChangePercent", 0)),
                    "marketCap": float(result.get("marketCap", 0)),
                    "volume": float(result.get("regularMarketVolume", 0)),
                    "logo": result.get("coinImageUrl", ""),
                })

            result_data = {"coins": coins, "requestedAt": time.time()}
            _set_cache(cache_key, result_data)
            return result_data

    except Exception as e:
        return {"error": str(e), "coins": []}
