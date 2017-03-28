# 基于Asynchronous Socket Epoll的简单HTTP服务器Demo
# 本HTTP SOCKET SERVER为TCP短暂连接实现，单次请求返回后即销毁SOCKET，故未考虑通信包的粘包问题
# 若是TCP长久连接通信，需要解决长连接的数据流粘包问题
# Author: WUWEI


#!/usr/bin/env python 
#-*- coding:utf-8 -*-

# 支持epoll
import select
# 支持socket
import socket
# 支持时间
import time 
# 支持日志记录
import logging,errno,sys


# 初始化日志对象 
logger = logging.getLogger('SocketServer')

# 定义日志输出函数
def initLog():
    try:      
        # 设置日志信息输出级别，一旦设置了日志等级，则调用比等级低的日志记录函数则不会输出
        # 当seLevel设置为DEBUG时，可以截获取所有等级的输出
        logger.setLevel(logging.DEBUG)
    
        # logging.FileHandler: 日志输出到文件
        fh = logging.FileHandler('log/socketserver.log')
        fh.setLevel(logging.DEBUG)
    
    
        # logging.StreamHandler: 日志输出到流，可以是sys.stderr、sys.stdout或者文件    
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.DEBUG)
    
        # 格式定义
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
    
        # logging有一个日志处理的主对象，其它处理方式都是通过addHandler添加进去的
        logger.addHandler(fh)
        logger.addHandler(ch)
    
        logger.debug('Create Logging Handler Successed\n')

    except socket.error as msg:
        logger.error('Create Logging Handler Failed',msg)
    

# 构造server响应信息
def makeResponseMsg():
    servertime = time.strftime('%a %b %d %H:%M:%S %Y', time.localtime())  
    response = 'SOCKET/1.0 RECEIVED OK Content-Type: Text/Plain %s\r\n'%servertime
    # 按utf-8的方式编码，将str转成bytes->b''
    response = response.encode(encoding='utf-8')
    return response

