## build a QApplication before building other widgets
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import glob,pandas
import numpy as np
import time
import progressbar
import os
pg.mkQApp()

## make a widget for displaying 3D objects
import pyqtgraph.opengl as gl
view = gl.GLViewWidget()
view.show()
import winsound

rootfolder="D:\Project\ODEA7\PTrun\\"
picklefolder="F:\\A7data\\p\\"
folders=["20190729-cup-longer","20190729-cup-ctktup-longer"]
folder=folders[1]
files = glob.glob(rootfolder+folder+"\\a\\allMyNumbers*.csv")

bar = progressbar.ProgressBar(max_value=len(files))
prog_i = 0
def readfun(f,bar):
    global prog_i
    winsound.Beep(2500, 300)
    bar.update(prog_i)
    prog_i=prog_i+1
    return pandas.read_csv(f, index_col=False)
datas = {}
if os.path.exists(picklefolder+folder):
    print("read pickle")
    datas[folder] = pandas.read_pickle(picklefolder+folder)
else:
    print("read raw csv")
    datas[folder] = pandas.concat([ readfun(f,bar) for f in files], ignore_index=True)
    datas[folder].to_pickle(picklefolder+folder)

pair = ['time','x1','y1']
nd = np.array(datas[folder][pair])

## create three grids, add each to the view
xgrid = gl.GLGridItem()
ygrid = gl.GLGridItem()
zgrid = gl.GLGridItem()
view.addItem(xgrid)
view.addItem(ygrid)
view.addItem(zgrid)

p1 = gl.GLLinePlotItem(pos=nd)
view.addItem(p1)
## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
