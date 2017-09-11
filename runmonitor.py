#!/usr/bin/env python
# coding:gbk
import os
import re
import sys
import time
import datetime
import pycurl
import string
import MySQLdb
import logging
import urllib
from decimal import Decimal
import smtplib
from email.mime.text import MIMEText
import sys
reload(sys)
sys.setdefaultencoding('gbk')

if len(sys.argv) <> 3:
    print "Usage: " + sys.argv[0] + " IDC Location"
    sys.exit(-1)

DBNAME='yw_netmonitor'
DBUSER='networkmonitor'
DBPASSWORD='networkmonitor161014'
DBHOST='gamedb.netmonitor.TXWX.db'
DBPORT=10016

#IDC选项(1,"电信"),(2,"联通"),(3,"移动")
IDC = sys.argv[1]
#节点选项(1,"西安"),(2,"天津"),(3,"上海"),(4,"深圳"),(5,"香港")
NODE = sys.argv[2]

#连接超时时间
CONNECTTIMEOUT = 5
#请求超时时间
TIMEOUT = 10

MAILTO = ['toc@yuewen.com']
MOBILETO=" "


class Runmonitor():
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    filename='/data/log/runmonitor_syslog.log',
                    filemode='a')

        try:
            self.conn = MySQLdb.Connection(DBHOST, DBUSER, DBPASSWORD, DBNAME, DBPORT, init_command='set names gbk')
            self.cursor = self.conn.cursor()
        except Exception, e:
            logging.error('connect database error!'+str(e))
            return

        self.HOST = []
        self.ALARM = []
        self.FID = 0
        self.NAMELOOKUP_TIME = 0.0
        self.CONNECT_TIME = 0.0
        self.PRETRANSFER_TIME = 0.0
        self.STARTTRANSFER_TIME = 0.0
        self.TOTAL_TIME = 0.0
        self.HTTP_CODE = '000'
        self.SIZE_DOWNLOAD = 0
        self.HEADER_SIZE = 0
        self.REQUEST_SIZE = 0
        self.CONTENT_LENGTH_DOWNLOAD = 0
        self.SPEED_DOWNLOAD = 0.0
        self.DATETIME = 0
        self.MARK = 0
        self.HOST_id = 0
        self.RunResult = ()

        self.mail_host = 'smtp.exmail.qq.com'
        self.mail_user = 'messagepush'
        self.mail_addr = 'messagepush@yuewen.com'
        self.mail_pass = 'Jw2bax'
        self.mail_postfix = 'yuewen.com'

        self.sms_exec_dir = '/usr/local/support/bin'
        self.MONITOR_NODE = {'1': u"西安",'2': u"天津",'3': u"上海",'4': u"深圳",'5': u"香港",'6':u"成都",'7':u"杭州"}
        self.MONITOR_IDC = {'1': u"电信",'2': u"联通",'3': u"移动"}
        self.STARTDATE = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __del__(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception,e:
            logging.debug('__del__ object error!'+str(e))

    def Alarm_mail(self, target, content, subject):
        os.system("/usr/bin/perl "+self.sms_exec_dir+'/send_mail.pl '+str(target)+' '+str(content)+' '+str(subject))

    def Alarm_all(self, target, content):
        os.system("/usr/bin/perl "+self.sms_exec_dir+'/send_all.pl '+str(target)+' '+str(content))

    def runhost(self):
        for _hostlist in self.HOST:
            code_list, alarm_list = [], []
            for a in range(5):
                time.sleep(5)
                self.FID = int(_hostlist[0])
                self.HOST_id = int(_hostlist[0])
                self.DATETIME = int(str(time.time()).split('.')[0])
                self.IDC = _hostlist[2]
                self.NODE = _hostlist[6]

                try:
                    url = _hostlist[1].strip()
                    Curlobj = pycurl.Curl()
                    Curlobj.setopt(Curlobj.URL, url)
                    if _hostlist[8]:
                        Curlobj.setopt(Curlobj.POST, 1)
                        Curlobj.setopt(Curlobj.POSTFIELDS, urllib.quote_plus(_hostlist[7]))
                    else:
                        Curlobj.setopt(Curlobj.HTTPGET, 1)

                    Curlobj.setopt(Curlobj.CONNECTTIMEOUT, CONNECTTIMEOUT)

                    Curlobj.setopt(Curlobj.SSL_VERIFYPEER, 0)
                    Curlobj.setopt(Curlobj.SSL_VERIFYHOST, 0)
                    Curlobj.setopt(Curlobj.TIMEOUT, TIMEOUT)
                    Curlobj.setopt(Curlobj.NOPROGRESS, 0)
                    Curlobj.setopt(Curlobj.FOLLOWLOCATION, 1)
                    Curlobj.setopt(Curlobj.MAXREDIRS, 5)
                    Curlobj.setopt(Curlobj.OPT_FILETIME, 1)
                    Curlobj.setopt(Curlobj.NOPROGRESS, 1)

                    bodyfile = open(os.path.dirname(os.path.realpath(__file__))+"/_body", "wb")
                    Curlobj.setopt(Curlobj.WRITEDATA, bodyfile)
                    Curlobj.perform()
                    bodyfile.close()

                    self.NAMELOOKUP_TIME = Decimal(str(round(Curlobj.getinfo(Curlobj.NAMELOOKUP_TIME), 2)))
                    self.CONNECT_TIME = Decimal(str(round(Curlobj.getinfo(Curlobj.CONNECT_TIME), 2)))
                    self.PRETRANSFER_TIME = Decimal(str(round(Curlobj.getinfo(Curlobj.PRETRANSFER_TIME), 2)))
                    self.STARTTRANSFER_TIME = Decimal(str(round(Curlobj.getinfo(Curlobj.STARTTRANSFER_TIME), 2)))
                    self.TOTAL_TIME = Decimal(str(round(Curlobj.getinfo(Curlobj.TOTAL_TIME), 2)))
                    self.HTTP_CODE = Curlobj.getinfo(Curlobj.HTTP_CODE)
                    #self.ALARM = Curlobj.getinfo(Curlobj.HTTP_CODE)
                    code_list.append(self.HTTP_CODE)
                    self.SIZE_DOWNLOAD = Curlobj.getinfo(Curlobj.SIZE_DOWNLOAD)
                    self.HEADER_SIZE = Curlobj.getinfo(Curlobj.HEADER_SIZE)
                    self.REQUEST_SIZE = Curlobj.getinfo(Curlobj.REQUEST_SIZE)
                    self.CONTENT_LENGTH_DOWNLOAD = Decimal(str(round(Curlobj.getinfo(Curlobj.CONTENT_LENGTH_DOWNLOAD),2)))
                    self.SPEED_DOWNLOAD = Curlobj.getinfo(Curlobj.SPEED_DOWNLOAD)

                    if str(_hostlist[4]) != "200":
                        returncontent = ''.join(open(os.path.dirname(os.path.realpath(__file__))+'/_body', 'rb').readlines())
                        match = re.findall(_hostlist[4], returncontent)
                        if not match:
                            self.HTTP_CODE = "000"
                            _target = _hostlist[7]
                            if _hostlist[3] == "mobile+email":
                                self.Alarm_all(_target, "探测["+_hostlist[5]+"]"+"["+self.MONITOR_NODE[str(_hostlist[6])]+"]"+"["+self.MONITOR_IDC[str(_hostlist[2])]+"]应用返回串与设定值不一致")
                            else:
                                contentheader = "应用异常报警通知"
                                self.Alarm_mail(_target, "探测["+_hostlist[5]+"]"+"["+self.MONITOR_NODE[str(_hostlist[6])]+"]"+"["+self.MONITOR_IDC[str(_hostlist[2])]+"]应用返回串与设定值不一致,"+"探测目标URL为["+url+"]", "["+_hostlist[5]+"]"+"["+self.MONITOR_NODE[str(_hostlist[6])]+"]"+"["+self.MONITOR_IDC[str(_hostlist[2])]+"]"+_contentheader)
                                logging.error(u'返回串不一致邮件已执行!')

                except Exception, e:
                    self.NAMELOOKUP_TIME = 0.0
                    self.CONNECT_TIME = 0.0
                    self.PRETRANSFER_TIME = 0.0
                    self.STARTTRANSFER_TIME = 0.0
                    self.TOTAL_TIME = 0.0
                    self.HTTP_CODE = str(e).replace("'", "\''")
                    code_list.append(self.HTTP_CODE)
                    self.SIZE_DOWNLOAD = 0
                    self.HEADER_SIZE = 0
                    self.REQUEST_SIZE = 0
                    self.CONTENT_LENGTH_DOWNLOAD = 0
                    self.SPEED_DOWNLOAD = 0.0
                    self.MARK = 0

                    logging.error('pycurl url reset:'+str(e))

                self.RunResult=(self.FID, self.NAMELOOKUP_TIME, self.CONNECT_TIME,self.PRETRANSFER_TIME,self.STARTTRANSFER_TIME,self.TOTAL_TIME, \
                            self.HTTP_CODE, self.SIZE_DOWNLOAD, self.HEADER_SIZE,self.REQUEST_SIZE,self.CONTENT_LENGTH_DOWNLOAD,self.SPEED_DOWNLOAD, \
                            self.DATETIME, self.MARK, self.HOST_id)
                try:
                    self.cursor.execute("insert into yw_monitor_monitordata (`ID`, `FID`, `NAMELOOKUP_TIME`, `CONNECT_TIME`, `PRETRANSFER_TIME`, `STARTTRANSFER_TIME`, `TOTAL_TIME`, `HTTP_CODE`, `SIZE_DOWNLOAD`, `HEADER_SIZE`, `REQUEST_SIZE`, `CONTENT_LENGTH_DOWNLOAD`, `SPEED_DOWNLOAD`, `DATETIME`, `MARK`, `HOST_id`) VALUES (0,'%d','%f','%f','%f','%f','%f','%s','%f','%d','%d','%f','%f','%d','%d','%d')"%(self.RunResult))
                    self.conn.commit()
                except Exception,e:
                    logging.debug('monitordata insert error:'+str(e))

            if code_list:
                if code_list.count(200) < 2 and max(code_list)>399:
                    _target = _hostlist[7]

                    if _hostlist[3] == "mobile+email":
                        self.Alarm_all(_target, "'探测["+_hostlist[5]+"]["+self.MONITOR_NODE[str(_hostlist[6])]+"'-'"+self.MONITOR_IDC[str(_hostlist[2])]+"]应用异常, 探测时间为"+self.STARTDATE+", 探测目标URL为"+url+", 报错信息为["+','.join(map(str, [x for x in list(set(code_list)) if x!='200']))+"]'")
                    else:
                        _contentheader = "应用异常报警通知"
                        self.Alarm_mail(_target, "'探测["+_hostlist[5]+"]["+self.MONITOR_NODE[str(_hostlist[6])]+"'-'"+self.MONITOR_IDC[str(_hostlist[2])]+"]应用异常, 探测时间为"+self.STARTDATE+", 探测目标URL为"+url+", 报错信息为["+','.join(map(str, list(set(code_list))))+"]'", "'["+_hostlist[5]+"]["+self.MONITOR_NODE[str(_hostlist[6])]+"'-'"+self.MONITOR_IDC[str(_hostlist[2])]+"]"+_contentheader+"'")

            #if alarm_list:
                #if str(_hostlist[4]) == "200" and alarm_list.count(200) < 3:
                #if alarm_list.count(200) < 3:            
                    #_target = _hostlist[7]
                    #_target = 'p_nnanli'
                    #if _hostlist[3] == "mobile+email":
                        #self.Alarm_all(_target, "探测["+_hostlist[5]+"]"+"["+self.MONITOR_NODE[str(_hostlist[6])]+"]"+"["+self.MONITOR_IDC[str(_hostlist[2])]+"]应用返回非200状态["+str(alarm_list[0])+"]")
                    #else:
                        #_contentheader="应用异常报警通知[非200状态]"
                        #self.Alarm_mail(_target, "探测["+_hostlist[5]+"]"+"["+self.MONITOR_NODE[str(_hostlist[6])]+"]"+"["+self.MONITOR_IDC[str(_hostlist[2])]+"]应用返回非200状态["+str(alarm_list[0])+"],"+"探测目标URL为["+url+"]", "["+_hostlist[5]+"]"+"["+self.MONITOR_NODE[str(_hostlist[6])]+"]"+"["+self.MONITOR_IDC[str(_hostlist[2])]+"]"+_contentheader)
                    #logging.error(u'非200邮件已执行!')

            Curlobj.close()

    def readhost(self):
        self.cursor.execute("select ID, URL, IDC, Alarmtype, Alarmconditions, APPName, NODE, Alarm_Person, POST from yw_monitor_hostinfo where IDC='%s' and NODE='%s'"%(IDC, NODE))
        for row in self.cursor.fetchall():
            self.HOST.append(row)

    def GetURLdomain(self, url):
        xurl = ""
        if url[:7] == "http://":
            xurl = url[7:]
        else:
            xurl = url
        return string.split(xurl, '/')[0]

if __name__ == '__main__':
    app = Runmonitor()
    app.readhost()
    app.runhost()
