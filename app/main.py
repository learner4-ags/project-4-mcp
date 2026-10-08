from fastapi import FastAPI
from fastapi.responses import HTMLResponse
app=FastAPI(title='Thermal Console')
SAMPLE={'Sensor':'CPU1','TempC':72.0}
@app.get('/health')
def health(): return {'status':'ok'}
@app.get('/api/thermal')
def thermal(): return SAMPLE
@app.get('/',response_class=HTMLResponse)
def home():
    return HTMLResponse('''<!doctype html><html><head><meta charset='utf-8'><title>Thermal Console</title><style>body{font-family:Arial;margin:40px}.badge{padding:6px 10px;border-radius:14px;background:#ddd}</style></head><body><h1>Thermal Console</h1><p>Sensor: <span id='sensor'></span></p><p>Reading: <span id='reading'></span> °C</p><span id='health' class='badge'>Unknown</span><script>fetch('/api/thermal').then(r=>r.json()).then(x=>{sensor.textContent=x.Sensor;reading.textContent=x.TempC;});</script></body></html>''')
