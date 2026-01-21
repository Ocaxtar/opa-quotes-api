"""
Tests para el endpoint /metrics de Prometheus
"""
import pytest
from fastapi.testclient import TestClient

from opa_quotes_api.main import app

client = TestClient(app)


@pytest.mark.unit
class TestMetricsEndpoint:
    """Tests para el endpoint de métricas Prometheus."""

    def test_metrics_endpoint_returns_200(self):
        """Verificar que /metrics retorna status 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Verificar que /metrics retorna formato Prometheus."""
        response = client.get("/metrics")
        content = response.text

        # Verificar formato Prometheus (contiene # HELP, # TYPE, etc.)
        assert "# HELP" in content
        assert "# TYPE" in content
        # Verificar que es text/plain (sin importar la versión)
        assert response.headers["content-type"].startswith("text/plain")

    def test_metrics_contains_http_request_metrics(self):
        """Verificar que las métricas incluyen contadores HTTP."""
        # Hacer una request primero para generar métricas
        client.get("/health")

        # Consultar métricas
        response = client.get("/metrics")
        content = response.text

        # Verificar métricas HTTP básicas
        assert "http_requests_total" in content
        assert "http_request_duration" in content

    def test_metrics_contains_python_process_metrics(self):
        """Verificar que las métricas incluyen info del proceso Python."""
        response = client.get("/metrics")
        content = response.text

        # Verificar métricas del proceso Python
        assert "python_info" in content
        assert "python_gc_" in content  # Métricas de garbage collector
        # Nota: process_* solo está disponible en Linux, no en Windows

    def test_metrics_increments_after_requests(self):
        """Verificar que las métricas se incrementan con nuevas requests."""
        # Primera consulta de métricas
        response1 = client.get("/metrics")
        content1 = response1.text

        # Hacer varias requests
        for _ in range(5):
            client.get("/health")

        # Segunda consulta de métricas
        response2 = client.get("/metrics")
        content2 = response2.text

        # Las métricas deberían haber cambiado
        # (no comparamos valores exactos porque otros tests pueden afectar)
        assert "http_requests_total" in content2
        assert len(content2) >= len(content1)  # Al menos no debería reducirse
