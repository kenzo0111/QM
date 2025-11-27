# Quick import test to ensure create_map_visualization loads and supports both call styles
import sys
sys.path.append(r"c:\Users\Ramil\Downloads\QM")
from reporting import create_map_visualization
from types import SimpleNamespace

print('Loaded create_map_visualization signature OK')
# Call with accident_location kw (app.py style) at 60 fps
try:
    html = create_map_visualization(accident_location=(14.156, 122.83), accident_type='rear-end', severity='minor', entities=['Veh1'], timestamp=None, target_fps=30)
    print('App-style call OK, returned', type(html))
except Exception as e:
    print('App-style call raised:', repr(e))

# Simulate sim_data DataFrame-like object: provide object with 'columns' attr
class FakeDF(SimpleNamespace):
    columns = ['time', 'pos']

try:
    html2 = create_map_visualization(FakeDF(), vehicle1_name='Veh1', vehicle2_name=None, pedestrian_name=None, location='Bayabas', labo_geojson_path=None, collision_time=0.12, target_fps=30, animate_vehicles=False)
    print('Sim-data style call OK, returned', type(html2))
except Exception as e:
    print('Sim-data style call raised:', repr(e))
