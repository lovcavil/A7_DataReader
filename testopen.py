import os
# opens explorer at C:\ drive,just work for windows
start_directory = r'D:\Project\ODEA7\PTrun\01\cfg.ini'
os.startfile(start_directory)


import subprocess

main = r'D:\Project\ODEA7\PTrun\05\ODEA7.exe'
#if os.path.exists(main):
os.system(main)
#subprocess.Popen(main)