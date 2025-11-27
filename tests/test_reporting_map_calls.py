import sys
from types import SimpleNamespace
sys.path.append(r"c:\Users\Ramil\Downloads\QM")
from reporting import create_map_visualization


def test_app_style_call():
    html = create_map_visualization(accident_location=(14.156, 122.83), accident_type='rear-end', severity='minor', entities=['Veh1'], target_fps=30)
    assert isinstance(html, str)
    # Check that the TimestampedGeoJson period is present for 30 fps
    assert 'PT0.033333S' in html


def test_simdata_style_call():
    class FakeDF(SimpleNamespace):
        columns = ['time', 'pos']
    html2 = create_map_visualization(FakeDF(), vehicle1_name='Veh1', vehicle2_name=None, pedestrian_name=None, location='Bayabas', animate_vehicles=False, target_fps=60)
    assert isinstance(html2, str)
