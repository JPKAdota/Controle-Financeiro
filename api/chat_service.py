"""
Serviço de chat IA para o Agente de Investimentos.
Usa Google Gemini (gemini-2.5-flash) com contexto financeiro do usuário.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Flag para saber se o SDK está disponível
_genai_available = False
_client = None

try:
    from google import genai
    from google.genai import types
    _genai_available = True
    if GEMINI_API_KEY:
        _client = genai.Client(api_key=GEMINI_API_KEY)
except ImportError:
    pass


SYSTEM_PROMPT = """Você é o Assistente de Investimentos do Controle Financeiro, um agente de IA especializado em finanças pessoais e investimentos no mercado brasileiro.

## Suas Capacidades:
- Explicar conceitos de investimentos (Renda Fixa, Renda Variável, Tesouro Direto, CDB, LCI/LCA, Ações, FIIs, ETFs)
- Analisar a situação financeira do usuário com base nos dados fornecidos
- Sugerir estratégias de diversificação de carteira
- Explicar indicadores econômicos (Selic, CDI, IPCA, Ibovespa)
- Ajudar com planejamento financeiro e metas
- Comparar tipos de investimentos
- Explicar tributação de investimentos (IR, IOF, come-cotas)

## Regras:
1. Responda SEMPRE em português do Brasil
2. Seja didático e use exemplos práticos com valores em Reais (R$)
3. Use linguagem acessível, evitando jargões desnecessários
4. Quando analisar dados do usuário, seja específico com os números fornecidos
5. Use formatação markdown para organizar suas respostas (negrito, listas, tabelas quando útil)
6. Mantenha respostas concisas mas completas (máximo 400 palavras)
7. Sempre que mencionar um investimento, mencione seus riscos

## DISCLAIMER OBRIGATÓRIO:
Ao final de TODA resposta que envolva recomendação, sugestão ou análise de investimentos, adicione:

---
⚠️ *Este é um assistente educacional. As informações aqui NÃO constituem recomendação de investimento. Consulte um profissional certificado (CEA/CFP) antes de tomar decisões financeiras.*
"""


def _build_context_message(context: dict) -> str:
    """Constrói uma mensagem de contexto com os dados financeiros do usuário."""
    if not context:
        return ""

    parts = ["\n\n--- CONTEXTO FINANCEIRO DO USUÁRIO ---"]

    metrics = context.get("metrics", {})
    if metrics:
        parts.append(f"- Receitas totais: R$ {metrics.get('receitas', 0):,.2f}")
        parts.append(f"- Despesas totais: R$ {metrics.get('despesas', 0):,.2f}")
        parts.append(f"- Saldo em caixa: R$ {metrics.get('saldo', 0):,.2f}")
        parts.append(f"- Total investido: R$ {metrics.get('investido', 0):,.2f}")

    investments = context.get("investments", [])
    if investments:
        parts.append(f"\n- Investimentos registrados ({len(investments)}):")
        for inv in investments[:10]:  # Limitar a 10 para não estourar contexto
            desc = inv.get("descricao", "N/A")
            valor = abs(float(inv.get("valor", 0)))
            data = inv.get("data", "N/A")
            parts.append(f"  • {desc}: R$ {valor:,.2f} ({data})")

    parts.append("--- FIM DO CONTEXTO ---\n")
    return "\n".join(parts)


async def chat_with_agent(message: str, context: dict = None, history: list = None) -> dict:
    """
    Envia mensagem para o Gemini e retorna resposta.
    
    Args:
        message: Mensagem do usuário
        context: Dados financeiros do usuário para personalização
        history: Histórico de mensagens anteriores (para multi-turn)
    
    Returns:
        Dict com a resposta da IA.
    """
    if not _genai_available:
        return {
            "response": "⚠️ O módulo `google-genai` não está instalado. "
                        "Execute `pip install google-genai` no backend para habilitar o chat IA.",
            "error": "module_not_installed"
        }

    if not GEMINI_API_KEY or not _client:
        return {
            "response": "⚠️ A chave da API Gemini (GEMINI_API_KEY) não está configurada no arquivo `.env`. "
                        "Crie uma chave gratuita em [aistudio.google.com](https://aistudio.google.com) "
                        "e adicione ao `.env`.",
            "error": "api_key_missing"
        }

    try:
        # Montar conteúdo com contexto financeiro
        context_str = _build_context_message(context) if context else ""
        full_message = f"{message}{context_str}"

        # Montar histórico de conversa se disponível
        contents = []
        if history:
            for msg in history[-10:]:  # Últimas 10 mensagens para não estourar tokens
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.get("content", ""))]
                    )
                )

        # Adicionar mensagem atual
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=full_message)]
            )
        )

        response = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=2048,
            )
        )

        response_text = response.text if response.text else "Desculpe, não consegui gerar uma resposta. Tente novamente."

        return {
            "response": response_text,
            "error": None
        }

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {
                "response": "⏳ Limite de requisições atingido. Aguarde um momento e tente novamente.",
                "error": "rate_limited"
            }
        return {
            "response": f"❌ Erro ao processar sua mensagem: {error_msg}",
            "error": "generation_error"
        }


def get_suggested_questions() -> list[str]:
    """Retorna sugestões de perguntas para o usuário."""
    return [
        "Como começar a investir com pouco dinheiro?",
        "Qual a diferença entre CDB e Tesouro Direto?",
        "Analise minha situação financeira atual",
        "Como diversificar minha carteira de investimentos?",
        "O que é a taxa Selic e como ela afeta meus investimentos?",
        "Quanto preciso investir por mês para juntar R$ 100.000 em 5 anos?",
        "Vale a pena investir em ações para iniciantes?",
        "Explique o que são FIIs (Fundos Imobiliários)",
    ]
