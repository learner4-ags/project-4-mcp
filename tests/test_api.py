from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_legacy_thermal_shape():
    body=client.get('/api/thermal').json(); assert body['Sensor']=='CPU1'; assert body['TempC']==72.0
