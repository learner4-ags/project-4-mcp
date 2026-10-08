from fastapi import FastAPI
from fastapi.responses import HTMLResponse
app=FastAPI(title='Thermal Console')
SENSOR='CPU1'
READING_CELSIUS=72.0

# Health thresholds per contract://thermal/v2: OK <75, Warning 75-84.9, Critical >=85
def compute_health(reading_celsius:float)->str:
    if reading_celsius>=85:
        return 'Critical'
    if reading_celsius>=75:
        return 'Warning'
    return 'OK'

@app.get('/health')
def health(): return {'status':'ok'}
@app.get('/api/thermal')
def thermal():
    return {'Sensor':SENSOR,'ReadingCelsius':READING_CELSIUS,'Health':compute_health(READING_CELSIUS)}
@app.get('/',response_class=HTMLResponse)
def home():
    return HTMLResponse('''<!doctype html><html><head><meta charset='utf-8'><title>Thermal Console</title><style>body{font-family:Arial;margin:40px}.badge{padding:6px 10px;border-radius:14px;background:#ddd}.badge-ok{background:#c8f7c5}.badge-warning{background:#ffe8a3}.badge-critical{background:#f7b7b7}</style></head><body><h1>Thermal Console</h1><p>Sensor: <span id='sensor'></span></p><p>Reading: <span id='reading'></span> °C</p><span id='health' class='badge'>Unknown</span><script>fetch('/api/thermal').then(r=>r.json()).then(x=>{sensor.textContent=x.Sensor;reading.textContent=x.ReadingCelsius;const h=document.getElementById('health');h.textContent=x.Health;h.className='badge badge-'+x.Health.toLowerCase();});</script></body></html>''')
