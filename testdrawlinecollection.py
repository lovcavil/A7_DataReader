import glob,pandas
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as p3
import matplotlib.animation as animation

files = glob.glob("D:\Project\ODEA7\PTrun\\20190729-2\\a\\allMyNumbers*.csv")



dict0 = {}
dict0['Age'] = pandas.concat([pandas.read_csv(f ,index_col=False ) for f in files], ignore_index=True)
pair = ['time','x1','y1']
nd = np.array(dict0['Age'][pair]).T

def update_lines(num, dataLines, lines,ax):
    num=num*100+1
    for line, data in zip(lines, dataLines):
        # NOTE: there is no .set_data() for 3 dim data...
        line.set_data(data[0:2, :num])
        line.set_3d_properties(data[2, :num])

    s=data[1, :num]
    if abs(s.max(0))>abs(s.min(0)):
        r1=s.max(0)
    else:
        r1 =abs(s.min(0))

    s=data[2, :num]
    if abs(s.max(0))>abs(s.min(0)):
        r2=s.max(0)
    else:
        r2 =abs(s.min(0))

    if r1 > r2:
        r = r1
    else:
        r = r2
    ax.set_ylim3d([-r, r])
    ax.set_zlim3d([-r, r])


    return lines
# Attaching 3D axis to the figure
fig = plt.figure()
ax = p3.Axes3D(fig)

# Fifty lines of random 3-D lines
data = [nd]

# Creating fifty line objects.
# NOTE: Can't pass empty arrays into 3d version of plot()
lines = [ax.plot(dat[0, 0:1], dat[1, 0:1], dat[2, 0:1])[0] for dat in data]

# Setting the axes properties
ax.set_xlim3d([0, 2])
ax.set_xlabel('t')

ax.set_ylim3d([-0.001,0.001])
ax.set_ylabel('X')

ax.set_zlim3d([-0.001, 0.001])
ax.set_zlabel('Y')

ax.set_title('3D Test')

# Creating the Animation object
line_ani = animation.FuncAnimation(fig, update_lines, int(nd.shape[1]/100), fargs=(data, lines,ax),
                                   interval=1, blit=False)

plt.show()
pass
