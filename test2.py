import sys
from PyQt5 import QtCore, QtGui

def startCount():
    timer.start(1000)

def showNum():
    global count
    count = count + 1
    print(count)
    if count > 10:
        app.quit()

print('strating')
app = QtCore.QCoreApplication(sys.argv)

timer = QtCore.QTimer()
count = 0
timer.timeout.connect(showNum)
startCount()

app.exec_()
print('finished')
