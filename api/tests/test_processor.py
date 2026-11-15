import pytest
import io
import pandas as pd
from processor import ProcessadorExtratos, extrair_padrao_regra

@pytest.fixture
def processador():
    return ProcessadorExtratos()

class TestProcessadorExtratos:
    
    def test_init_categorias_padrao(self, processador):
        """Valida que o dicionário de categorias essenciais foi inicializado"""
        assert 'Comida' in processador.categorias_padrao
        assert 'Receita' in processador.categorias_padrao
        assert 'Lazer' in processador.categorias_padrao
        
    def test_categorizacao_conhecida_comida(self, processador):
        """Valida que strings que tem ifood entram na categoria correta"""
        cat = processador.categorizar_transacao("PGTO IFOOD *IFOOD", -35.90)
        assert cat == "Comida"
        
    def test_categorizacao_conhecida_transporte(self, processador):
        cat = processador.categorizar_transacao("UBER *UBER *TRIP", -15.50)
        assert cat == "Transporte"
        
    def test_categorizacao_receita(self, processador):
        cat = processador.categorizar_transacao("SALARIO DEPOSITADO NOVO", 5000.0)
        assert cat == "Receita"

    def test_categorizacao_ignora_acentos(self, processador):
        """Extratos bancários costumam vir sem acento (ex: 'COMBUSTIVEL', 'CONDOMINIO').
        A categorização precisa reconhecer esses casos mesmo com a palavra-chave acentuada."""
        assert processador.categorizar_transacao("POSTO COMBUSTIVEL SHELL", -200.0) == "Transporte"
        assert processador.categorizar_transacao("PAGAMENTO CONDOMINIO EDIFICIO", -450.0) == "Moradia"
        assert processador.categorizar_transacao("PIX RECEBIDO - DEPOSITO", 100.0) == "Receita"

    def test_categorizacao_desconhecida(self, processador):
        """Transações sem correspondência caem em 'A Categorizar'"""
        cat = processador.categorizar_transacao("XPTO TARIFA BANCARIA", -12.0)
        assert cat == "A Categorizar"
        
    def test_processar_csv_valido(self, processador):
        """Testa se consegue processar um arquivo CSV em bytes montando a lista de transações corrreta"""
        # Criamos um DataFrame simulado e transformamos em csv bytes
        df_fake = pd.DataFrame({
            'Data': ['15/05/2026', '16/05/2026'],
            'Descrição': ['COMPRA MERCADO', 'CREDITO PIX DE JOAO'],
            'Valor': ['R$ -150,00', '500,00']
        })
        
        csv_bytes = df_fake.to_csv(index=False).encode('utf-8')
        
        resultado = processador.processar_csv(csv_bytes)
        
        assert len(resultado) == 2
        
        # Validando a transacao 1 (Despesa e Mercado)
        assert resultado[0]['tipo'] == 'Despesa'
        assert resultado[0]['valor'] == -150.0
        assert resultado[0]['categoria'] == 'Comida'
        
        # Validando a transacao 2 (Receita e Desconhecida, mas tipo positivo)
        assert resultado[1]['tipo'] == 'Receita'
        assert resultado[1]['valor'] == 500.0

    def test_processar_csv_formato_invalido(self, processador):
        """Se submeter um CSV quebrado garante que levante a exception"""
        # CSV Faltando a coluna necessaria 'Valor'
        df_fake = pd.DataFrame({
            'Data': ['15/05/2026'],
            'Descrição': ['TESTE']
        })
        csv_bytes = df_fake.to_csv(index=False).encode('utf-8')
        
        with pytest.raises(Exception) as excinfo:
            processador.processar_csv(csv_bytes)
            
        assert "colunas necessárias" in str(excinfo.value).lower()

    def test_processar_csv_suporta_milhar_e_decimal_brasileiros(self, processador):
        csv_bytes = (
            'Data,Descrição,Valor\n'
            '15/05/2026,Salário,"R$ 1.234,56"\n'
        ).encode('utf-8')

        resultado = processador.processar_csv(csv_bytes)

        assert resultado[0]['valor'] == 1234.56

    def test_processar_ofx_valido(self, processador):
        """Parseia um OFX mínimo com uma despesa e uma receita."""
        ofx_bytes = (
            "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\n\n"
            "<OFX>\n<BANKMSGSRSV1>\n<STMTTRNRS>\n<STMTRS>\n<BANKTRANLIST>\n"
            "<STMTTRN>\n<TRNTYPE>DEBIT\n<DTPOSTED>20260905120000[-3:BRT]\n"
            "<TRNAMT>-150.00\n<FITID>202609050001\n<MEMO>COMPRA MERCADO XYZ\n</STMTTRN>\n"
            "<STMTTRN>\n<TRNTYPE>CREDIT\n<DTPOSTED>20260903120000[-3:BRT]\n"
            "<TRNAMT>5000.00\n<FITID>202609030001\n<MEMO>SALARIO EMPRESA ABC\n</STMTTRN>\n"
            "</BANKTRANLIST>\n</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>\n"
        ).encode('utf-8')

        resultado = processador.processar_ofx(ofx_bytes)

        assert len(resultado) == 2
        assert resultado[0]['valor'] == -150.0
        assert resultado[0]['data'] == '05/09/2026'
        assert resultado[0]['categoria'] == 'Comida'
        assert resultado[0]['tipo'] == 'Despesa'
        assert resultado[0]['fonte'] == 'OFX'

        assert resultado[1]['valor'] == 5000.0
        assert resultado[1]['categoria'] == 'Receita'
        assert resultado[1]['tipo'] == 'Receita'


class TestExtrairPadraoRegra:
    """PIX/TED nomeiam pessoas físicas e empresas - nunca batem com keywords
    de comércio. extrair_padrao_regra isola o nome para virar chave de regra
    de categorização aprendida."""

    def test_remove_prefixo_pix_enviado(self):
        assert extrair_padrao_regra("PIX enviado para AUTOPASS S.A.") == "autopass s.a."

    def test_remove_prefixo_pix_recebido(self):
        assert extrair_padrao_regra("PIX recebido de Wise Brasil Corretora de Cambio Ltda") == \
            "wise brasil corretora de cambio ltda"

    def test_remove_prefixo_pix_credito(self):
        assert extrair_padrao_regra("Pix crédito CENTRO AUTOMOTIVO JOAO COTIA") == "centro automotivo joao cotia"

    def test_variacoes_do_mesmo_destinatario_geram_o_mesmo_padrao(self):
        """'Pix crédito X' e 'PIX enviado para X' devem gerar o mesmo padrão,
        senão a regra aprendida não se propaga entre as duas variações."""
        a = extrair_padrao_regra("Pix crédito CENTRO AUTOMOTIVO JOAO COTIA")
        b = extrair_padrao_regra("PIX enviado para CENTRO AUTOMOTIVO JOAO COTIA")
        assert a == b

    def test_remove_prefixo_ted(self):
        assert extrair_padrao_regra("TED recebido de TECH4HUMANS TECNOLOGIA DA INFO") == \
            "tech4humans tecnologia da info"

    def test_sem_prefixo_conhecido_mantem_descricao_normalizada(self):
        assert extrair_padrao_regra("Compra no débito XYZ") == "compra no debito xyz"

    def test_processar_ofx_sem_transacoes_levanta_excecao(self, processador):
        ofx_bytes = b"<OFX>\n<BANKMSGSRSV1>\n</BANKMSGSRSV1>\n</OFX>\n"

        with pytest.raises(Exception) as excinfo:
            processador.processar_ofx(ofx_bytes)

        assert "ofx" in str(excinfo.value).lower()
