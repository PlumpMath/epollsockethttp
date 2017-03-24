# -*- coding: utf-8 -*-
# http://docs.locust.io/en/latest/api.html#available-hooks
# http://blog.csdn.net/a464057216/article/details/48394213
# http://docs.locust.io/en/latest/testing-other-systems.html

# Locust支持并发，不采用高层的HttpLocust
from locust import Locust
# 支持任务场景描述
from locust import TaskSet,task
# 支持事件监听及钩子函数
from locust import events
# 支持时间戳
import time
# 支持socket
import socket
# 支持随机数
import random


# 任务场景描述
class Behavior(TaskSet):
    # 权重1
    @task(1)
    # 请求的是自己写的Asynchronous Socket Epoll HTTP SERVER, 单次连接通信完成后，SERVER通知客户端销毁SOCKET
    def ClientSocket(self):
        # 标记起始时间
        starttime = time.time()
        # 初始化client socket
        try:
            connFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            connFd.connect(('127.0.0.1', 8080))
            msg = 'The Number is %d'%random.randint(1,101)        
            data = msg.encode('utf-8')
            connFd.send(data)
            readData = connFd.recv(1024)
            print(readData.decode())
        except Exception,e:
            print 'Socket Connection Failed: %s '%e 
            # 保留两位小数，单位毫秒
            responsetime = round(((time.time()-starttime)*1000),2)       
            #失败+1
            events.request_failure.fire(request_type='socket', name='socketepoll', response_time=responsetime, exception=e)
        finally:
            connFd.close()
        
        # 保留两位小数，单位毫秒
        responsetime = round(((time.time()-starttime)*1000),2)       
        # 成功+1
        events.request_success.fire(request_type='socket', name='socketepoll', response_time=responsetime, response_length=30)
        

class User(Locust):
    task_set = Behavior
    min_wait = 1000
    max_wait = 1000

    
