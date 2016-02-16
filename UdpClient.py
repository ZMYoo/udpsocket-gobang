# -*- coding:utf8 -*-
# Game.py
#__author__ : daijie
#__date__ : 20151117

#import standard packages
import sys
import socket
import json
import time

#import PyQt5
from PyQt5.QtWidgets import (QDesktopWidget,QApplication,qApp,QMainWindow,QWidget,QPushButton,QLabel,QMessageBox,QLineEdit,
                             QTextEdit,QDialog,QAction,QGridLayout)
from PyQt5.QtCore import Qt,QThread,pyqtSignal
from PyQt5.QtGui import QIcon,QPixmap,QPainter

#import own packages
from utils import Othello

UI_WIDTH = 800
UI_HEIGHT = UI_WIDTH * 0.72
BOARD_WIDTH = UI_WIDTH * 0.53
BOARD_BORDER = BOARD_WIDTH * 0.07925
BOARD_L = BOARD_WIDTH * 0.1052

REC_BUFFER_SIZE = 8192


class Game(QMainWindow):
    def __init__(self,host="localhost",port=9999,nickname="wa"):
        super(Game, self).__init__()
        #常量
        self.BLACK = 'images/black.png'
        self.WHITE = 'images/white.png'
        self.ME ="me"
        self.YOU = "you"
        self.ADMIN = "admin"
        #是否正在进行游戏
        self.nickname = nickname
        self.opponent = {
            'nickname':'',
            'client_id':'',
            'role':'',
        }
        self.host = str(host)
        self.port = int(port)
        self.playing = False
        # 设置标题、图标等
        self.setWindowTitle('黑白棋')
        self.setWindowIcon(QIcon('images/icon.jpg'))
        # 创建布局
        self.createGrid()
        # 创建菜单
        self.createMenu()
        #导入样式表
        self.createStyleQss()
        # 初始化类
        self.initGame()
        # 网络连接，并且为网络连接单独建立一个线程
        self.createConnection()

    def __str__(self):
        return "<p style='text-align:center'>网络编程黑白棋作业</p>" \
            "<p style='text-align:left'>学号：13300240008</p>" \
            "<p style='text-align:left'>姓名：代杰</p>" \
            "<p style='text-align:left'>专业：保密管理</p>"

    def initGame(self):
        self.statusBar().showMessage("准备就绪")
        self.setTurnImage(self.BLACK)
        self.displayScores(2,2)
        self.edit.clear()
        self.messages.clear()
        self.move_record.setText("游戏未开始")
        self.playing = False

    def restartGame(self):
        #重新开始游戏，初始化 Game、Othello、Board、Controller
        self.initGame()
        self.othello.initOthello()
        self.board.initBoard(self.othello)

    def createStyleQss(self):
        file = open('style.css','r')
        style = file.read()
        qApp.setStyleSheet(style)
        file.close()

    def createConnection(self):
        self.connect = True
        self.client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.client.connect((self.host,self.port))
        self.packAndSend({
            'action':'login',
            'value': self.nickname,
            'to':'admin'
        })

    def createGrid(self):
        def btn_restart_game():
            if self.playing:
                self.packAndSend({
                    'to':self.opponent['client_id'],
                    'action':'restart',
                    'value': 'apply'
                })
            else:
                QMessageBox.information(self,'系统消息',"没有加入任何游戏")
                self.restartGame()
        def btn_leave_game():
            if self.playing:
                self.packAndSend({
                    'to':self.opponent['client_id'],
                    'action':'leave',
                    'value': ''
                })
                self.restartGame()
            else:
                QMessageBox.information(self,'系统消息',"没有加入任何游戏")
        #设置主窗口的大小与位置
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry( (screen.width() - UI_WIDTH)/2 ,( screen.height() - UI_HEIGHT )/2,UI_WIDTH,UI_HEIGHT)
        self.setFixedSize(UI_WIDTH,UI_HEIGHT)
        #创建布局
        main = QWidget(self)
        main.setObjectName('main')
        self.setCentralWidget(main)
        self.othello = Othello()
        self.board = Board(main,self.othello)
        self.hall = Hall(self)

        #创建应该下子的图片标志，初始化为黑子
        pic = QLabel(self)
        pic.setGeometry(UI_WIDTH*0.212,UI_HEIGHT*0.12,50,50)
        pic.setObjectName('label_for_turn_image')

        #创建功能按钮
        buttons = QWidget(self)
        buttons.setGeometry(UI_WIDTH*0.77,UI_HEIGHT*0.4,UI_WIDTH*0.2,UI_HEIGHT*0.12)
        buttons.setObjectName('buttons')
        btn_restart = QPushButton('重新开始',self)
        btn_list = QPushButton('玩家列表',self)
        btn_leave = QPushButton('离开',self)
        btn_hall = QPushButton('大厅',self)
        grid = QGridLayout()
        grid.addWidget(btn_restart,0,0)
        grid.addWidget(btn_list,0,1)
        grid.addWidget(btn_leave,1,0)
        grid.addWidget(btn_hall,1,1)
        buttons.setLayout(grid)
        btn_restart.clicked.connect(btn_restart_game)
        btn_list.clicked.connect(lambda:self.packAndSend({'to':'admin','action':'list','value': '玩家列表'}))
        btn_hall.clicked.connect(lambda:self.packAndSend({'to':'admin','action':'games','value': '列出大厅'}))
        btn_leave.clicked.connect(btn_leave_game)
        #创建分数显示屏,包括黑棋得分，黑棋昵称，白棋得分，白棋昵称
        self.score_black = QLabel(self)
        self.score_black.setObjectName('score_black')
        self.score_black.setGeometry(UI_WIDTH*0.08,UI_HEIGHT*0.25,100,60)
        self.nickname_black = QLabel("<p style='text-align:center'>黑棋</p>",self)
        self.nickname_black.setObjectName('nickname_black')
        self.nickname_black.setGeometry(UI_WIDTH*0.03,UI_HEIGHT*0.36,120,60)

        self.score_white = QLabel(self)
        self.score_white.setObjectName('score_white')
        self.score_white.setGeometry(UI_WIDTH*0.08,UI_HEIGHT*0.57,100,60)
        self.nickname_white = QLabel("<p style='text-align:center'>白棋</p>",self)
        self.nickname_white.setObjectName('nickname_white')
        self.nickname_white.setGeometry(UI_WIDTH*0.03,UI_HEIGHT*0.68,120,60)
        self.move_record =  QTextEdit("当前下子情况",self)
        self.move_record.setReadOnly(True)
        #显示走棋的位置
        self.move_record =  QTextEdit("下子情况",self)
        self.move_record.setObjectName("move_record")
        self.move_record.setReadOnly(True)
        self.move_record.setGeometry(UI_WIDTH*0.765,UI_HEIGHT*0.24,UI_WIDTH*0.215,UI_HEIGHT*0.15)

        #创建输入框
        chat = QWidget(self)
        chat.setObjectName('chat')
        chat.setGeometry(UI_WIDTH*0.755,UI_HEIGHT*0.54,UI_WIDTH*0.235,UI_HEIGHT*0.45)
        grid = QGridLayout()
        chat.setLayout(grid)
        # 聊天窗口
        self.messages = QTextEdit("欢饮来到呆尐兔兔五子棋,撒花~~~",self)
        self.messages.setReadOnly(True)
        self.edit = QLineEdit(self)
        btn_send_msg = QPushButton("Enter/发送",self)
        btn_send_msg.clicked.connect(self.chat)
        grid.addWidget(self.messages,0,0,10,10)
        grid.addWidget(self.edit,10,0,2,8)
        grid.addWidget(btn_send_msg,10,8,2,2)

    def createMenu(self):
        def quitGame():
            #退出信号槽函数
            reply = QMessageBox.question(self,'问题','想要退出吗',QMessageBox.Yes,QMessageBox.No)
            if reply == QMessageBox.Yes:
                qApp.quit()

        def aboutUs():
            QMessageBox.about(self,'关于作者',str(self))

        menubar = self.menuBar()
        #主菜单
        main_menu = menubar.addMenu('&主菜单')
        main_menu.addAction(QAction(QIcon('images/icon.jpg'),'退出',
                                 self, statusTip="退出黑白棋游戏", triggered=quitGame))
        #关于菜单
        about_menu = menubar.addMenu('&关于')
        about_menu.addAction(QAction(QIcon('images/icon.jpg'),'作者',
                                 self, statusTip="作者信息", triggered=aboutUs))

    def setTurnImage(self,turn_image=None):
        if turn_image:
            pic_l = 30
            pic = self.findChild(QLabel,'label_for_turn_image')
            pic.setPixmap(QPixmap(turn_image).scaled(pic_l,pic_l))
        else:
            game_othello.setWhoFirst()
            QMessageBox.information(self,"提示","已选择" + ("黑棋" if game_othello.isBlack() else "白棋") + "优先")
            if game_othello.isBlack():
                self.setTurnImage(self.BLACK)
            else:
                self.setTurnImage(self.WHITE)

    def displayScores(self,black=0,white=0):
        #显示分数
        if not ( black and white):
            n = game_othello.N
            black = white = 0
            for x in range(n):
                for y in range(n):
                    if game_othello.isBlack(x,y):
                        black += 1
                    elif game_othello.isWhite(x,y):
                        white += 1
        self.score_white.setText(str('%02d' % white))
        self.score_black.setText(str('%02d' % black))
        return black,white

    def getBoard(self):
        #返回棋局
        return self.board

    def getOthello(self):
        #返回逻辑五子棋
        return self.othello

    def keyPressEvent(self,event):
        key = event.key()
        if key == Qt.Key_Enter or key == Qt.Key_Return:
            self.chat()

    def isTurnMe(self):
        return (game_othello.isBlack() and self.opponent['role'] == "white" ) \
               or (game.othello.isWhite() and self.opponent['role'] == "black")

    def chat(self, src = None, nickname=None, msg = None):
        def packMsg(src,name,msg):
            color = {
                self.ADMIN : "blue",
                self.ME: "white",
                self.YOU: "wheat"
            }
            packed = "<span style='color: %s '> %s : %s</span>" % ( color[src], name , msg )
            return packed

        if not src:
            send_msg = self.edit.text()
            if send_msg and len(send_msg):
                self.edit.clear()
                self.messages.append(packMsg(self.ME ,self.nickname,send_msg ))
                if self.playing:
                    self.packAndSend({
                        'to':self.opponent['client_id'],
                        'action' : 'message',
                        'value': send_msg
                    })
        else:
            self.messages.append(packMsg(src, nickname, msg))

    def parseMsg(self,msg_str):
        data = json.JSONDecoder().decode(msg_str)
        action = data['action']
        value = data['value']
        nickname = data['nickname']

        if data['from'] == "admin":
            if action == "message":
                self.chat(self.ADMIN , nickname , value)
            elif action == "kickout":
                QMessageBox.information(self,"系统消息","你已经被踢出棋局，原因是" + value,QMessageBox.Yes)
                self.restartGame()
            elif action == "leave":
                QMessageBox.question(self,"系统消息","对方玩家请求离开，是否同意？",QMessageBox.Yes)
            elif action == "join":
                if value == "fail":
                    QMessageBox.information(self,'系统消息',"该棋局已满，请选择其他棋局")
                elif value == "success":
                    self.hall.hide()
                    QMessageBox.information(self,'系统消息',"你已经加入棋局，等待其他玩家进入棋局")
                else:
                    self.restartGame()
                    name,client_id,role = value.split(':')
                    self.opponent['role'] = role
                    self.opponent['client_id']= client_id
                    self.opponent['nickname'] = name
                    self.playing = True
                    self.hall.hide()
                    #根据系统分配的角色，显示双方昵称，初始化棋子
                    if role == "black" :
                        self.move_record.setText("游戏开始，我方白棋后手")
                        QMessageBox.information(self,'提示','您是白棋\r\n白棋后手')
                        self.nickname_black.setText("<p style='text-align:center'>%s</p>" % name)
                        self.nickname_white.setText("<p style='text-align:center'>%s</p>" % self.nickname)
                    elif role == "white" :
                        self.move_record.setText("游戏开始，我方黑棋先手")
                        QMessageBox.information(self,'提示','您是黑棋\r\n黑棋先手')
                        self.nickname_black.setText("<p style='text-align:center'>%s</p>" % self.nickname)
                        self.nickname_white.setText("<p style='text-align:center'>%s</p>" % name)
            elif action == "games":
                self.hall.showHall(value)
            elif action == "list":
                res = ""
                print(value)
                for i in value:
                    res += i + '\r\n'
                QMessageBox.information(self,"玩家列表",res)
            elif action == "closegame":
                QMessageBox.information(self,"系统消息",value)
                self.restartGame()
            elif action == "win":
                QMessageBox.information(self,"系统消息",value)
                self.restartGame()
            elif action == "watch":
                self.packAndSend({
                    'to':'admin',
                    'action':'watch',
                    'value': self.othello.board
                })
        else:
            if action == "move":
                x ,y  = int(value[0]) , int(value[1])
                game_board.placePiece(x,y)
            elif action == "message":
                self.chat(self.YOU, nickname, value)
            elif action == "restart":
                if value == "apply":
                    reply = QMessageBox.question(self,"系统消息","对方请求重新开始游戏，是否同意",QMessageBox.Yes,QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.packAndSend({
                            'to':self.opponent['client_id'],
                            'action':'restart',
                            'value':'agree'
                        })
                        self.restartGame()
                        self.playing = True
                    else:
                        self.packAndSend({
                            'to':self.opponent['client_id'],
                            'action':'restart',
                            'value':'refuse'
                        })
                elif value == "agree":
                    QMessageBox.information(self,"系统消息","对方同意了您的请求")
                    self.restartGame()
                    self.playing = True
                elif value == "refuse":
                    QMessageBox.information(self,"系统消息","对方拒绝了您的请求")
            elif action == "leave":
                self.restartGame()
                QMessageBox.information(self,"系统消息","对方离开了棋局")

    def packAndSend(self, msg=None):
        '''
        :param msg: 字典，需要打包的消息，例如{'msg':'你真棒','move':'77'}
        :return: pack message and sent to
        '''
        msg = {} if not msg else msg
        msg['nickname'] = self.nickname
        pack_msg = json.JSONEncoder().encode(msg)
        self.client.sendall(pack_msg.encode('utf8'))


class Board(QWidget):
    def __init__(self,parent=None,othello = None):
        super(Board,self).__init__(parent)
        #设置常量
        self.setObjectName('board')

        self.BLACK = "images/black.png"
        self.WHITE = "images/white.png"
        self.READY = "images/available_pos.png"
        #初始化棋盘
        self.initBoard(othello)

    def paintEvent(self,event):
        painter=QPainter(self)
        painter.drawPixmap(0,0,QPixmap("images/board.jpg").scaled(BOARD_WIDTH,BOARD_WIDTH))
        self.move(UI_WIDTH * 0.201 ,UI_HEIGHT * 0.1 )

    def initBoard(self,othello):
        #初始化棋盘
        n = othello.N
        for x in range(n):
            for y in range(n):
                if othello.isBlack(x,y):
                    self.placePieceImage(x, y, self.BLACK)
                elif othello.isWhite(x,y):
                    self.placePieceImage(x, y, self.WHITE)
                else:
                    label = self.getPiece(x, y)
                    if label:
                        label.hide()
        #记录上一次可以落子的位置
        self.last_available_pos = []

    def mousePressEvent(self,event):
        if not game.playing:
            QMessageBox.information(self,"警告","您未加入任何棋局，点击大厅可加入")
            return
        if not game.isTurnMe():
            QMessageBox.information(self,"警告","等待对方走棋")
            return

        _x = event.x()
        _y = event.y()
        x = round((_x - BOARD_BORDER - BOARD_L/2 )/BOARD_L )
        y = round((_y - BOARD_BORDER - BOARD_L/2)/BOARD_L )
        #下子
        self.placePiece(x,y)

    def placePiece(self,x,y):
        #返回可以翻转的子
        ready_for_reverse = game_othello.placePiece(x, y)
        if ready_for_reverse and len(ready_for_reverse):
            if game.isTurnMe():
                game.packAndSend({
                    'to':game.opponent['client_id'],
                    'action':'move',
                    'value': str(x) + str(y)
                })
            #如果可以下子，则下子
            if game_othello.isBlack():
                self.placePieceImage(x, y, self.BLACK)
                for i,j in ready_for_reverse:
                    self.placePieceImage(i, j, self.BLACK)
                game.move_record.append("黑棋落子 %d %d"% (x+1,y+1))
            else:
                self.placePieceImage(x, y, self.WHITE)
                for i,j in ready_for_reverse:
                    self.placePieceImage(i, j, self.WHITE)
                game.move_record.append("白棋落子 %d %d"% (x+1,y+1))
            #显示分数，并且判断游戏是否结束
            b_score , w_score = game.displayScores()
            available_pos = game_othello.setWhoTurn()
            #判断游戏是否结束
            if not game_othello.game_over:
                if game_othello.isBlack():
                    game.setTurnImage(game.BLACK)
                else:
                    game.setTurnImage(game.WHITE)
                #游戏未结束，显示下一个可下子的地方
                for i,j in self.last_available_pos:
                    if not( i == x and j == y) :
                        self.getPiece(i,j).hide()
                for i,j in available_pos:
                    self.placePieceImage(i, j, self.READY)
                self.last_available_pos = available_pos
            else:
                for i,j in self.last_available_pos:
                    if not( i == x and j == y) :
                        self.getPiece(i,j).hide()
                win = "黑棋胜" if b_score > w_score else "白棋胜"
                if b_score == w_score:
                    win = "和局"
                game_over_info = "游戏结束\r\n" + win + "\r\n"
                QMessageBox.question(self,'警告',game_over_info,QMessageBox.Yes)
        else:
            #不能下子，弹出提醒
            QMessageBox.question(self,'警告','这个地方不能下子哟哟哟',QMessageBox.Yes)

    def placePieceImage(self, x, y, image):
        #下子，如果该标签存在，则替换图片，不存在，则新建
        label = self.getPiece(x, y)
        pixmap = QPixmap(image).scaled(BOARD_L,BOARD_L)
        if not label:
            label = QLabel(self)
            label.setGeometry( x*BOARD_L + BOARD_BORDER ,y*BOARD_L + BOARD_BORDER,BOARD_L,BOARD_L)
            label.setPixmap(pixmap)
            label.setObjectName('point_' + str(x) +'_' + str(y) )
            label.show()
        else:
            label.setPixmap(pixmap)
            label.show()
        return label

    def getPiece(self, x, y):
        #判断标签是否存在
        return self.findChild(QLabel , 'point_' + str(x) +'_' + str(y))


class Hall(QDialog):
    def __init__(self,parent = None):
        super(Hall,self).__init__(parent)
        self.ROW = 4
        self.COL = 3
        self.N = self.ROW * self.COL
        self.resize(UI_HEIGHT*0.8,UI_HEIGHT*0.6)
        self.setObjectName("hall")
        self.setWindowTitle("游戏大厅")
        self.tables = [0 for i in range(self.N)]
        layout = QGridLayout()
        self.setLayout(layout)
        for i in range(self.N):
            label = QLabel(self)
            label.setObjectName('table_' + str(i))
            layout.addWidget(label,i // self.COL,i % self.COL)

    def showHall(self,tables):
        cnt = len(tables)
        for i in range(cnt):
            label = self.findChild(QLabel,'table_'+str(i))
            print(tables[i])
            t_table = tables[i].split(' ')
            label.setText(  "<p style='text-align:center'>%s</p><p style='text-align:center;font-size:14px'>%s</p>" % \
                            (t_table[0],t_table[1]))
        self.show()


    def mousePressEvent(self, event):
        #点击哪一个棋局
        width = self.width()/self.COL
        height = self.height()/self.ROW
        _x = event.x()
        _y = event.y()
        x = round((_x - width/2)/width)
        y = round((_y - height/2)/height)
        no = y*self.COL + x
        if self.tables[no] <2:
            game.packAndSend({
                'to':'admin',
                'action':'join',
                'value':no
            })
        else:
            QMessageBox.information(self,'警告',"该桌已经满了")


class GetDataWorker(QThread):
    dataSignal = pyqtSignal(str)

    def __init__(self,client):
        super(GetDataWorker , self).__init__()
        self.client = client

    def run(self):
        while True:
            buf = self.client.recv(REC_BUFFER_SIZE)
            if len(buf):
                self.dataSignal.emit(buf.decode("utf8"))


class InputDialog(QDialog):
    def __init__(self,parent=None):
        super(InputDialog,self).__init__(parent)
        self.setWindowTitle("输入服务器地址和用户名")
        self.resize(300,150)
        self.setWindowIcon(QIcon('images/icon.jpg'))
        self.createGrid()

    def createGrid(self):
        names = ('呆尐兔兔','康师傅','哇哈哈','矿泉水','农夫山泉','蛤蛤','操作系统','计算机','网络','数据通信')
        nick_name = names[int(time.time() * 1000) % 10]
        layout = QGridLayout(self)
        self.setLayout(layout)
        #添加三个输入框
        self.ipEdit = QLineEdit('127.0.0.1')
        self.portEdit = QLineEdit('9999')
        self.nicknameEdit = QLineEdit(nick_name)
        layout.addWidget(QLabel("IP地址"),0,0,1,2)
        layout.addWidget(self.ipEdit,0,2,1,10)
        layout.addWidget(QLabel("端口号"),1,0,1,2)
        layout.addWidget(self.portEdit,1,2,1,10)
        layout.addWidget(QLabel("昵称"),2,0,1,2)
        layout.addWidget(self.nicknameEdit,2,2,1,10)
        #添加提交按钮
        submit_btn = QPushButton('确认',self)
        submit_btn.clicked.connect(self.submit)
        layout.addWidget(submit_btn,3,7,1,5)

    def submit(self):
        ip,port,nickname = self.ipEdit.text(),self.portEdit.text(),self.nicknameEdit.text()
        def is_valid_ip(ip_address):
            if ip_address == "localhost":
                return True
            if not ip:
                return False
            ip_address = str(ip_address).split('.')
            if len(ip_address) != 4:
                return False
            for each in ip_address :
                if not each.isdigit():
                    return False
                if int(each) > 255 or int(each) < 0:
                    return False
            return True

        def is_valid_port(port):
            return port and str(port).isdigit() and ( 0 < int(port) < 65536)

        def is_valid_nickname(nickname):
            return nickname and ( 0 < len(nickname) < 21)

        if not is_valid_ip(ip):
            QMessageBox.information(self,"警告","请输入正确的IP地址")
        elif not is_valid_port(port):
            QMessageBox.information(self,"警告","请输入正确的端口号")
        elif not is_valid_nickname(nickname):
            QMessageBox.information(self,"警告","请输入正确的昵称，1-20字符")
        else:
            self.hide()
            startGame(ip,port,nickname)


def startGame(ip,port,nickname):
    # 黑白棋GUI界面
    global game,game_othello,game_board
    game = Game(ip,port,nickname)
    game_othello = game.getOthello()
    game_board = game.getBoard()

    #黑白棋网络连接线程
    data_worker = GetDataWorker(game.client)
    data_worker.start()
    data_worker.dataSignal.connect(game.parseMsg)
    #游戏开始以及结束
    game.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config = InputDialog()
    config.show()
    sys.exit(app.exec_())
