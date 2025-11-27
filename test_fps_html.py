import sys
sys.path.append(r"c:\Users\Ramil\Downloads\QM")
from reporting import create_map_visualization

html = create_map_visualization(accident_location=(14.156, 122.83), accident_type='rear-end', severity='minor', entities=['Veh1'], target_fps=30)
print('HTML len', len(html))
if 'PT0.033333S' in html:
    print('Period string for 30fps found')
else:
    print('Period string for 30fps NOT found')
