import os
import sys
import subprocess 
 
#编写bat脚本，删除旧程序，运行新程序
def WriteRestartCmd(new_name,old_name):
    b = open("upgrade.bat",'w')
    TempList = "@echo off\n"
    TempList += "if not exist " + new_name + " exit \n"  #判断是否有新版本的程序，没有就退出更新。
    TempList += "echo 正在更新至最新版本...\n"
    TempList += "timeout /t 10 /nobreak\n"  #等待10秒
    TempList += "del " + old_name + "\n" #删除旧程序
    TempList += "copy  " + new_name + " " + old_name + '\n' #复制新版本程序
    TempList += "echo 更新完成，正在启动...\n"
    TempList += "timeout /t 3 /nobreak\n"
    TempList += "start  " + old_name+"\n"   #"start 1.bat\n"
    TempList += "exit"
    b.write(TempList)
    b.close()
    subprocess.Popen("upgrade.bat") #不显示cmd窗口
    # os.system('start upgrade.bat')  #显示cmd窗口
 
 
def main():
#新程序启动时，删除旧程序制造的脚本
    if os.path.isfile("upgrade.bat"):
        os.remove("upgrade.bat")
    WriteRestartCmd("newVersion.exe","Version.exe")
 
if __name__ == '__main__':
    main()
    sys.exit()