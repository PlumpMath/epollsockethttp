import socket
import select  # select带有epoll功能

EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response  = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(1)
serversocket.setblocking(0) # 设置socket为非阻塞(异步)模式

epoll = select.epoll() # 建立一个epoll对象
epoll.register(serversocket.fileno(), select.EPOLLIN) # 注册监听读取事件，服务器socket接收一个连接的时候, 产生一个读取事件

try:
    connections = {}; requests = {}; responses = {} # connections表映射文件描述符(file descriptors, 整型)到对应的网络连接对象上面. 
    while True:
        events = epoll.poll(1) # events为事件列表，返回的events是一个(fileno, event code)tuple列表. fileno是文件描述符, 是一个整型数.
        for fileno, event in events:
            if fileno == serversocket.fileno(): # 如果是服务端产生event,表示有一个新的连接进来 
                connection, address = serversocket.accept() # 对新的连接建立一个socket，在别的线程，用于客户端通信
                print('fileno %d connected from: %s'%(fileno,address)) # 打印信息调试

                connection.setblocking(0) # 设置socket为非阻塞(异步)模式
                epoll.register(connection.fileno(), select.EPOLLIN) # 注册socket的read(EPOLLIN)事件
                connections[connection.fileno()] = connection # connections = {},把connection这个socket的文件描述符存入connections字典
                requests[connection.fileno()] = b'' # requests = {};
                responses[connection.fileno()] = response # responses = {}
            
            elif event & select.EPOLLIN: # 如果发生一个读event，就读取从客户端发送过来的新数据
                requests[fileno] += connections[fileno].recv(1024)
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    epoll.modify(fileno, select.EPOLLOUT) #  取消注册读取事件, 注册写入事件(EPOLLOUT)
                    print('-'*40 + '\n' + requests[fileno].decode()[:-2])

            elif event & select.EPOLLOUT:
                byteswritten = connections[fileno].send(responses[fileno])
                responses[fileno] = responses[fileno][byteswritten:]
                if len(responses[fileno]) == 0:
                    epoll.modify(fileno, 0)
                    connections[fileno].shutdown(socket.SHUT_RDWR)

            elif event & select.EPOLLHUP:
                epoll.unregister(fileno)
                connections[fileno].close()
                del connections[fileno]
finally:
    epoll.unregister(serversocket.fileno())
    epoll.close()
    serversocket.close()





