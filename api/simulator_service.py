"""
Motor de simulação de investimentos.
Calcula projeção de patrimônio com aportes mensais e juros compostos.
Suporta taxas pré-fixadas e indexadas (CDI%, IPCA+%).
"""

from typing import Optional


def simulate_investment(
    aporte_inicial: float,
    aporte_mensal: float,
    taxa_anual: float,
    meses: int,
    indexador: str = "pre",
    taxa_indexador: float = 0.0,
) -> dict:
    """
    Simula a evolução de um investimento com aportes mensais.
    
    Args:
        aporte_inicial: Valor inicial investido (R$)
        aporte_mensal: Valor do aporte mensal (R$)
        taxa_anual: Taxa de juros anual (ex: 12.5 para 12.5% a.a.)
        meses: Número de meses da simulação
        indexador: Tipo de indexação ("pre", "cdi", "ipca")
        taxa_indexador: Taxa do indexador base (ex: CDI = 14.25% a.a., IPCA = 4.5% a.a.)
                        Quando indexador = "cdi", taxa_anual é % do CDI (ex: 100 = 100% CDI)
                        Quando indexador = "ipca", taxa_anual é o spread (ex: 6 = IPCA + 6%)
    
    Returns:
        Dict com série temporal e métricas resumo.
    """
    # Calcular taxa efetiva mensal
    if indexador == "cdi":
        # taxa_anual = percentual do CDI (ex: 100 = 100% do CDI)
        # taxa_indexador = CDI anual (ex: 14.25)
        taxa_efetiva_anual = (taxa_anual / 100) * taxa_indexador
    elif indexador == "ipca":
        # taxa_anual = spread sobre IPCA (ex: 6.0)
        # taxa_indexador = IPCA anual (ex: 4.5)
        taxa_efetiva_anual = taxa_indexador + taxa_anual
    else:
        # Pré-fixado: taxa_anual é a taxa direta
        taxa_efetiva_anual = taxa_anual

    # Converter taxa anual para mensal (juros compostos)
    taxa_mensal = (1 + taxa_efetiva_anual / 100) ** (1 / 12) - 1

    # Simulação mês a mês
    saldo = aporte_inicial
    total_investido = aporte_inicial
    serie = []

    # Ponto zero
    serie.append({
        "mes": 0,
        "saldo": round(saldo, 2),
        "totalInvestido": round(total_investido, 2),
        "rendimentoMes": 0,
        "rendimentoAcumulado": 0,
    })

    rendimento_acumulado = 0

    for mes in range(1, meses + 1):
        # Rendimento do mês sobre o saldo atual
        rendimento_mes = saldo * taxa_mensal

        # Saldo = saldo anterior + rendimento + aporte
        saldo = saldo + rendimento_mes + aporte_mensal
        total_investido += aporte_mensal
        rendimento_acumulado += rendimento_mes

        serie.append({
            "mes": mes,
            "saldo": round(saldo, 2),
            "totalInvestido": round(total_investido, 2),
            "rendimentoMes": round(rendimento_mes, 2),
            "rendimentoAcumulado": round(rendimento_acumulado, 2),
        })

    # Métricas finais
    valor_final = round(saldo, 2)
    rendimento_total = round(rendimento_acumulado, 2)
    rentabilidade_pct = round(
        (rendimento_total / total_investido * 100) if total_investido > 0 else 0, 2
    )

    return {
        "parametros": {
            "aporteInicial": aporte_inicial,
            "aporteMensal": aporte_mensal,
            "taxaAnual": taxa_anual,
            "taxaEfetivaAnual": round(taxa_efetiva_anual, 2),
            "taxaMensal": round(taxa_mensal * 100, 4),
            "meses": meses,
            "indexador": indexador,
        },
        "resultado": {
            "valorFinal": valor_final,
            "totalInvestido": round(total_investido, 2),
            "rendimentoTotal": rendimento_total,
            "rentabilidadePct": rentabilidade_pct,
        },
        "serie": serie,
    }


def compare_scenarios(scenarios: list[dict]) -> dict:
    """
    Compara múltiplos cenários de investimento.
    
    Args:
        scenarios: Lista de dicts com parâmetros para simulate_investment.
                   Cada dict deve ter: nome, aporte_inicial, aporte_mensal,
                   taxa_anual, meses, indexador, taxa_indexador.
    
    Returns:
        Dict com resultados de cada cenário para comparação.
    """
    results = []

    for scenario in scenarios[:3]:  # Máximo 3 cenários
        sim = simulate_investment(
            aporte_inicial=scenario.get("aporte_inicial", 0),
            aporte_mensal=scenario.get("aporte_mensal", 0),
            taxa_anual=scenario.get("taxa_anual", 0),
            meses=scenario.get("meses", 12),
            indexador=scenario.get("indexador", "pre"),
            taxa_indexador=scenario.get("taxa_indexador", 0),
        )

        results.append({
            "nome": scenario.get("nome", f"Cenário {len(results) + 1}"),
            "parametros": sim["parametros"],
            "resultado": sim["resultado"],
            "serie": sim["serie"],
        })

    return {"scenarios": results}
