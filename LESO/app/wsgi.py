import sys

path = '/home/Verduu/WB-thesis-EV-dashboard'
if path not in sys.path:
    sys.path.append(path)

from dashapp import app
application = app.server
