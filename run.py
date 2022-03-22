import json
import threading
import time

import PyQt5
import serial.tools.list_ports
from PyQt5 import Qt, QtGui
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QMutex, QMutexLocker
from PyQt5.QtGui import QImage, QPixmap, QCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTreeWidgetItem, QInputDialog, QLineEdit, QMenu, \
    QAction
from PyQt5.uic.properties import QtCore
from cv2.cv2 import *

from PyDMX import PyDMX
from sdr import Ui_Form


class Main(QMainWindow):
    video_url = ""
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2
    isPause = False
    jsonFile = None
    vFrameCount =0
    timeLong = 0
    dmx = None
    dmx_thread = None
    dmx_thread_flag = False
    jsonInfo=None

    def __init__(self):
        super(Main, self).__init__()

        # build ui
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.treeWidgetSDR.setHeaderLabels(['Key','Value'])
        self.ui.treeWidgetSDR.itemDoubleClicked.connect(self.on_tree_double_click)
        self.ui.treeWidgetSDR.setContextMenuPolicy(PyQt5.QtCore.Qt.CustomContextMenu)
        self.ui.treeWidgetSDR.customContextMenuRequested.connect(self.on_context_menu)
        #self.ui.treeWidgetSDR.setHeaderHidden(True)
        #data = ["COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9","COM10","COM11","COM12","COM13","COM14","COM15"]
        data = list(serial.tools.list_ports.comports())
        for comi in data:
            self.ui.comboBox_COM.addItem(comi.device)
        #self.ui.comboBox_COM.addItems(data)
        self.ui.pushButton_open.clicked.connect(self.on_open_file)
        self.ui.pushButton_pause.clicked.connect(self.on_pause)
        self.ui.labelvideo.mousePressEvent = self.on_mouse_press
        self.ui.pushButton_torgbw.clicked.connect(self.on_rgbw)
        self.ui.pushButtontodmx.clicked.connect(self.on_dmx)
        self.ui.pushButtonto_savejsn.clicked.connect(self.on_save_jsn)
        self.ui.pushButton_toJsnList.clicked.connect(self.on_add_list)
        self.ui.horizontalSlider.valueChanged.connect(self.on_slider_change)
        self.ui.pushButton_loadJsn.clicked.connect(self.on_open_jsn)
        self.jsonFile = self.readJason("default.jsn")
        # connect signals
        #self.ui.some_button.connect(self.on_button)
        self.timer = VideoTimer()
        self.timer.timeSignal.signal[str].connect(self.show_video_images)

        self.playCapture = VideoCapture()
        self.dmx_thread = None

    def on_tree_double_click(self,item,col):
        print(item,col)
        item_text = item.text(1)
        item_name = item.text(0)
        if item_text is None:
            return
        if len(item_text) == 0 :
            return
        text,baction = QInputDialog.getText(self,item.text(0),"Please input new value",QLineEdit.Normal,item_text)
        if baction:
            print(text)
            item.setText(1,text)
            if item_name == "SN":
                self.jsonFile["SN"] = text
                return
            if item_name == "video_count":
                self.jsonFile["video_count"] = text
                return
            if item_name == "4g_adapter":
                self.jsonFile["4g_adapter"] = text
                return
            if item_name == "server_ip":
                self.jsonFile["server_ip"] = text
                return
            if item_name == "server_port":
                self.jsonFile["server_port"] = text
            else:
                if item.parent().parent().text(0)== "video_info":
                    idx = str(item.parent().text(0))
                    if item_name == "name":
                        self.jsonFile["video_info"][idx]["name"] = text
                    if item_name == "wave_name":
                        self.jsonFile["video_info"][idx]["wave_name"] = text
                    if item_name == "play_time":
                        self.jsonFile["video_info"][idx]["play_time"] = text
                    if item_name == "RGBW_list_count":
                        self.jsonFile["video_info"][idx]["RGBW_list_count"]  =int(text)
                if item.parent().parent().text(0) == "RGBW_list_info":
                    idx = int(item.parent().text(0))
                    idx1 = int(item.parent().parent().parent().text(0))
                    if item_name == "time":
                        self.jsonFile["video_info"][idx1]["RGBW_list_info"][idx]["time"] = text
                    if item_name == "RGBW":
                        self.jsonFile["video_info"][idx1]["RGBW_list_info"][idx]["RGBW"] = text
                    if item_name == "RGBW_CHANGED":
                        self.jsonFile["video_info"][idx1]["RGBW_list_info"][idx]["RGBW_CHANGED"] = text


        #item = self.ui.treeWidgetSDR.currentItem()
        #if col == 1 :
        #item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)


        '''
        for ii in self.ui.treeWidgetSDR.selectedItems():
            print(ii.text(0))
            ii.setFlags(ii.flags()| Qt.ItemIsEditable)
        '''
        pass

    def on_start_thread(self):
        if self.dmx_thread == None:
            self.dmx_thread_flag = True
            self.dmx_thread = threading.Thread(target=self.on_dmx_thread)
            self.dmx_thread.start()


    def on_dmx_thread(self):
        while( self.dmx_thread_flag):
            time.sleep(1)
            comname = self.ui.comboBox_COM.currentText()
            if comname is None:
                continue
            if len(comname) < 3:
                continue
            #if self.dmx == None:
            #    self.dmx = PyDMX(comname)
            try:
                if self.dmx == None:
                    self.dmx = PyDMX(comname)
                r = self.ui.textEdit_r_2.toPlainText()
                g = self.ui.textEdit_g_2.toPlainText()
                b = self.ui.textEdit_b_2.toPlainText()
                w = self.ui.textEdit_w.toPlainText()
                self.dmx.set_data(1,int(r))
                self.dmx.set_data(2,int(g))
                self.dmx.set_data(3,int(b))
                self.dmx.set_data(4,int(w))
                self.dmx.send()
            except  Exception:
                pass

    def on_exit(self):
        if self.dmx_thread_flag:
            self.dmx_thread_flag = False
            self.dmx_thread.join
        if self.dmx != None:
            del self.dmx
    def __del__(self):
        self.on_exit()
    def on_slider_change(self):
        va = self.ui.horizontalSlider.value()
        print(va)
        cur_frame = va*0.01*self.vFrameCount
        self.playCapture.set(CAP_PROP_POS_FRAMES,cur_frame)
        pass
    def on_open_jsn(self):
        self.ui.treeWidgetSDR.clear()
        files, ok1 = QFileDialog.getOpenFileNames(self,"视频选择","./","All Files (*);;movie Files (*.mp4);;movie Files (*.avi)")
        print(files,ok1)
        if len(files) != 0:
            print(files[0])
            self.jsonFile = self.readJason(files[0])
            self.show_on_tree()
        pass

    def treeWidgetAddItem(self,parent,key,value):
        tw = QTreeWidgetItem(parent)
        tw.setText(0,str(key))
        if value != None:
            tw.setText(1,str(value))
        return tw

    def show_on_tree(self):
        #self.ui.
        print("treeView init____")

        it = self.treeWidgetAddItem(self.ui.treeWidgetSDR,"SN",self.jsonFile["SN"])

        #it.setFlags(QtCore.Qt.ItemIsEditable)
        self.treeWidgetAddItem(self.ui.treeWidgetSDR,"video_count",self.jsonFile["video_count"])
        self.treeWidgetAddItem(self.ui.treeWidgetSDR,"4g_adapter",self.jsonFile["4g_adapter"])
        self.treeWidgetAddItem(self.ui.treeWidgetSDR,"server_ip",self.jsonFile["server_ip"])
        self.treeWidgetAddItem(self.ui.treeWidgetSDR,"server_port",self.jsonFile["server_port"])
        rt = self.treeWidgetAddItem(self.ui.treeWidgetSDR,"video_info",None)
        count = len(self.jsonFile["video_info"])
        for i in range(count):
            rt1 = self.treeWidgetAddItem(rt,str(i),None)
            self.treeWidgetAddItem(rt1,"name",self.jsonFile["video_info"][i]["name"])
            self.treeWidgetAddItem(rt1,"wave_name",self.jsonFile["video_info"][i]["wave_name"])
            self.treeWidgetAddItem(rt1,"play_time",self.jsonFile["video_info"][i]["play_time"])
            self.treeWidgetAddItem(rt1,"RGBW_list_count",self.jsonFile["video_info"][i]["RGBW_list_count"])
            rt2 = self.treeWidgetAddItem(rt1,"RGBW_list_info",None)
            count1 = len(self.jsonFile["video_info"][i]["RGBW_list_info"])
            for j in range(count1):
                rt3 = self.treeWidgetAddItem(rt2,str(j),None)
                self.treeWidgetAddItem(rt3,"time",self.jsonFile["video_info"][i]["RGBW_list_info"][j]["time"])
                self.treeWidgetAddItem(rt3,"RGBW",self.jsonFile["video_info"][i]["RGBW_list_info"][j]["RGBW"])
                self.treeWidgetAddItem(rt3,"RGBW_CHANGED",self.jsonFile["video_info"][i]["RGBW_list_info"][j]["RGBW_CHANGED"])
        pass
    def on_save_jsn(self):
        file,ok1 = QFileDialog.getSaveFileName(self,"Save","../","JASON(*.jsn")
        if not file:
            return
        print(file)
        self.writeJason(self.jsonFile,file)
        pass
    def on_add_list(self):
        '''
        st = self.ui.textEdit_v_time.toPlainText()
        if st is None:
            return
        rgbw = self.ui.textEdit_rgbw.toPlainText()
        if rgbw is None:
            return
        item = {"time":"00:00:00","RGBW":[0,0,0,0],"RGBW_CHANGED":[-1,-1,-1,-1]}
        item["time"] = st
        rgbw = rgbw.split(',')
        item["RGBW"][0] = int(rgbw[0])
        item["RGBW"][1] = int(rgbw[1])
        item["RGBW"][2] = int(rgbw[2])
        item["RGBW"][3] = int(rgbw[3])
        outtxt = (time.strftime('%H:%M:%S',time.gmtime(self.timeLong)))
        self.jsonFile["play_time"] = outtxt
        #self.jsonFile["RGBW_list_count"] +=1
        self.jsonFile["RGBW_list_info"].append(item)
        self.jsonFile["RGBW_list_count"] = len(self.jsonFile["RGBW_list_info"])
        '''
    def on_dmx(self):
        self.on_start_thread()
        comname = self.ui.comboBox_COM.currentText()
        if comname is None:
            return
        if len(comname) < 3:
            return

        #data = str(data).split(",")
        try:
            if self.dmx == None:
                self.dmx = PyDMX(comname)
            r = self.ui.textEdit_r_2.toPlainText()
            g = self.ui.textEdit_g_2.toPlainText()
            b = self.ui.textEdit_b_2.toPlainText()
            w = self.ui.textEdit_w.toPlainText()
            self.dmx.set_data(1,int(r))
            self.dmx.set_data(2,int(g))
            self.dmx.set_data(3,int(b))
            self.dmx.set_data(4,int(w))
            self.dmx.send()
        except Exception:
            print("error in dmx")
        #del self.dmx
        pass

    def treeWidget_reflesh(self):
        self.ui.treeWidgetSDR.clear()
        self.show_on_tree()
    def new_cluster(self):
        print("New Cluster")
        current_item = self.ui.treeWidgetSDR.currentItem()
        if current_item.text(0).isnumeric():
            idx = int(current_item.text(0))
            if current_item.parent().text(0) == "video_info":
                defalutj = { "name":"defalut.mp4","wave_name":"default.wav","play_time":"00:01:00","RGBW_list_count":1,"RGBW_list_info": [{"time":"0:00:00","RGBW":[255,150,0,0],"RGBW_CHANGED":[-1,-1,-1,-1]}]}
                self.jsonFile["video_info"].append(defalutj)
                self.jsonFile["video_count"] = len(self.jsonFile["video_info"])
                it2 = self.ui.treeWidgetSDR.topLevelItem(1)
                #itf = self.ui.treeWidgetSDR.findItems("video_count")
                it2.setText(1,str(self.jsonFile["video_count"]))
                rt1 = self.treeWidgetAddItem(current_item.parent(),str(self.jsonFile["video_count"]-1),None)
                self.treeWidgetAddItem(rt1,"name","defalut.mp4")
                self.treeWidgetAddItem(rt1,"wave_name","default.wav")
                self.treeWidgetAddItem(rt1,"play_time","00:01:00")
                self.treeWidgetAddItem(rt1,"RGBW_list_count","1")
                rt2 = self.treeWidgetAddItem(rt1,"RGBW_list_info",None)
                rt3 = self.treeWidgetAddItem(rt2,"0",None)
                self.treeWidgetAddItem(rt3,"time","00:00:00")
                self.treeWidgetAddItem(rt3,"RGBW","[255,150,0,0]")
                self.treeWidgetAddItem(rt3,"RGBW_CHANGED","[-1,-1,-1,-1]")

                #self.treeWidget_reflesh()
            if current_item.parent().text(0) == "RGBW_list_info":
                defalutj =  {"time":"0:00:00","RGBW":[255,150,0,0],"RGBW_CHANGED":[-1,-1,-1,-1] }
                pidx = int(current_item.parent().parent().text(0))
                self.jsonFile["video_info"][pidx]["RGBW_list_info"].append(defalutj)
                self.jsonFile["video_info"][pidx]["RGBW_list_count"] = len(self.jsonFile["video_info"][pidx]["RGBW_list_info"])
                rt3 = self.treeWidgetAddItem(current_item.parent(),str(self.jsonFile["video_info"][pidx]["RGBW_list_count"]-1),None)
                self.treeWidgetAddItem(rt3,"time","00:00:00")
                self.treeWidgetAddItem(rt3,"RGBW","[255,150,0,0]")
                self.treeWidgetAddItem(rt3,"RGBW_CHANGED","[-1,-1,-1,-1]")
                current_item.parent().parent().child(3).setText(1,str(self.jsonFile["video_info"][pidx]["RGBW_list_count"]))
                #self.treeWidget_reflesh()
    def delete_cluster(self):
        print("Delete cluster")
        current_item = self.ui.treeWidgetSDR.currentItem()
        if current_item.text(0).isnumeric():
            idx = int(current_item.text(0))
            if current_item.parent().text(0) == "video_info":
                self.jsonFile["video_info"].pop(idx)
                self.jsonFile["video_count"] = len(self.jsonFile["video_info"])
                self.treeWidget_reflesh()
            if current_item.parent().text(0) == "RGBW_list_info":
                if idx ==0:
                    return
                pidx = int(current_item.parent().parent().text(0))
                self.jsonFile["video_info"][pidx]["RGBW_list_info"].pop(idx)
                self.jsonFile["video_info"][pidx]["RGBW_list_count"] = len(self.jsonFile["video_info"][pidx]["RGBW_list_info"])
                self.treeWidget_reflesh()
    def play_cluster(self):
        current_item = self.ui.treeWidgetSDR.currentItem()
        url = current_item.text(1)
        if url.find(".mp4") != -1:
            self.video_url = str(url)
            print(self.video_url)
            self.stop()
            self.play()

    def on_context_menu(self, pos):
        current_item = self.ui.treeWidgetSDR.currentItem()
        item_flag = self.ui.treeWidgetSDR.itemAt(pos)
        if current_item is not None and item_flag is not None:
            popMenu = QMenu()
            newact = QAction('New', self)
            newact.triggered.connect(self.new_cluster)  # 连接删除功能（未定义）
            popMenu.addAction(newact)
            delact = QAction("Del", self)
            delact.triggered.connect(self.delete_cluster)  # 连接删除功能（未定义）
            popMenu.addAction(delact)
            rgbwlact = QAction("ToRGBW", self)
            rgbwlact.triggered.connect(self.rgbwlact_cluster)  # 连接删除功能（未定义）
            popMenu.addAction(rgbwlact)
            playact = QAction("Play", self)
            playact.triggered.connect(self.play_cluster)  # 连接删除功能（未定义）
            popMenu.addAction(playact)
            popMenu.exec_(QCursor.pos())
        return

    def rgbwlact_cluster(self):
        current_item = self.ui.treeWidgetSDR.currentItem()
        tinfo = current_item.text(0)
        if tinfo == "RGBW" or tinfo== "RGBW_CHANGED":
            idx = int(current_item.parent().text(0))
            idx1 = int(current_item.parent().parent().parent().text(0))
            linfo = self.jsonFile["video_info"][idx1]["RGBW_list_info"][idx]["RGBW"]
            if(linfo[0] == -1):
                return
            self.ui.textEdit_r_2.setText(str(linfo[0]))
            self.ui.textEdit_g_2.setText(str(linfo[1]))
            self.ui.textEdit_b_2.setText(str(linfo[2]))
            self.ui.textEdit_w.setText(str(linfo[3]))

    def on_rgbw(self):
        r = self.ui.textEdit_r.toPlainText()
        g = self.ui.textEdit_g.toPlainText()
        b = self.ui.textEdit_b.toPlainText()
        r,g,b,w = self.rgb_to_rgbw_method_1(r,g,b)
        self.ui.textEdit_r_2.setText(str(r))
        self.ui.textEdit_b_2.setText(str(b))
        self.ui.textEdit_g_2.setText(str(g))
        self.ui.textEdit_w.setText(str(w))
        #self.ui.textEdit_rgbw.setText(str(r)+","+str(g)+","+str(b)+","+str(w))
        pass
    def on_mouse_press(self,ev):
        print("lable pressed",ev.pos())
        if self.ui.labelvideo.pixmap() == None:
            return
        img = self.ui.labelvideo.pixmap().toImage()
        color = img.pixelColor(ev.pos())
        self.ui.textEdit_r.setText(str(color.red()))
        self.ui.textEdit_g.setText(str(color.green()))
        self.ui.textEdit_b.setText(str(color.blue()))
        self.ui.pushButton_torgbw.setStyleSheet("background-color:rgb("+str(color.red())+","+str(color.green())+","+str(color.blue())+")")


        #print(color)


    def on_pause(self):
        if self.isPause :
            self.isPause = False
        else:
            self.isPause = True
    def on_open_file(self):
        files, ok1 = QFileDialog.getOpenFileNames(self,
                                                  "视频选择",
                                                  "./",
                                                  "All Files (*);;movie Files (*.mp4);;movie Files (*.avi)")
        print(files,ok1)
        if len(files) != 0:
            self.video_url = files[0]
        print(self.video_url)
        self.stop()
        self.play()

    def show_video_images(self):
        if self.isPause:
            return
        if self.playCapture.isOpened():
            st = (self.playCapture.get(CAP_PROP_POS_MSEC))
            st = int(st/1000)
            outtxt = (time.strftime('%H:%M:%S',time.gmtime(st)))
            self.ui.textEdit_v_time.setText(outtxt)
            curr_frame = self.playCapture.get(CAP_PROP_POS_FRAMES)
            pos = curr_frame/self.vFrameCount
            pos = int(pos*100)
            self.ui.horizontalSlider.setValue(pos)
            success, frame = self.playCapture.read()
            if success:
                height, width = frame.shape[:2]
                if frame.ndim == 3:
                    rgb = cvtColor(frame, COLOR_BGR2RGB)
                elif frame.ndim == 2:
                    rgb = cvtColor(frame, COLOR_GRAY2BGR)

                temp_image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
                temp_pixmap = QPixmap.fromImage(temp_image)
                self.ui.labelvideo.setPixmap(temp_pixmap)

            else:
                print("read failed, no frame data")
                success, frame = self.playCapture.read()
                if not success :
                    print("play finished")  # 判断本地文件播放完毕
                    self.reset()
                    return
                else:
                    print("open file or capturing device error, init again")
                    self.reset()
    def rgb_to_rgbw_method_1(self,r,g,b):
        r = int(r)
        g = int(g)
        b = int(b)
        aph = 1.5 # 1<a<2.5
        value_min = min(r,g,b)[0][0]
        value_max = max(r,g,b)[0][0]
        value_m = value_min/value_max
        led_w = value_min*aph
        led_r = (1+value_m)*r-led_w
        if led_r < 0:
            led_r = 0
        led_g = (1+value_m)*g-led_w
        if led_g < 0:
            led_g =0
        led_b = (1+value_m)*b-led_w
        if led_b < 0:
            led_b = 0
        return int(led_r),int(led_g),int(led_b),int(led_w)

    def set_timer_fps(self):
        self.playCapture.open(self.video_url)
        fps = self.playCapture.get(CAP_PROP_FPS)
        self.timer.set_fps(fps)
        self.playCapture.release()

    def stop(self):
        if self.video_url == "" or self.video_url is None:
            return
        if self.playCapture.isOpened():
            self.timer.stop()
        self.playCapture.release()

    def play(self):
        if self.video_url == "" or self.video_url is None:
            return
        if not self.playCapture.isOpened():
            self.playCapture.open(self.video_url)
            height = self.playCapture.get(CAP_PROP_FRAME_HEIGHT)
            width = self.playCapture.get(CAP_PROP_FRAME_WIDTH)
            self.ui.labelvideo.resize(width,height)
            self.vFrameCount = self.playCapture.get(CAP_PROP_FRAME_COUNT)
            self.timeLong = self.vFrameCount/self.playCapture.get(CAP_PROP_FPS)
            outtxt = (time.strftime('%H:%M:%S',time.gmtime(self.timeLong)))
            self.ui.label_file_time_long.setText(outtxt)
        self.timer.start()
    def reset(self):
        self.timer.stop()
        self.playCapture.release()
    def readJason(self,str_filename):
        with open(str_filename,'r') as load_f:
            load_dict = json.load(load_f)
            return load_dict
        return None
    def writeJason(self,jsn_data,str_filename):
        with open(str_filename,'w') as f:
            json.dump(jsn_data,f)


class Communicate(QObject):

    signal = pyqtSignal(str)


class VideoTimer(QThread):

    def __init__(self, frequent=20):
        QThread.__init__(self)
        self.stopped = False
        self.frequent = frequent
        self.timeSignal = Communicate()
        self.mutex = QMutex()

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
        while True:
            if self.stopped:
                return
            self.timeSignal.signal.emit("1")
            time.sleep(1 / self.frequent)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, fps):
        self.frequent = fps

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = Main()
    w.show()
    try:
        sys.exit(app.exec_())
    except SystemExit:
        w.on_exit()
        print('Closing Window...')
