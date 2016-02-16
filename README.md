# UdpSockets
## 开发环境
1. python版本 python 3.4
2. 图形 pyqt5
3. 打包 py2exe
4. 网络 socket
5. 多线程支持 threading

## GobangServer（服务方）程序
服务器除了支持这些命令，最好在用户游戏的过程中，要能判断何时游戏结束，胜负如何。
1.  /msg [playerid]
群发和向指定用户发送消息，用以某些提示。 

2.  /list 
列出所有玩家的列表及其参加棋局的情况。

3.  /kickout playerid 
将某玩家踢出游戏，以防止一些捣乱的玩家，如长时间不走棋。并且向参加该棋局中的对方玩家发送踢出的消息。

4.  /opengame  gameName
开通新的棋局 

5.  /games 
列出当前正在比赛的棋局。 

6.  /watch gameName
可以观看某一棋局的比赛情况，可以list，kickout playerid命令。直到使用leave命令离开该棋局。

7.  /closegame gameName
关闭某一棋局。

## GobangClient（客户方）程序
该黑白棋游戏客户方程序要求能够支持如下命令（所有命令以/开始）和服务方程序交互：
1.	/login playername
用playername登录服务器。服务方给该用户分配一个唯一标识

2.  /games
列出当前正在比赛的棋局。

3.  /list
列出服务器的当前所有玩家列表，及其参加棋局的情况。

4.  /join gameName
加入某一棋局（人为控制加入现没有人或只有一人的游戏）。该棋局的对方玩家收到其加入的消息。

5.  /move x y
通知服务器及对方玩家的走棋情况，（x,y）为棋盘上坐标。

6.  /restart
发出重新开始游戏，如对方玩家同意后，重新开始游戏。

7.	/leave
离开游戏。该棋局的对方玩家收到其离开的消息。