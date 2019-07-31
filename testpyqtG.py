import glob,pandas
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as p3
import matplotlib.animation as animation


import winsound
files = glob.glob("D:\Project\ODEA7\PTrun\\20190729-2\\a\\allMyNumbers*.csv")

def readfun(f):
    ret=pandas.read_csv(f, index_col=False)
    winsound.Beep(2500, 300)
    return ret


dict0 = {}
dict0['Age'] = pandas.concat([ readfun(f) for f in files], ignore_index=True)
pair = ['time','x1','y1']
nd = np.array(dict0['Age'][pair]).T

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time

app = QtGui.QApplication([])

p = pg.plot()
p.setWindowTitle('pyqtgraph example: PlotSpeedTest')
# p.setRange(QtCore.QRectF(0, -10, 5000, 20))
p.setLabel('bottom', 'Index', units='B')
curve = p.plot()
curve.setData(nd[0],nd[1],nd[2])
# curve.setFillBrush((0, 0, 100, 100))
# curve.setFillLevel(0)

# lr = pg.LinearRegionItem([100, 4900])
# p.addItem(lr)

data = np.random.normal(size=(50, 5000))

ptr = 0
lastTime = time()
fps = None


def update():
    global curve, data, ptr, p, lastTime, fps
    curve.setData(data[ptr])
    #ptr += 1
    now = time()
    dt = now - lastTime
    lastTime = now
    if fps is None:
        fps = 1.0 / dt
    else:
        s = np.clip(dt * 3., 0, 1)
        fps = fps * (1 - s) + (1.0 / dt) * s
    p.setTitle('%0.2f fps' % fps)
    app.processEvents()  ## force complete redraw for every plot


#timer = QtCore.QTimer()
#timer.timeout.connect(update)
#timer.start(0)

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
