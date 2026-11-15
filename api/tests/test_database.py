import pytest
from unittest.mock import MagicMock
from database import DatabaseManager, DatabaseError


class TestDatabaseManager:

    def test_database_manager_inicializacao(self, mocker):
        """Testa se o DatabaseManager lida OK quando não há DATABASE_URL"""
        mocker.patch('os.environ.get', return_value=None)

        db = DatabaseManager()
        assert db.client is False

        with pytest.raises(DatabaseError):
            with db._connect():
                pass

    def test_get_transactions_with_mock(self, mocker):
        """Testa a leitura de transações simulando o retorno do Postgres"""
        db = DatabaseManager()
        db.dsn = "postgresql://fake"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': '1', 'descricao': 'Mercado', 'valor': -100.0, 'data': '2026-05-10', 'tipo': 'Despesa'}
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mocker.patch('database.psycopg.connect', return_value=mock_conn)

        resultado = db.get_transactions()

        assert len(resultado) == 1
        assert resultado[0]['descricao'] == 'Mercado'

    def test_add_manual_transaction(self, mocker):
        db = DatabaseManager()
        db.dsn = "postgresql://fake"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mocker.patch('database.psycopg.connect', return_value=mock_conn)

        transacao_fake = {
            'data': '2026-05-10',
            'descricao': 'Conta de Luz',
            'valor': -150.0,
            'categoria': 'Moradia',
            'tipo': 'Despesa'
        }

        db.add_manual_transaction(transacao_fake)

        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "insert into transacoes" in args[0]

    def test_save_transactions_ignora_duplicatas(self, mocker):
        """Reimportar o mesmo extrato não deve duplicar transações já salvas."""
        db = DatabaseManager()
        db.dsn = "postgresql://fake"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # 1ª chamada: transações já existentes (dedup). 2ª chamada: regras
        # de categorização aprendidas (nenhuma, nesse teste).
        mock_cursor.fetchall.side_effect = [
            [{'data': '2026-05-10', 'descricao': 'Conta de Luz', 'valor': -150.0}],
            [],
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mocker.patch('database.psycopg.connect', return_value=mock_conn)

        transacoes = [
            {  # duplicata exata (mesma data/descricao/valor) -> deve ser ignorada
                'data': '10/05/2026',
                'descricao': 'Conta de Luz',
                'valor': -150.0,
                'categoria': 'Moradia',
                'tipo': 'Despesa',
                'fonte': 'PDF',
            },
            {  # transação nova -> deve ser inserida
                'data': '11/05/2026',
                'descricao': 'Mercado',
                'valor': -80.0,
                'categoria': 'Comida',
                'tipo': 'Despesa',
                'fonte': 'PDF',
            },
        ]

        resultado = db.save_transactions(transacoes)

        assert resultado == {"inseridas": 1, "duplicadas": 1}
        # select de existentes + apenas 1 insert (a duplicata não gera insert)
        insert_calls = [
            c for c in mock_cursor.execute.call_args_list
            if "insert into transacoes" in c.args[0]
        ]
        assert len(insert_calls) == 1

    def test_update_transaction_aprende_regra_e_propaga(self, mocker):
        """Corrigir a categoria de um PIX deve criar uma regra e aplicá-la
        retroativamente em outras transações do mesmo destinatário que ainda
        estejam em 'A Categorizar' - mas não em destinatários diferentes."""
        db = DatabaseManager()
        db.dsn = "postgresql://fake"

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'descricao': 'PIX enviado para AUTOPASS S.A.'}
        mock_cursor.fetchall.return_value = [
            {'id': 'id-2', 'descricao': 'Pix crédito AUTOPASS S.A.'},      # mesmo destinatário -> propaga
            {'id': 'id-3', 'descricao': 'PIX enviado para OUTRA PESSOA'},  # destinatário diferente -> não propaga
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mocker.patch('database.psycopg.connect', return_value=mock_conn)

        db.update_transaction('id-1', {'categoria': 'Transporte'})

        executed = [c.args[0] for c in mock_cursor.execute.call_args_list]
        assert any("insert into regras_categorizacao" in e for e in executed)

        propagacao_updates = [
            c for c in mock_cursor.execute.call_args_list
            if c.args[0].strip() == "update transacoes set categoria = %s where id = %s"
        ]
        assert len(propagacao_updates) == 1
        assert propagacao_updates[0].args[1] == ('Transporte', 'id-2')