if __name__ == '__main__':
    initLog()

    try:
        # 生成服务端socket对象，此socket仅用于监听连接请求，不与客户端传输数据
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        # 允许bind()操作, 即使其他程序也在监听同样的端口. 否则这个程序只能在其他程序停止使用这个端口之后的1到2分钟后才能执行. 
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 监听port所有外部ip的请求
        serversocket.bind(('0.0.0.0', 8080)) 
        # listen(backlog),传入的值指定在拒绝连接之前，操作系统可以挂起的最大连接数量
        serversocket.listen(1)
        # 因为socket默认是阻塞的，设置为非阻塞（异步）模式
        serversocket.setblocking(0) 
    
        logger.debug('Create Server Socket Successed\n')
    
    except socket.error as msg:
        logger.error('Create Server Socket Failed',msg)

    try:    
        # 创建一个epoll对象 
        # EPOLLIN ：表示对应的文件描述符可以读
        # EPOLLOUT：表示对应的文件描述符可以写
        # EPOLLERR：表示对应的文件描述符发生错误
        # EPOLLHUP：表示对应的文件描述符被挂断
        # EPOLLET：表示对应的文件描述符设定为edge模式
        epoll = select.epoll() 

        # 在serversocket上面注册对读event的关注,当发生对serversocket的读事件时，引发一个事件
        epoll.register(serversocket.fileno(), select.EPOLLIN)
    except select.error as msg:
        logger.error('Register Server Socket Epoll Listening Failed',msg)
    
    try:
        # connections以socket.fileno()为键，以socket为值，将文件描述符（整数）映射到网络连接对象，一一对应 
        connections = {} 
        # requests以socket.fileno()为键，以对应传入数据为值，存储接收数据
        requests = {} 
        # responses以socket.fileno()为键，以对应响应数据为值，存储传出数据
        responses = {}
        while True:
            # 查询epoll对象，看是否有任何关注的event被触发。参数“1”表示，我们会等待1秒来看是否有event发生
            # 如果有任何我们感兴趣的event发生在这次查询之前，这个查询就会带着这些event的列表立即返回 
            events = epoll.poll(1) 
            # event作为一个序列（fileno，event code）的元组返回,fileno是文件描述符的代名词，始终是一个整数
            for fileno, event in events:
                # 首先events是epoll对注册对象的监听事件结果集，目前只监听了serversocket一个对象
                # 如果events有元素，则代表serversocket产生event,表示有一个新的连接进来（读事件）
            
            
                # 处理serversocket的逻辑，监听是否有外部连接事件，并分配clientsocket线程对象
                # fileno是epoll.register监听触发事件获取到的值，serversocket.fileno()是自己获取的值
                # 如果为真，代表有连接请求到serversocket产生event被epoll监听到了
                if fileno == serversocket.fileno(): 
                    # 进行 accept -- 获得连接上来 client 的 ip 和 port，以及 socket 句柄
                    connection, address = serversocket.accept()

                    logger.debug('SERVER SOCKET/1.0 Accept Connection From %s, %d, fd = %d' % (address[0], address[1], connection.fileno()))

                    # 设置新的socket为非阻塞模式
                    connection.setblocking(0) 

                    # 为新的客户端socket注册对读（EPOLLIN）event的关注 
                    epoll.register(connection.fileno(), select.EPOLLIN)

                    # 字典connections映射文件描述符（整数）到其相应的网络连接对象 
                    # connection.fileno()的值为fileno始终是一个整数，connection是socket对象
                    connections[connection.fileno()] = connection

                    # 初始化接收的数据 
                    requests[connection.fileno()] = b'' 
                    # 初始化响应的数据
                    responses[connection.fileno()] = makeResponseMsg()

                # 处理clientsocket的读event逻辑
                # 如果发生一个读event，就读取从客户端发送过来的新数据 
                # &与运算符，为1的话即真, event是epoll.poll(1)返回的events列表里的一个poll对象
                elif event & select.EPOLLIN:
                    # 接收客户端发送过来的数据,根据fileno，去connections里选出对应的socket，并存入requests对应的元素里
                    try:                    
                        requests[fileno] += connections[fileno].recv(1024) 
                        # 如果客户端退出,关闭客户端连接，取消所有的读和写监听
                        # 如果requests[fileno]不存在，代表没有在serversocket的逻辑的时候requests[connection.fileno()]初始化接收数据元素
                        if not requests[fileno]:
                            connections[fileno].close() 
                            # 删除connections字典中的监听对象
                            del connections[fileno] 
                            # 删除接收数据字典对应的句柄对象 
                            del requests[connections[fileno]] 
                            logger.debug('Client Connection Disconnected',connections, requests)
                            epoll.modify(fileno, 0) 
                        else:
                            # 完整请求已收到，注销对读event的关注，注册对写（EPOLLOUT）event的关注
                            epoll.modify(fileno, select.EPOLLOUT) 
                            logger.debug('RecvData: %s'%requests[fileno].decode())

                    except socket.error as msg:
                        logger.error('select.EPOLLIN failed',msg)
                
                
                
                # 处理clientsocket的写event逻辑
                elif event & select.EPOLLOUT: 
                    # 每次发送一部分响应数据，直到完整的响应数据都已经发送给操作系统等待传输给客户端
                    try:
                        byteswritten = connections[fileno].send(responses[fileno]) 
                        responses[fileno] = responses[fileno][byteswritten:] 
                        if len(responses[fileno]) == 0: 
                            # 一旦所有的响应数据都发送完, 取消监听读取和写入事件.
                            epoll.modify(fileno, 0) 
                            # 明确地让客户端socket断开
                            logger.debug('Response SendData Finished')
                            connections[fileno].shutdown(socket.SHUT_RDWR)
                    except socket.error as msg:
                        logger.error('select.EPOLLOUT failed',msg)


                # HUP（挂起）event表明客户端socket已经断开（即关闭），所以服务端也需要关闭
                # 不需要专门注册对HUP event的关注。在socket上面，它们总是会被epoll对象所默认关注 
                elif event & select.EPOLLHUP: 
                    try:
                        # 注销对此socket连接的关注 
                        epoll.unregister(fileno) 
                        # 关闭socket连接 
                        connections[fileno].close() 
                        del connections[fileno] 
                        logger.debug('EndHup Client Socket TearDown\n')
                    except socket.error as msg:
                        logger.error('select.EPOLLHUP failed',msg)

    finally: 
        # 显式关闭
        epoll.unregister(serversocket.fileno()) 
        epoll.close() 
        serversocket.close() 
        logger.debug('%s, %d Closed' % (addresses[fd][0], addresses[fd][1]))
