import json
from pathlib import Path
from mcp.server import MCPServer
mcp=MCPServer('hpe-contracts'); DATA=Path(__file__).parent/'data'
@mcp.resource('contract://thermal/v2', mime_type='application/json')
def thermal_contract()->dict: return json.loads((DATA/'thermal_v2.json').read_text())
@mcp.resource('standard://api-errors', mime_type='text/markdown')
def api_error_standard()->str: return (DATA/'api_error_standard.md').read_text()
@mcp.prompt(name='implement_thermal_v2')
def implement_thermal_v2(component:str='API and UI')->str:
    return f'''Implement ThermalReadingV2 for {component}. First attach/read resource contract://thermal/v2. Update API, UI, and tests consistently. Create a Playwright UI acceptance test that verifies the Health badge. Keep the change minimal and summarize compatibility impact before editing.'''
if __name__=='__main__': mcp.run()
