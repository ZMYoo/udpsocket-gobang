# -*- coding:utf8 -*-
# Player.py
#__author__ : daijie
#__date__ : 20151117

#import standard packages
import socket
import json
import time
import os
import sys
import threading

REC_BUFFER_SIZE = 8192
TIMEOUT = 3000


class Threads(object):
    def __init__(self):
        self.threads = []

    def createThread(self,func,args=()):
        t = threading.Thread(target=func,args=args)
        t.setDaemon(True)
        self.threads.append(t)
        t.start()

    def run(self):
        alive = True
        while alive:
            alive = False
            threads_num = len(self.threads)
            for i in range(threads_num):
                alive = alive or self.threads[i].isAlive()

class UdpServer(object):
    def __init__(self,host="0.0.0.0",port=9999):
        '''
        :param host: 服务器IP
        :param port: 服务端口
        :clients = {
            client_id : {
                address : address
                nickname : nickname
                timeout:20
            }
        }
        :pair = [ clients_id_a , clients_id_b ]
        :return:
        '''
        self.host = host
        self.port = port
        self.clients = {}
        self.running = True
        self.N = 5
        self.pair = [['0','0'] for i in range(self.N)]
        self.startServer()

    def startServer(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.running = True
            print("服务开启，%s:%d"% (self.host,self.port))
        except Exception:
            print("error")

    def parseCommand(self):
        '''
        1.	/msg [playerid]
        群发和向指定用户发送消息，用以某些提示。
        2.	/list
        列出所有玩家的列表及其参加棋局的情况。
        3.	/kickout playerid
        将某玩家踢出游戏，以防止一些捣乱的玩家，如长时间不走棋。并且向参加该棋局中的对方玩家发送踢出的消息。
        4.	/opengame  gameName
        开通新的棋局
        5.  /games
        列出当前正在比赛的棋局。
        6.  /watch gameName
        可以观看某一棋局的比赛情况，可以list，kickout playerid命令。直到使用leave命令离开该棋局。
        7.	/closegame gameName
        关闭某一棋局。
        :return:
        '''
        while self.running:
            print()
            cmd = input(">>>请输入执行命令，输入/?可以查看帮助\n")
            if not len(cmd) or cmd[0] != '/':
                print("无效的命令，命令需要以 / 开头  ",end="")
                continue
            cmd = cmd[1:].split(' ')
            if cmd[0] == "?":
                os.system('cls')
                print("   /msg [playid] 向用户发送消息，例如/msg 蛤蛤")
                print("   /list，列出所有玩家的列表及其参加棋局的情况")
                print("   /kickout play_id，踢出玩家")
                print("   /opengame，新增一个棋局")
                print("   /games，查看比赛情况")
                print("   /watch id，观战，id为桌号，例如/watch 5")
                print("   /closegame id，关闭某一棋局，id为桌号，例如/closegame 2")

            elif cmd[0] == "list":
                client_ids = list(self.clients.keys())
                for key in client_ids:
                    cnt = 0
                    flag = 0
                    for i,j in self.pair:
                        cnt += 1
                        if i == key or j == key:
                            flag = 1
                            print("玩家%s在第%d局" %(key,cnt))
                            break
                    if flag == 0:
                        print("玩家%s未加入任何棋局"% key)
                if not len(client_ids):
                    print("没有玩家加入")
            elif cmd[0] == "games":
                cnt =0
                for i,j in self.pair:
                    cnt += 1
                    if i != "0" and j !="0" :
                        print("第%d局，%s 对战 %s" % (cnt,i,j))
                    elif i!= "0":
                        print("第%d局，玩家%s在等待"% (cnt,i))
                    elif j!= "0":
                        print("第%d局，玩家%s在等待"% (cnt,j))
                    else:
                        print("第%d局，暂时没有任何玩家加入"% cnt)
            elif cmd[0] == "msg":
                if len(cmd) > 2 and len(cmd[2]):
                    if cmd[1] in self.clients:
                        self.packAndSend(client_id = cmd[1], msg= {
                            'action':"message",
                            'value':cmd[2]
                        })
                        print("已经成功向该用户发送消息")
                    else:
                        print("用户不存在")
                elif len(cmd) > 1:
                    print("向所有用户群发消息")
                    self.packAndSend(msg ={
                        'from':'admin',
                        'action':"message",
                        'value':cmd[1]
                    })
                else:
                    print("无效的命令")
            elif cmd[0] == "kickout":
                client_id = cmd[1]
                client_ids = self.clients.keys()
                if client_id not in client_ids:
                    print("玩家不存在")
                else:
                    for each in self.pair:
                        if each[0] == client_id or each[1] == client_id:
                            if each[0] == client_id:
                                opp = 1
                                each[0] = "0"
                            else:
                                opp = 0
                                each[1] = "0"
                            self.packAndSend('admin',client_id,{
                                'action':'kickout',
                                'value':"你已经被系统管理员踢出"
                            })
                            if each[opp] == "0":
                                print("该用户未加入任何棋局")
                            else:
                                self.packAndSend('admin',each[opp],{
                                    'action':'win',
                                    'value':"对方被管理员踢出，系统判定您获胜"
                                })
                            break
            elif cmd[0] == "opengame":
                self.N += 1
                self.pair.append(['0','0'])
                print("新增棋局成功")
            elif cmd[0] == "closegame":
                if len(cmd) > 1 and cmd[1].isdigit():
                    no = int(cmd[1]) -1
                    if self.N <= no :
                        print("该棋局不存在")
                    elif self.pair[no][0] == "0" or self.pair[no][1] == "0":
                        print("该棋局并没有开始游戏")
                    else:
                        for i in range(2):
                            self.packAndSend("admin",self.pair[no][i],{
                                'action':'closegame',
                                'value': '管理员已经将该棋局关闭'
                            })
                        self.pair[no][0] = self.pair[no][1] = "0"
                        print("该棋局已经被关闭，并通知了双方玩家")
                else:
                    print("命令无效")
            elif cmd[0] == "watch":
                if len(cmd) > 1 and cmd[1].isdigit():
                    no = int(cmd[1]) -1
                    if self.N <= no :
                        print("该棋局不存在")
                    elif self.pair[no][0] == "0" or self.pair[no][1] == "0":
                        print("该棋局并没有开始游戏")
                    else:
                        self.packAndSend("admin",self.pair[no][0],{
                            'action':'watch',
                            'value': ''
                        })
                        print("已经发出观战请求")
                else:
                    print("命令无效")
            else:
                print("命令无效")

    def packAndSend(self, msg_from = "admin",client_id = "ALL", msg = None):
        '''
        :param client_id: 储存的客户端的 id ,默认是ALL，向所有客户端广播
        :param msg: 字典，需要打包的消息，例如{'msg':'你真棒','move':'77'}
        :return: pack message and sent to
        '''
        if not msg : msg = {}
        msg['from'] = msg_from
        msg['nickname'] = "管理员"
        if msg_from != "admin":
            msg['nickname'] = self.clients[msg_from]['nickname']
        pack_msg = json.JSONEncoder().encode(msg)
        client_ids = self.clients.keys() if client_id == "ALL" else  [client_id]
        try:
            for key in client_ids:
                self.server.sendto(pack_msg.encode('utf8'),self.clients[key]['address'])
        except KeyError:
            return

    def parseMsg(self):
        while self.running:
            try:
                data, address = self.server.recvfrom(REC_BUFFER_SIZE)
            except ConnectionResetError:
                continue

            host = address[0]
            port = address[1]
            client_id = host + str(port)
            data = json.JSONDecoder().decode(data.decode('utf8'))
            if client_id not in self.clients:
                self.clients.setdefault(client_id,{
                    'address':address,
                    'nickname': data['nickname'],
                    'timeout':TIMEOUT,
                })
            self.clients[client_id]['timeout'] = TIMEOUT
            action = data['action']
            value = data['value']
            if data['to'] == 'admin':
                if action == 'login':
                    self.packAndSend("admin",client_id, {
                        'action':'message',
                        'value': '连接服务器成功',
                    })
                elif action == "join":
                    table = self.pair[int(value)]
                    if table[0] == table[1] == '0':
                        table[0] = client_id
                        self.packAndSend("admin",client_id,{
                            'action':'join',
                            'value':'success',
                        })
                    elif table[0] =='0' or table[1] == '0':
                        no = 0 if table[0] == '0' else 1
                        table[no] = client_id
                        other = table[(no + 1)%2]
                        msg = {
                            'action':'join',
                            'value':'%s:%s:black'% (self.clients[other]['nickname'],other)
                        }
                        self.packAndSend("admin",client_id,msg)
                        msg['value'] = '%s:%s:white'% (self.clients[client_id]['nickname'], client_id)
                        self.packAndSend("admin",other,msg)
                    else:
                        self.packAndSend("admin",client_id,{
                            'action':'join',
                            'value':'fail',
                        })
                elif action == 'games':
                    cnt = 0
                    res = []
                    for i,j in self.pair:
                        cnt += 1
                        if i != "0" and j !="0" :
                            res.append("第%d局 %s对战%s" % (cnt, self.clients[i]['nickname'] ,self.clients[j]['nickname']))
                        elif i!= "0":
                            res.append("第%d局 %s在等待" % (cnt,self.clients[i]['nickname']))
                        elif j!= "0":
                            res.append("第%d局 %s在等待"% (cnt,self.clients[j]['nickname']))
                        else:
                            res.append("第%d局 空"% cnt)

                    self.packAndSend('admin',client_id,{
                        'action':'games',
                        'value': res
                    })
                elif action == "list":
                    client_ids = list(self.clients.keys())
                    res = []
                    for key in client_ids:
                        cnt = 0
                        flag = 0
                        for i,j in self.pair:
                            cnt += 1
                            if i == key or j == key:
                                flag = 1
                                res.append("玩家%s在第%d局" %(self.clients[key]['nickname'],cnt))
                                break
                        if flag == 0:
                            res.append("玩家%s未加入任何棋局" % self.clients[key]['nickname'] )
                    if not len(client_ids):
                        res.append("没有玩家加入")
                    self.packAndSend('admin',client_id,{
                        'action':'list',
                        'value': res
                    })
                elif action == "watch":
                    time.sleep(1)
                    for x in range(8):
                        for y in range(8):
                            if value[y][x] == "*":
                                print("+ ",end="")
                            elif value[y][x] == "1":
                                print("* ",end="")
                            elif value[y][x] == "0":
                                print("o ",end="")
                        print()
            else:
                if action == "leave":
                    for table in self.pair:
                        if table[0] == client_id or table[1] == client_id:
                            table[0] = table[1] = "0"
                self.packAndSend(client_id,data['to'],{
                    'action':data['action'],
                    'value':value
                })

    def clearOfflineUser(self):
        while self.running:
            time.sleep(1)
            client_ids = list(self.clients.keys())
            for key in client_ids:
                self.clients[key]['timeout'] -= 1
                if self.clients[key]['timeout'] > 0:
                    continue
                self.packAndSend('admin',key,{
                    'action':'kickout',
                    'value':"长时间不走棋被自动踢出棋局"
                })
                self.clients.pop(key)
                for i in range(self.N):
                    a , b = self.pair[i][0] , self.pair[i][1]
                    if (a != key and b != key):
                        continue
                    elif ( a == key and b == "0" ) or (b == key and a == '0'):
                        self.pair[i] = ['0','0']
                    elif a == key or b == key:
                        self.pair[i][0 if a == key else 1] ='0'
                        self.packAndSend('admin',(b if a == key else a ),{
                            'action':'win',
                            'value':"对方长时间不走棋，系统判定您获胜"
                        })
    def closeServer(self):
        print("close")
        self.server.close()
        self.running = False
        exit()

if __name__ == "__main__":
    while True:
        config_port = input("输入端口，按回车默认为9999: ")
        if config_port and config_port.isdigit():
            config_port = int(config_port)
            if config_port > 1024:
                break
            print("端口至少1025")
        else:
            config_port = 9999
            break

    udp_server = UdpServer(port=config_port)
    threads_manager = Threads()
    threads_manager.createThread(udp_server.parseMsg)
    threads_manager.createThread(udp_server.parseCommand)
    threads_manager.createThread(udp_server.clearOfflineUser)
    threads_manager.run()