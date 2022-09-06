import binascii
import datetime
import os
import re
import string
import threading
import time
import tkinter as tk
import sys
from tkinter import *
from tkinter import (END, dialog, filedialog, messagebox, scrolledtext,
                     simpledialog, ttk)
import serial.tools.list_ports
import serial
from ctypes import *



class MainSerial:

    def __init__(self):
        # 定义串口变量
        self.port = None
        self.band = None
        self.myserial = None
        self.ser = None
        self.flag_ser = None
        self.port_list_name = ''
        class _PointAPI(Structure): # 用于getpos()中API函数的调用
            _fields_ = [("x", c_ulong), ("y", c_ulong)]

        def getpos():
            # 调用API函数获取当前鼠标位置。返回值以(x,y)形式表示。
            po = _PointAPI()
            windll.user32.GetCursorPos(byref(po))
            return int(po.x), int(po.y)
        def xpos():return getpos()[0]
        def ypos():return getpos()[1]

        # tkinter控件支持作为字典键。
        # bound的键是dragger, 值是包含1个或多个绑定事件的列表, 值用于存储控件绑定的数据
        # 列表的一项是对应tkwidget和其他信息的元组
        bound = {}
        def __add(wid,data):# 添加绑定数据
            bound[wid]=bound.get(wid,[])+[data]


        def move(widget,x=None,y=None,width=None,height=None):
            "移动控件或窗口widget, 参数皆可选。"
            x=x if x!=None else widget.winfo_x()
            y=y if y!=None else widget.winfo_y()
            width=width if width!=None else widget.winfo_width()
            height=height if height!=None else widget.winfo_height()
            if isinstance(widget,tk.Wm):
                widget.geometry("%dx%d+%d+%d"%(width,height,x,y))
            else:
                widget.place(x=x,y=y,width=width,height=height)
            return x,y,width,height

        def _mousedown(event):
            if event.widget not in bound:return
            lst=bound[event.widget]
            for data in lst: # 开始拖动时, 在每一个控件记录位置和控件尺寸
                widget=data[1]
                widget.mousex,widget.mousey = getpos()
                widget.startx,widget.starty = widget.winfo_x(),widget.winfo_y()
                widget.start_w=widget.winfo_width()
                widget.start_h=widget.winfo_height()
        def _drag(event):
            if event.widget not in bound:return
            lst=bound[event.widget]
            for data in lst: # 多个绑定
                if data[0]!='drag':return
                widget=data[1]
                dx = xpos()-widget.mousex # 计算鼠标当前位置和开始拖动时位置的差距
                # 注: 鼠标位置不能用event.x和event.y
                # event.x,event.y与控件的位置、大小有关，不能真实地反映鼠标移动的距离差值
                dy = ypos()-widget.mousey 
                move(widget,widget.startx + dx if data[2] else None,
                            widget.starty + dy if data[3] else None)

        def draggable(tkwidget,x=True,y=True):
            """调用draggable(tkwidget) 使tkwidget可拖动。
        tkwidget: 一个控件(Widget)或一个窗口(Wm)。
        x 和 y: 只允许改变x坐标或y坐标。"""
            bind_drag(tkwidget,tkwidget,x,y)

        def bind_drag(tkwidget,dragger,x=True,y=True):
            """绑定拖曳事件。
        tkwidget: 被拖动的控件或窗口,
        dragger: 接收鼠标事件的控件,
        调用bind_drag后,当鼠标拖动dragger时, tkwidget会被带着拖动, 但dragger
        作为接收鼠标事件的控件, 位置不会改变。
        x 和 y: 同draggable()函数。"""
            dragger.bind("<Button-1>",_mousedown,add='+')
            dragger.bind("<B1-Motion>",_drag,add='+')
            __add(dragger,('drag',tkwidget,x,y)) # 在bound字典中记录数据
        btns=[]
        def adjust_button(event=None):
        # 改变大小或拖动后,调整手柄位置
            for b in btns:
                x,y=b._func()
                b.place(x=x,y=y)
        # 初始化窗体
        self.mainwin = tk.Tk()
        self.mainwin.title("WCM CodeTest")
        screen_width = self.mainwin.winfo_screenwidth()
        screen_height = self.mainwin.winfo_screenheight()
        
        
        # calculate position x and y coordinates
        x = (screen_width / 2) - (700 / 2)
        y = (screen_height / 2) - (600 / 2)
        self.mainwin.geometry('%dx%d+%d+%d' % (700, 600, x, y))
        self.mainwin.config(bg='lightGray')
        tab_main = ttk.Notebook()
        tab_main.place(relx=0.01, rely=0.01, relwidth=1, relheight=1)
        tab1 = Frame(tab_main)
        tab1.config(bg='lightGray', highlightbackground="black")
        tab_main.add(tab1, text='主页')
        tab2 = Frame(tab_main)
        tab2.config(bg='lightGray', highlightbackground="black")
        tab_main.add(tab2, text='设置项')
        #画布1
        self.canvas = Canvas(tab1,
                             height=320,
                             width=180,
                             highlightthickness=0.5,
                             bg='lightGray',
                             highlightbackground="black")
        self.canvas.place(x=15, y=15)
        Label(tab1, text='端口设置:', font=("宋体", 10), height=1,
              bg='lightGray').place(
                  x=18,
                  y=20,
              )
        # 串口号
        self.label1 =Label(tab1,
                                    text="串口号:",
                                    font=("宋体", 10),
                                    height=2,
                                    bg='lightGray')
        self.label1.place(x=25, y=45)
        self.com1value = tk.StringVar()  # 窗体中自带的文本，创建一个值
        self.combobox_port = ttk.Combobox(
            tab1,
            textvariable=self.com1value,
            width=10,
            font=("宋体", 10),
        )
        self.combobox_port["value"] = self.port_get()
        self.combobox_port.place(x=80, y=45)  # 显示
        #波特率
        self.label2 = Label(tab1,
                                    text="波特率:",
                                    font=("宋体", 10),
                                    bg='lightGray')
        self.label2.place(x=25, y=80)
        self.bandvalue = tk.StringVar()  # 窗体中自带的文本，创建一个值
        self.combobox_band = ttk.Combobox(tab1,
                                          textvariable=self.bandvalue,
                                          height=12,
                                          width=10,
                                          font=("宋体", 10))
        self.combobox_band["value"] = [
            '1200', '2400', "4800", "9600", "14400", "19200", "38400", "57600",
            "115200"
        ]  # 常规用波特率
        self.combobox_band.current(3)  # 默认选中9600
        self.combobox_band.place(x=80, y=80)  # 显示
        self.openport = tk.Button(tab1,
                                       text="打开串口",
                                       command=self.open_port,
                                       font=("宋体", 10),
                                       bg='lightGray',
                                       width=8,
                                       height=1)
        self.openport.place(x=25, y=120)
        self.button_find = tk.Button(
            tab1,
            text="扫描串口",  
            command=self.port_get,
            font=("宋体", 10),
            bg='lightGray',
            width=8,
            height=1)
        self.button_find.place(x=105, y=120)
        self.button_232 = tk.Button(
            tab1,
            text="TTL-232串口",  
            font=("宋体", 9),
            bg='lightGray',
            width=10,command=lambda:self.com('00'),
            height=1)
        self.button_232.place(x=105, y=160)
        self.button_HID = tk.Button(
            tab1,
            text="USB-HID",  
            font=("宋体", 9),
            bg='lightGray',command=lambda:self.com('01'),
            width=10,
            height=1)
        self.button_HID.place(x=25, y=160)
        self.button_VCP = tk.Button(
            tab1,
            text="虚拟串口",  
            font=("宋体", 9),
            bg='lightGray',command=lambda:self.com('11'),
            width=10,
            height=1)
        self.button_VCP.place(x=105, y=200)
        self.button_HIDTTL = tk.Button(
            tab1,
            text="HID/TTL同时",  
            font=("宋体", 9),
            bg='lightGray',command=lambda:self.com('10'),
            width=10,
            height=1)
        self.button_HIDTTL.place(x=25, y=200)
        self.button_star = tk.Button(tab1,text='触发识读命令',  
            font=("宋体", 9),bg='lightGray',command=lambda:self.send_txt('7E 00 08 01 00 02 01 AB CD'),width=10)
        self.button_star.place(x=25, y=240)
        self.data_txt = scrolledtext.ScrolledText(self.mainwin,
                                                  width=65,
                                                  height=24,
                                                  bg='lightGray',
                                                  font=("宋体", 10))
        self.data_txt.place(x=210, y=50)
        self.formatvalue = tk.StringVar()
        self.combobox_format = ttk.Combobox(self.mainwin,
                                            textvariable=self.formatvalue,
                                            height=4,
                                            width=6,
                                            font=("宋体", 10))
        self.combobox_format["value"] = ['GBK', "UTF8"]  # 常规编码方式
        self.combobox_format.current(0)  # 默认选中GBK
        self.combobox_format.place(x=280, y=30)  # 显示
        self.recv_hex = IntVar()
        self.check_hex = Checkbutton(self.mainwin,
                                     text='HEX接收',
                                     font=("宋体", 9),
                                     onvalue=1,
                                     offvalue=0,
                                     variable=self.recv_hex,
                                     bg='lightGray')
        
        self.check_hex.place(x=350, y=30)
        Label(self.mainwin,
              text='超时时间       ms',
              font=("宋体", 10),
              bg='lightGray').place(x=430, y=30)
        self.ent_timeout = Entry(
            self.mainwin,
            width=5,
        )
        self.ent_timeout.place(x=490, y=27)
        self.ent_timeout.insert(0, 20)
        self.btn_qingchu = Button(self.mainwin,
                                  text='清除接收',
                                  width=10,
                                  font=("宋体", 10),
                                  command=self.txt_del)
        self.btn_qingchu.place(x=570, y=30)

        

        #画布2
        self.canvas1 = Canvas(tab1,
                              height=90,
                              width=260,
                              highlightthickness=0.5,
                              bg='lightGray',
                              highlightbackground="black")
        self.canvas1.place(x=15, y=355)
        Label(tab1, text='识读模式:', font=("宋体", 10), height=1,
              bg='lightGray').place(
                  x=120,
                  y=345,
              )
        self.btn_shoudong = Button(tab1,
                                   text='手动模式',
                                   width=12,
                                   bg='lightGray',
                                   command=lambda: self.mode(bit='00'))
        draggable(self.btn_shoudong)
        self.btn_shoudong.bind('<B1-Motion>',adjust_button,add='+')
        self.btn_shoudong.place(x=25, y=365)
        self.btn_lianxu = Button(tab1,
                                 text='连续模式',
                                 width=12,
                                 bg='lightGray',
                                 command=lambda: self.mode(bit='10'))
        self.btn_lianxu.place(x=25, y=400)
        self.btn_mingling = Button(tab1,
                                   text='命令触发模式',
                                   width=12,
                                   bg='lightGray',
                                   command=lambda: self.mode(bit='01'))
        self.btn_mingling.place(x=165, y=365)
        self.btn_ganying = Button(tab1,
                                  text='感应模式',
                                  width=12,
                                  bg='lightGray',
                                  command=lambda: self.mode(bit='11'))
        self.btn_ganying.place(x=165, y=400)
        #画布3
        self.canvas2 = Canvas(tab1,
                              height=90,
                              width=170,
                              highlightthickness=0.5,
                              bg='lightGray',
                              highlightbackground="black")
        self.canvas2.place(x=280, y=355)
        Label(tab1, text='识读间隔：', font=("宋体", 10), height=1,
              bg='lightGray').place(
                  x=320,
                  y=345,
              )
        self.btn_0 = Button(tab1,
                            font=("宋体", 9),
                            text='无间隔',
                            width=10,
                            bg='lightGray',
                            command=lambda: self.time_interval(0))
        self.btn_0.place(x=290, y=365)
        self.btn_100 = Button(tab1,
                              font=("宋体", 9),
                              text='间隔100ms',
                              width=10,
                              bg='lightGray',
                              command=lambda: self.time_interval(100))
        self.btn_100.place(x=290, y=400)
        self.btn_500 = Button(tab1,
                              font=("宋体", 9),
                              text='间隔500ms',
                              width=10,
                              bg='lightGray',
                              command=lambda: self.time_interval(500))
        self.btn_500.place(x=370, y=365)
        self.btn_self = Button(tab1,
                               font=("宋体", 9),
                               text='自定义',
                               width=10,
                               bg='lightGray',
                               command=self.time_self)
        self.btn_self.place(x=370, y=400)
       
        #画布4
        self.canvas3 = Canvas(tab1,
                              height=50,
                              width=220,
                              highlightthickness=0.5,
                              bg='lightGray',
                              highlightbackground="black")
        self.canvas3.place(x=455, y=395)
        Label(tab1, text='结束符', bg='lightGray', font=("宋体", 9)).place(x=465,
                                                                      y=385)
        self.btn_reset = Button(
            tab1,
            font=("宋体", 9),
            text='恢复出厂设置',
            width=11,
            bg='lightGray',
            command=lambda: self.reset(data='7E 00 08 01 00 D9 50 AB CD'))
        self.btn_reset.place(x=460, y=345)
        self.btn_save = Button(
            tab1,
            text='保存为自定义出厂设置',
            font=("宋体", 9),
            bg='lightGray',
            command=lambda: self.reset(data='7E 00 08 01 00 D9 56 AB CD'))
        self.btn_save.place(x=550, y=345)
        self.btn_recovery = Button(
            tab1,
            text='恢复为自定义出厂设置',
            font=("宋体", 9),
            bg='lightGray',
            command=lambda: self.reset(data='7E 00 08 01 00 D9 55 AB CD'))
        self.btn_recovery.place(x=550, y=372)
        self.btn_CR=Button(tab1,text='CR', height=1,bg='lightGray',command=lambda:self.end_data('00'))
        self.btn_CR.place(x=460,y=412)
        self.btn_TAB=Button(tab1,text='TAB', height=1,bg='lightGray',command=lambda:self.end_data('10'))
        self.btn_TAB.place(x=500,y=412)
        self.btn_CRLF=Button(tab1,text='CRLF', height=1,bg='lightGray',command=lambda:self.end_data('01'))
        self.btn_CRLF.place(x=540,y=412)
        self.btn_None=Button(tab1,text='无', height=1,bg='lightGray',command=lambda:self.end_data('11'))
        self.btn_None.place(x=590,y=412)
        Label(self.mainwin, text='-' * 130, bg='lightGray').place(x=15, y=550)
        self.send_tx = Text(tab1, width=80, height=5)
        self.send_tx.place(x=15, y=452)
        self.send_hex = IntVar()

        self.check_hex = Checkbutton(tab1,
                                     text='HEX发送',
                                     font=("宋体", 9),
                                     onvalue=1,
                                     offvalue=0,
                                     variable=self.send_hex,
                                     bg='lightGray')
        self.check_hex.place(x=580, y=462)

        self.btn_send = Button(tab1, text='发送', command=self.send_data)
        self.btn_send.place(x=580, y=492)
    def end_data(self,bit):
        dict1 = {'00': 'CR', '01': 'CRLF', '10': 'TAB', '11': 'USB 无'}
        self.end_dat=dict1[bit]
        self.flag_ser = False
        self.ser.flushInput()
        self.ser.write(bytes.fromhex('7E 00 07 01 00 60 01 AB CD'))  #查询

        self.mainwin.after(40)
        if self.ser.in_waiting:
            a = str(binascii.b2a_hex(self.ser.read(
                self.ser.in_waiting)))[2:-1].upper()
            s = a.find('02000001')
            b = a[s + 8:s + 10]
            b = bin(int(b, 16)).replace('0b', '').zfill(8)
            c = b[0] + str(bit)+b[3::]
            c = hex(int(c, 2)).replace('0x', '').zfill(2).upper()

            self.ser.write(
                bytes.fromhex('7E 00 08 01 00 60 ' + c.replace('0x', '') +
                              ' AB CD'))  #写入
            self.ser.write(bytes.fromhex('7E 00 07 01 00 60 01 AB CD'))  #查询
            self.mainwin.after(60)
            if self.ser.in_waiting:
                re = str(binascii.b2a_hex(self.ser.read(
                    self.ser.in_waiting)))[2:-1].upper()
        if '02000001003331' in re:
            self.data_txt.insert(
                END,'\n'+
                str(datetime.datetime.now())[11:-3] + dict1[bit] + '写入成功')
            self.data_txt.update()
            self.data_txt.see(END)
        self.ser.write(bytes.fromhex('7E 00 09 01 00 00 00 DE C8'))  #保存
        self.ser.flushInput()
        self.mainwin.after(80)
        self.flag_ser = True
        self.recv = threading.Thread(target=self.recv_data)
        self.recv.start()
    def send_data(self, time=None):
        data = self.send_tx.get('0.0', 'end').strip()

        print(str(datetime.datetime.now())[11:-3],len(data))
        
        if len(data) > 0:
            if self.ser.isOpen():
                try:
                    if self.send_hex.get() == 1:
                        self.ser.write(bytes.fromhex(data))
                    else:
                        self.ser.write(data.encode('ansi'))
                except:
                    messagebox.showinfo('错误', '数据错误')
            else:
                messagebox.showinfo('错误', '请检查串口连接！')
            self.data_txt.insert(END,str(datetime.datetime.now())[11:-3] +'[发]→'+ data+'\n')
            self.data_txt.update()
            self.data_txt.see(END)
    def reset(self, data):
        self.flag_ser = False
        try:
            self.ser.write(bytes.fromhex(data))
            
            self.data_txt.insert(END,
                            str(datetime.datetime.now())[11:-3] + data+'\n')
            self.data_txt.update()
            self.data_txt.see(END)
        except:
            messagebox.showinfo('写入错误', '请检查串口连接')
        self.mainwin.after(40)
        self.ser.write(bytes.fromhex('7E 00 09 01 00 00 00 DE C8'))  #保存
        self.ser.flushInput()
        self.flag_ser = False

    def recv_data(self):
        self.mainwin.after(100)
        self.ser.flushInput()
        if self.flag_ser == True:
            while 1:
                if self.ser == None or self.flag_ser == False:
                    break
                try:
                  if self.ser.in_waiting:
                    if self.recv_hex.get() == 0:
                        
                        recv = (self.ser.read(self.ser.in_waiting))
                        recv = recv.decode(self.combobox_format.get(),
                                           'replace')
                        self.data_txt.insert(
                            END,
                            '\n'+str(datetime.datetime.now())[11:-3] + '[收]←' +
                            recv )

                    else:
                        rec = str(
                            binascii.b2a_hex(self.ser.read(
                                self.ser.in_waiting)))[2:-1].upper()
                        rec = re.findall('.{2}', rec)
                        recv = ' '.join(rec)
                        self.data_txt.insert(
                            END,
                            str(datetime.datetime.now())[11:-3] + '[收]←' +
                            recv )
                except:
                    self.open_port()
                self.data_txt.see(END)
                self.data_txt.update()
                #self.data_txt.mark_set('insert',END)
                self.data_txt.mark_set('insert',END)
                endline, endcolumn = self.data_txt.index('end').split('.')
                
                try:
                    time.sleep(int(self.ent_timeout.get()) / 1000)
                except:
                    time.sleep(0.02)
    def com(self, bit):
        dict1 = {'00': '串口输出', '01': 'USB -HID', '10': '串口&HID同时输出', '11': 'USB 虚拟串口'}
        self.flag_ser = False
        self.ser.flushInput()
        self.ser.write(bytes.fromhex('7E 00 07 01 00 0D 01 AB CD'))  #查询

        self.mainwin.after(40)
        if self.ser.in_waiting:
            a = str(binascii.b2a_hex(self.ser.read(
                self.ser.in_waiting)))[2:-1].upper()
            s = a.find('02000001')
            b = a[s + 8:s + 10]
            b = bin(int(b, 16)).replace('0b', '').zfill(8)
            c = b[0:6] + str(bit)
            c = hex(int(c, 2)).replace('0x', '').zfill(2).upper()

            self.ser.write(
                bytes.fromhex('7E 00 08 01 00 0D ' + c.replace('0x', '') +
                              ' AB CD'))  #写入
            self.ser.write(bytes.fromhex('7E 00 07 01 00 0D 01 AB CD'))  #查询
            self.mainwin.after(60)
            if self.ser.in_waiting:
                re = str(binascii.b2a_hex(self.ser.read(
                    self.ser.in_waiting)))[2:-1].upper()
        if '02000001003331' in re:
            self.data_txt.insert(
                END,'\n'+
                str(datetime.datetime.now())[11:-3] + dict1[bit] + '写入成功')
            self.data_txt.update()
            self.data_txt.see(END)
        self.ser.write(bytes.fromhex('7E 00 09 01 00 00 00 DE C8'))  #保存
        self.ser.flushInput()
        self.mainwin.after(80)
        self.flag_ser = True
        self.recv = threading.Thread(target=self.recv_data)
        self.recv.start()
    def mode(self, bit):
        dict1 = {'00': '手动模式', '01': '命令触发', '10': '连续模式', '11': '感应模式'}
        self.flag_ser = False
        self.ser.flushInput()
        self.ser.write(bytes.fromhex('7E 00 07 01 00 00 01 AB CD'))  #查询

        self.mainwin.after(40)
        if self.ser.in_waiting:
            a = str(binascii.b2a_hex(self.ser.read(
                self.ser.in_waiting)))[2:-1].upper()
            s = a.find('02000001')
            b = a[s + 8:s + 10]
            b = bin(int(b, 16)).replace('0b', '').zfill(8)
            c = b[0:6] + str(bit)
            c = hex(int(c, 2)).replace('0x', '').zfill(2).upper()

            self.ser.write(
                bytes.fromhex('7E 00 08 01 00 00 ' + c.replace('0x', '') +
                              ' AB CD'))  #写入
            self.ser.write(bytes.fromhex('7E 00 07 01 00 00 01 AB CD'))  #查询
            self.mainwin.after(60)
            if self.ser.in_waiting:
                re = str(binascii.b2a_hex(self.ser.read(
                    self.ser.in_waiting)))[2:-1].upper()
        if '02000001003331' in re:
            self.data_txt.insert(
                END,'\n'+
                str(datetime.datetime.now())[11:-3] + dict1[bit] + '写入成功')
            self.data_txt.update()
            self.data_txt.see(END)
        self.ser.write(bytes.fromhex('7E 00 09 01 00 00 00 DE C8'))  #保存
        self.mainwin.after(100,self.ser.flushInput())
        self.flag_ser = True
        self.recv = threading.Thread(target=self.recv_data)
        self.recv.start()

    def time_self(self):
        entry = None
        try:
            entry = int(
                simpledialog.askinteger(title='自定义间隔时间',
                                        prompt='请输入自定义数字单位ms：'))
            if entry % 100 == 0:
                self.time_interval(entry)
            else:
                messagebox.showinfo('错误', '请输入100的整数倍')
        except:
            pass

    def time_interval(self, time):
        a = time
        time = hex(int(time / 100)).replace('0x', '')
        time = time.zfill(2).upper()
        self.flag_ser = False
        self.ser.flushInput()
        str1 = '7E 00 08 01 00 05 ' + time + ' AB CD'
        try:
            self.ser.write(bytes.fromhex(str1))
            self.mainwin.after(60)
            if self.ser.in_waiting:
                recv = str(binascii.b2a_hex(self.ser.read(
                    self.ser.in_waiting)))[2:-1].upper()

                if '02000001003331' in recv:
                    if a == 0:
                        a = '无间隔'
                    else:
                        a = str(a) + 'ms'
                    self.data_txt.insert(
                        END,'\n'+
                        str(datetime.datetime.now())[11:-3] +
                        '识读间隔【%s】写入成功' % a)
                    self.ser.write(bytes.fromhex('7E 00 09 01 00 00 00 DE C8'))
                    self.data_txt.update()
                    self.data_txt.see(END)
        except:
            messagebox.showinfo('错误', '请检查串口连接')  
        self.mainwin.after(100)
        self.flag_ser = True
        self.recv = threading.Thread(target=self.recv_data)
        self.recv.start()

    def show(self):
        self.mainwin.mainloop()

    def port_get(self):
        
        port_list = serial.tools.list_ports.comports()
        port_list_name = []
        # get all com
        
        if len(port_list) == '':
            self.port_list_name=''
            print(port_list)
            self.combobox_port.delete()
            self.combobox_port.update()


        else:
            for itms in port_list:
                port_list_name.append(itms.device)
        self.port_list_name = port_list_name
        self.combobox_port["value"] = self.port_list_name
        if self.port_list_name:
            self.combobox_port.current(0) 
        self.combobox_port.update()

    def open_port(self):
        self.com_choose = self.combobox_port.get()
        self.openport.config(state=NORMAL)
        self.openport.config(state=NORMAL)
        if self.openport['bg'] == 'lightGray':
            self.flag_ser = True
            try:
                self.ser = serial.Serial(self.combobox_port.get(),
                                         self.combobox_band.get(),
                                         timeout=30,
                                         parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
                self.openport.config(text='已连接', bg='lightgreen')
                self.combobox_port.config(state=DISABLED)
                #self.combobox_band.config(state=DISABLED)
                self.recv = threading.Thread(target=self.recv_data)
                self.recv.start()
                
            except:
                if self.com_choose == '':
                    messagebox.showinfo('错误', '没有找到端口')
                else:
                    messagebox.showinfo('错误', '串口已打开')
        else:
            if self.ser.isOpen():
                self.flag_ser = False
                self.ser.close()
                self.openport.config(text='打开串口', bg='lightGray')
                self.combobox_port.config(state=NORMAL)
                #self.combobox_band.config(state=NORMAL)
                self.data_txt.insert(END, (str(datetime.datetime.now())[11:-3]) +
                                '串口已关闭\n')
                self.data_txt.see(END)

    def txt_del(self):
        #self.txt.delete(0.0, END)
        self.data_txt.delete(0.0, END)

    def send_txt(self,data):
            self.ser.write(bytes.fromhex(data))
            

if __name__ == '__main__':
    my_ser1 = MainSerial()
    my_ser1.show()
