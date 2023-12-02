# 定义处理客户端请求的后端函数
import socket
import os

def backend(clientSocket):
    """
    处理所有请求的后端。
    :param clientSocket: 客户端套接字
    :return: 无返回值
    """
    requestData = clientSocket.recv(1024)  # 从客户端接收数据
    requestList = requestData.decode().split("\r\n")  # 对请求数据进行解码和分割
    reqHeaderLine = requestList[0]  # 获取请求头的第一行
    print("request line: " + reqHeaderLine)  # 打印请求行
    fileName = reqHeaderLine.split(" ")[1].split("/")[-1]  # 提取请求的文件名
    # 尝试打开请求的文件
    try:
        file = open("./" + fileName, 'rb')  # 从磁盘读取相应文件
    except FileNotFoundError:  # 如果文件不存在
        # 准备404 Not Found响应头
        responseHeader = "HTTP/1.1 404 Not Found\r\n" + \
                         "Server: 127.0.0.1\r\n" + "\r\n"
        responseData = responseHeader + "No such file\nCheck your input\n"
        # 组装完整的HTTP错误响应
        content = (responseHeader + responseData).encode("UTF-8")
        clientSocket.sendall(content)  # 向客户端发送错误响应
    else:  # 如果成功找到文件
        content = file.read()  # 读取文件内容到缓冲区
        file.close()
        # 准备200 OK响应头
        resHeader = "HTTP/1.1 200 OK\r\n"
        fileContent01 = "Server: 127.0.0.1\r\n"
        fileContent02 = content.decode()
        # 组装完整的HTTP响应
        response = resHeader + fileContent01 + "\r\n" + fileContent02
        clientSocket.sendall(response.encode("UTF-8"))  # 向客户端发送响应


# 定义启动服务器的函数
def startServer(serverAddr, serverPort):
    """
    使用（ip + 端口）启动服务器。
    :param serverAddr: 套接字监听的服务器地址（IPv4）
    :param serverPort: 套接字监听的服务器端口
    :return: 无返回值，数据将在控制台打印
    """
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建TCP套接字
    serverSocket.bind((serverAddr, serverPort))  # 绑定地址和端口
    serverSocket.listen(0)  # 开始监听
    while True:
        try:
            print("waiting for connecting...")
            clientSocket, clientAddr = serverSocket.accept()  # 接受一个新连接
            print("one connection is established and it's address is: %s" % str(clientAddr))
            backend(clientSocket)  # 调用后端函数处理请求
            clientSocket.close()  # 关闭客户端套接字
            print("client close")
        except Exception as err:  # 捕获异常
            print(err)
            break
    serverSocket.close()  # 关闭服务器套接字

startServer("", 8000)