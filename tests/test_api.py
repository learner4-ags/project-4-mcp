import pytest
from fastapi.testclient import TestClient
from app.main import app, compute_health
client=TestClient(app)

def test_thermal_v2_shape():
    body=client.get('/api/thermal').json()
    assert body['Sensor']=='CPU1'
    assert body['ReadingCelsius']==72.0
    assert body['Health']=='OK'
    assert 'TempC' not in body

@pytest.mark.parametrize('reading,expected',[(74.9,'OK'),(75,'Warning'),(84.9,'Warning'),(85,'Critical')])
def test_health_boundaries(reading,expected):
    assert compute_health(reading)==expected
