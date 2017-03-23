import socket
import time

def sendmsg(i):
    connFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    connFd.connect(("127.0.0.1", 8080))
    msg = "The Number is %d" % i
    data = msg.encode(encoding="utf-8")
    connFd.send(data)
    readData = connFd.recv(1024)
    print(readData.decode())
    connFd.close()

for i in range(1,100001):
    sendmsg(i)
