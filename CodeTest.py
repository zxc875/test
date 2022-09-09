import binascii
import datetime
from distutils.command.config import config
import os
import configparser
import re
import string
import threading
import time
import tkinter as tk
import sys
from tkinter import *
from tkinter import (END, dialog, filedialog, messagebox, scrolledtext,
                     simpledialog, ttk)
import serial
import serial.tools.list_ports

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
        self.data={}
        self.button=[]
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
        tab_main.add(tab2, text='DIY')
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
            width=10,command=lambda:self.send_txt(Flag_Num='0D',Flag_bit='Bit1-0',byte='00'),
            height=1)
        self.button_232.place(x=105, y=160)
        self.button_HID = tk.Button(
            tab1,
            text="USB-HID",  
            font=("宋体", 9),
            bg='lightGray',command=lambda:self.send_txt(Flag_Num='0D',Flag_bit='Bit1-0',byte='01'),
            width=10,
            height=1)
        self.button_HID.place(x=25, y=160)
        self.button_VCP = tk.Button(
            tab1,
            text="虚拟串口",  
            font=("宋体", 9),
            bg='lightGray',command=lambda:self.send_txt(Flag_Num='0D',Flag_bit='Bit1-0',byte='11'),
            width=10,
            height=1)
        
        self.button_VCP.place(x=105, y=200)
        self.button_HIDTTL = tk.Button(
            tab1,
            text="HID/TTL同时",  
            font=("宋体", 9),
            bg='lightGray',command=lambda:self.send_txt(Flag_Num='0D',Flag_bit='Bit1-0',byte='10'),
            width=10,
            height=1)
        self.button_HIDTTL.place(x=25, y=200)
        
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
        self.combobox_format["value"] = ['GBK', "UTF8",'ASCII']  # 常规编码方式
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
                                   width=10,
                                   bg='lightGray',
                                   font=("宋体", 9),
                                   command=lambda: self.send_txt(Flag_Num='00',Flag_bit='Bit1-0',byte='00'))
       
        
        self.btn_shoudong.place(x=25, y=365)
        self.btn_lianxu = Button(tab1,
                                 text='连续模式',
                                 width=10,
                                 bg='lightGray',
                                 font=("宋体", 9),
                                 command=lambda: self.send_txt(Flag_Num='00',Flag_bit='Bit1-0',byte='10'))
        self.btn_lianxu.place(x=25, y=393)
        self.btn_mingling = Button(tab1,
                                   text='命令触发模式',
                                   width=12,
                                   bg='lightGray',
                                   font=("宋体", 9),
                                   command=lambda: self.send_txt(Flag_Num='00',Flag_bit='Bit1-0',byte='01'))
        self.btn_mingling.place(x=105, y=365)
        self.button_star = Button(tab1,text='触发命令',  
            font=("宋体", 9),bg='lightGray',command=lambda:self.send_txt(Flag_Num='02',Flag_bit='Bit0',byte='1'),width=11)
        self.button_star.place(x=195, y=365)
        self.btn_ganying = Button(tab1,
                                  text='感应模式',
                                  width=10,
                                  bg='lightGray',
                                  font=("宋体", 9),
                                  command=lambda: self.send_txt(Flag_Num='00',Flag_bit='Bit1-0',byte='11'))
        self.btn_ganying.place(x=105, y=393)
        self.btn_kuaisu= Button(tab1,
                                  text='快速感应模式',
                                  width=11,
                                  bg='lightGray',
                                  font=("宋体", 9),
                                  command=lambda: self.send_txt(Flag_Num='CF',Flag_bit='Bit0',byte='0'))
        self.btn_kuaisu.place(x=105, y=420)
        self.btn_changgui= Button(tab1,
                                  text='常规感应模式',
                                  width=11,
                                  bg='lightGray',
                                  font=("宋体", 9),
                                  command=lambda: self.send_txt(Flag_Num='CF',Flag_bit='Bit0',byte='1'))
        self.btn_changgui.place(x=25, y=420)
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
                                                                      y=392)
        self.btn_edition = Button(
            tab1,
            font=("宋体", 9),
            text='版本信息',
            width=10,
            bg='lightGray',
            command=lambda: self.reset(data='7E 00 07 01 00 E1 07 AB CD'))
        self.btn_edition .place(x=460, y=345)
        self.btn_reset = Button(
            tab1,
            font=("宋体", 9),
            text='恢复出厂设置',
            width=11,
            bg='lightGray',
            command=lambda: self.reset(data='7E 00 08 01 00 D9 50 AB CD'))
        self.btn_reset.place(x=460, y=370)
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
        self.btn_CR=Button(tab1,text='CR', height=1,bg='lightGray',command=lambda:self.send_txt(Flag_Num='60',byte='00',Flag_bit='Bit6-5'))
        self.btn_CR.place(x=460,y=412)
        self.btn_TAB=Button(tab1,text='TAB', height=1,bg='lightGray',command=lambda:self.send_txt(Flag_Num='60',byte='10',Flag_bit='Bit6-5'))
        self.btn_TAB.place(x=492,y=412)
        self.btn_CRLF=Button(tab1,text='CRLF', height=1,bg='lightGray',command=lambda:self.send_txt(Flag_Num='60',byte='01',Flag_bit='Bit6-5'))
        self.btn_CRLF.place(x=530,y=412)
        self.btn_None=Button(tab1,text='无', height=1,bg='lightGray',command=lambda:self.send_txt(Flag_Num='60',byte='11',Flag_bit='Bit6-5'))
        self.btn_None.place(x=572,y=412)
        Label(self.mainwin, text='-' * 130, bg='lightGray').place(x=15, y=550)
        self.send_tx = Text(tab1, width=80, height=5)
        self.send_tx.place(x=15, y=452)
        self.send_hex = IntVar()
        menu = Menu(self.mainwin,
            tearoff=False,
            #bg="black",
            )
        menu.add_command(label="添加按钮", command=lambda: self.add_btn(tab2))
        menu.add_command(label="添加边框", command=self.del_btn)  
        def popup(event):
            menu.post(event.x_root, event.y_root)   # post在指定的位置显示弹出菜单
        tab2.bind("<Button-3>", popup)  
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
        self.btn_save=Button(tab1,text='保存配置',command=lambda: self.save_ini(tab1))
        self.btn_save.place(x=25,y=300)
        try:
            self.load_ini(tab2)
        except:
            pass
    def bianji(self):
        pass
    def del_btn(self):
       self.del1.destroy()
        
    def add_btn(self,tab):
        pass
    def load_ini(self,tab2):
        conf = configparser.ConfigParser()
        path='save_info.ini'
        conf.read(path)
        section=conf.sections()
        name=[]
        names=locals()
        i=0 
        def popup(event):
                menu.post(event.x_root, event.y_root) 
                self.del1=event.widget
        menu=Menu(tab2,tearoff=False)
        menu.add_command(label="删除", command=self.del_btn)
        for item in section:
            x=conf.get(item,'x')
            y=conf.get(item,'y')
            text=conf.get(item,'text')
            bg=conf.get(item,'bg')
            font=conf.get(item,'font')
            #print(item,x,y)
            s=Button(tab2,text=text,bg=bg,font=font,command= self.open_xls) #创建Button
            s.place(x=x,y=y)
            self.draggable(s) #绑定移动
            name.append(s)
            
        
            s.bind("<Button-3>", popup)
            i=i+1 
           
    def save_ini(self,tab1):
        conf = configparser.ConfigParser() # 类的实例化
        for child in tab1.winfo_children():
            print(child.widgetName)
            if child.widgetName=='button' or child.widgetName=='label':
                print(child.cget('text'),child.place_info()['x'],child.place_info()['y'])
                path = ('save_info.ini')
                conf.add_section(child.winfo_name()) # 添加一个新的section
                conf.set(child.winfo_name(),'text',child.cget('text'))
                conf.set(child.winfo_name(),'bg',child.cget('bg'))
                conf.set(child.winfo_name(),'font',child.cget('font'))
                #conf.set(child.winfo_name(),'width',child.cget('width'))
                conf.set(child.winfo_name(),'x',child.place_info()['x'])
                conf.set(child.winfo_name(),'y',child.place_info()['y'])   # 往配置文件写入数据
                conf.write(open(path,'w'))  # 保存数据

    def send_data(self, time=None): #发送按键
        data = self.send_tx.get('0.0', 'end').strip()
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
    def reset(self, data):#恢复出厂
        self.flag_ser = False
        try:
            self.ser.write(bytes.fromhex(data))
            self.data_txt.insert(END,
                            str(datetime.datetime.now())[11:-3] + '[发]→'+data+'\n')
            self.data_txt.update()
            self.data_txt.see(END)
        except:
            messagebox.showinfo('写入错误', '请检查串口连接')
        self.mainwin.after(100)
        print(data.replace(' ','')[10:12])
        if data=='7E 00 07 01 00 E1 07 AB CD':
            rec=str( binascii.b2a_hex(self.ser.read(
                                self.ser.in_waiting)))[2:-1].upper()
            rec = (re.findall('.{2}', rec))
            print(rec[4:-2])
            s=[]
            for i in rec[4:-2]:
                a=int(i,16)
                print(a)
                s.append[a]
            s=''.join(s)
            print(s)            

        self.ser.write(bytes.fromhex('7E 00 09 01 00 00 00 DE C8'))  #保存
        self.ser.flushInput()
        self.mainwin.after(100)
        self.flag_ser = True
        self.recv = threading.Thread(target=self.recv_data)
        self.recv.start()

    def recv_data(self):  #接收 待优化
        self.mainwin.after(100)
        self.ser.flushInput()
        endline1=2
        if self.flag_ser == True:
            while 1:
                if self.ser == None or self.flag_ser == False:
                    break
                try:
                  if self.ser.in_waiting:
                    if self.recv_hex.get() == 0:
                        
                        recv = self.ser.read_until()
                        recv = recv.decode(self.combobox_format.get(),
                                           'replace')
                        self.data_txt.insert(
                            END,str(datetime.datetime.now())[11:-3] + '[收]←'+recv+'\n' )
                        self.data_txt.see(END)
                        self.data_txt.update()
                        self.data_txt.mark_set('insert',END)
                    else:
                        rec = str(
                            binascii.b2a_hex(self.ser.read(
                                self.ser.in_waiting)))[2:-1].upper()
                        rec = re.findall('.{2}', rec)
                        recv = ' '.join(rec)
                        self.data_txt.insert(
                            END,
                            str(datetime.datetime.now())[11:-3] + '[收]←' +'\n'+
                            recv )
                        self.data_txt.see(END)
                        self.data_txt.update()
                        self.data_txt.mark_set('insert',END)
                except:
                    self.open_port()
                
                #self.data_txt.mark_set('insert',END)
                
                
                
                try:
                    time.sleep(int(self.ent_timeout.get()) / 1000)
                except:
                    time.sleep(0.02)
  

    def time_self(self):  #时间自定义
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

    def time_interval(self, time):  #时间间隔方面写入
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

    def port_get(self):  #扫描串口
        
        port_list = serial.tools.list_ports.comports()
        port_list_name = []
        # get all com
        if len(port_list) == '':
            self.port_list_name=''
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

    def open_port(self):   #打开串口
        self.com_choose = self.combobox_port.get()
        self.openport.config(state=NORMAL)
        self.openport.config(state=NORMAL)
        if self.openport['bg'] == 'lightGray':
            self.flag_ser = True
            try:
                self.ser = serial.Serial(self.combobox_port.get(),
                                         self.combobox_band.get(),
                                         timeout=0.5,
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

    def txt_del(self):
        #self.txt.delete(0.0, END)
        self.data_txt.delete(0.0, END)
    def query_bit(self,Flag_Num):  ###查询
        self.flag_ser = False
        self.ser.flushInput()
        a='7E 00 07 01 00'+Flag_Num+'01 AB CD'
        self.ser.write(bytes.fromhex(a))  #查询
        self.mainwin.after(40)
        if self.ser.in_waiting:
            a = str(binascii.b2a_hex(self.ser.read(
                self.ser.in_waiting)))[2:-1].upper()
            s = a.find('02000001')
            b = a[s + 8:s + 10]
            b = bin(int(b, 16)).replace('0b', '').zfill(8)
        return b
    def replace_bit(self,Flag_bit,write_byte,query):  ###替换对应位置
        a=query
        b=str(write_byte)
        c=Flag_bit.replace('Bit','').strip()
        if '-'in c: 
            c=(c.split('-')) 
            if len(b)==len(a[len(a)-int(c[0])-1:len(a)-int(c[1])]):
                d=a[len(a)-int(c[0])-1:len(a)-int(c[1])].replace(a[len(a)-int(c[0])-1:len(a)-int(c[1])],b)
                a=a[:len(a)-int(c[0])-1]+d+a[len(a)-int(c[1])::]
        else:
            d=a[int(c)].replace(a[int(c)],b)
            a=a[:len(a)-int(c)-1]+str(d)+a[len(a)-int(c)::]
        return a
    def send_txt(self,Flag_Num,Flag_bit,byte,):###写入对应位置，并保存
        try:
            query=self.query_bit(Flag_Num)
            c=self.replace_bit(write_byte=byte,Flag_bit=Flag_bit,query=query)
            c = hex(int(c, 2)).replace('0x', '').zfill(2).upper()
            self.ser.write(
                    bytes.fromhex('7E 00 08 01 00 '+Flag_Num+ ' '+ c.replace('0x', '') +
                                ' AB CD'))  #写入
            self.ser.write(bytes.fromhex('7E 00 07 01 00 '+Flag_Num+' 01 AB CD'))  #查询
            self.mainwin.after(60)
            if self.ser.in_waiting:
                    re = str(binascii.b2a_hex(self.ser.read(
                        self.ser.in_waiting)))[2:-1].upper()
            if '02000001003331' in re:
                self.data_txt.insert(
                    END,'\n'+
                    str(datetime.datetime.now())[11:-3]  + '写入成功\n')
                self.data_txt.update()
                self.data_txt.see(END)
            self.ser.write(bytes.fromhex('7E 00 09 01 00 00 00 DE C8'))  #保存
            self.mainwin.after(100,self.ser.flushInput())
            self.flag_ser = True
            self.recv = threading.Thread(target=self.recv_data)
            self.recv.start()
        except:
            print('串口没打开')
    def open_xls(self):            
        
                drec = dict()
                ncols =4
                for line in df:
                    d = drec
                    for j, col in enumerate(line[:-1]):
                        if not col in d.keys():
                            if j != ncols-2:
                                d[col] = {}
                                d = d[col]
                            else:
                                d[col] = line[-1]
                        else:
                            if j!= ncols-2:
                                d = d[col]
                return drec
                df = xlrd2.open_workbook('test_case.xlsx')
                table = df.sheets()[0]
                row = table.nrows
                data=[]
                for i in range(1, row):
                    a = table.row_values(i)
                    data.append(a)
                self.data=fdrec(data)
    def dict_num():
        s={}
        dict1=open_xls()
        for j in dict1.keys():
            for k in dict1[j].keys():
            #print(dict1[j][k])
                a=dict1[j][k]  
    def mousedown(self,event):
            widget=event.widget
            print(widget)
            widget.startx=event.x # 开始拖动时, 记录控件位置
            widget.starty=event.y
    def drag(self,event):
            widget=event.widget
            dx=event.x-widget.startx
            dy=event.y-widget.starty
            # winfo_x(),winfo_y() 方法获取控件的坐标
            if isinstance(widget,Wm):
                widget.geometry("+%d+%d"%(widget.winfo_x()+dx,
                                        widget.winfo_y()+dy))
            else:
                widget.place(x=widget.winfo_x()+dx,
                            y=widget.winfo_y()+dy)
    def draggable(self,tkwidget):
        if self.openport['bg'] == 'lightGray':
            # tkwidget为一个控件(Widget)或一个窗口(Wm)
            tkwidget.bind("<Button-1>",self.mousedown,add='+')
            tkwidget.bind("<B1-Motion>",self.drag,add='+')
        else:
            tkwidget.unbind("<Button-1>")
            tkwidget.unbind("<B1-Motion>")     
if __name__ == '__main__':
    my_ser1 = MainSerial()
    my_ser1.show()
