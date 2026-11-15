import pytest
from fastapi.testclient import TestClient
import sys
import os

# Adiciona o diretório api ao sys.path para importações locais (se executado via IDE ou linha de comando local)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index import app

# Fixture global para usar o test client do fastapi na suíte inteira
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
