# coding:utf-8

import time
import datetime
import os
import re
import string
import logging
import rrdtool
from yw_monitor.models import Hostinfo, MonitorData
from decimal import Decimal
from django.db import connections
from PIL import Image
from config import *
from common.log import logger


def GetURLdomain(url):
    if url[:7] == "http://":
        xurl = url[7:]
    elif url[:8] == "https://":
        xurl = url[8:]
    else:
        xurl = url
    return string.split(xurl, '/')[0]


def Graphrrd_normal(_id, url, appname):

    rrdfiletype = ['time', 'download', 'unavailable']
    GraphDate = ['current', 'day', 'month', 'year']
    GraphStart = ['-3h', '-1day', '-1month', '-1year']
    GraphEnd = ['now', 'now', 'now', 'now']

    Appdomain = str(GetURLdomain(url))

    if not os.path.isdir(PNGPATH+'/'+GetURLdomain(url)):
        os.makedirs(PNGPATH+'/'+GetURLdomain(url))

    time_rrdpath = RRDPATH+'/'+Appdomain+'/'+str(_id)+'_'+str(rrdfiletype[0])+'.rrd'
    download_rrdpath = RRDPATH+'/'+Appdomain+'/'+str(_id)+'_'+str(rrdfiletype[1])+'.rrd'
    unavailable_rrdpath = RRDPATH+'/'+Appdomain+'/'+str(_id)+'_'+str(rrdfiletype[2])+'.rrd'

    i = 0
    for datetype in GraphDate:
        time_pngpath = PNGPATH+'/'+Appdomain+'/'+str(datetype)+'_'+str(_id)+'_'+str(rrdfiletype[0])+'.png'
        download_pngpath = PNGPATH+'/'+Appdomain+'/'+str(datetype)+'_'+str(_id)+'_'+str(rrdfiletype[1])+'.png'
        unavailable_pngpath = PNGPATH+'/'+Appdomain+'/'+str(datetype)+'_'+str(_id)+'_'+str(rrdfiletype[2])+'.png'

        try:
            os.system("/bin/sh  "+MAINAPPPATH+'/graphrrd.sh '+str(time_rrdpath)+' '+str(time_pngpath)+' '+'time'+' '+appname.encode('utf-8')+' '+GraphStart[i]+' '+GraphEnd[i]+' '+str(TIME_YMAX)+' '+str(TIME_ALARM))
            os.system("/bin/sh  "+MAINAPPPATH+'/graphrrd.sh '+str(download_rrdpath)+' '+str(download_pngpath)+' '+'download'+' '+appname.encode('utf-8')+' '+GraphStart[i]+' '+GraphEnd[i]+' '+str(DOWN_APEED_YMAX))
            os.system("/bin/sh  "+MAINAPPPATH+'/graphrrd.sh '+str(unavailable_rrdpath)+' '+str(unavailable_pngpath)+' '+'unavailable'+' '+appname.encode('utf-8')+' '+GraphStart[i]+' '+GraphEnd[i])
            logger.debug(rrdtool.last(time_rrdpath))
        except Exception, e:
            logger.error('Graphrrd normal rrd png error: '+str(e))
        i += 1


def Graphrrd_custom(_id, _starttime, _endtime, url, appname):

    StartTime = _starttime
    EndTime = _endtime
    rrdfiletype = ['time', 'download', 'unavailable']
    Appdomain = str(GetURLdomain(url))
    time_rrdpath = RRDPATH+'/'+Appdomain+'/'+str(_id)+'_time.rrd'
    download_rrdpath = RRDPATH+'/'+Appdomain+'/'+str(_id)+'_download.rrd'
    unavailable_rrdpath = RRDPATH+'/'+Appdomain+'/'+str(_id)+'_unavailable.rrd'
    time_pngpath = PNGPATH+'/'+Appdomain+'/'+str(_id)+'_time.png'
    download_pngpath = PNGPATH+'/'+Appdomain+'/'+str(_id)+'_download.png'
    unavailable_pngpath = PNGPATH+'/'+Appdomain+'/'+str(_id)+'_unavailable.png'

    try:
        os.system("/bin/sh  "+MAINAPPPATH+'/graphrrd.sh '+str(time_rrdpath)+' '+str(time_pngpath)+' '+'time'+' '+appname.encode('utf-8')+' '+str(StartTime)+' '+str(EndTime)+' '+str(TIME_YMAX)+' '+str(TIME_ALARM))
        os.system("/bin/sh  "+MAINAPPPATH+'/graphrrd.sh '+str(download_rrdpath)+' '+str(download_pngpath)+' '+'download'+' '+appname.encode('utf-8')+' '+str(StartTime)+' '+str(EndTime)+' '+str(DOWN_APEED_YMAX))
        os.system("/bin/sh  "+MAINAPPPATH+'/graphrrd.sh '+str(unavailable_rrdpath)+' '+str(unavailable_pngpath)+' '+'unavailable'+' '+appname.encode('utf-8')+' '+str(StartTime)+' '+str(EndTime))
    except Exception, e:
        logger.error('Graphrrd normal rrd png error:'+str(e))


def png2bmp(sourceadd, targetadd):

    try:
        file_in = sourceadd
        img = Image.open(file_in)
        file_out = targetadd
        if len(img.split()) == 4:
            r, g, b, a = img.split()
            img = Image.merge("RGB", (r, g, b))
            img.save(file_out)
        else:
            img.save(file_out)
        return
    except Exception, e:
        logger.error('Graph png2bmp error:'+str(e))


def GetAppDateReport(ID, _starttime, _endtime):

    ReportListobj = []

    try:
        cursor = connections['WebMonitor'].cursor()
        for _id in ID:
            cursor.execute("select avg(NAMELOOKUP_TIME),avg(CONNECT_TIME),avg(PRETRANSFER_TIME),avg(STARTTRANSFER_TIME),avg(TOTAL_TIME),avg(SPEED_DOWNLOAD) from yw_monitor_monitordata where HTTP_CODE='200' and FID='%d' and DATETIME>='%d' and DATETIME<='%d'"%(int(_id),int(_starttime),int(_endtime)))
            row = cursor.fetchone()
            ReportListobj.append(row)
        return ReportListobj
    except Exception, e:
        logger.error('select database error!'+str(e))


def GetAppUnavailableReport(ID, _starttime, _endtime):

    if ID == None:
        return MonitorData.objects.values('HTTP_CODE', 'DATETIME', 'FID').filter(DATETIME__gte=_starttime,DATETIME__lte=_endtime).exclude(HTTP_CODE='200').order_by('FID', 'ID')
    else:
        return MonitorData.objects.values('HTTP_CODE', 'DATETIME', 'FID').filter(FID__in=ID, DATETIME__gte=_starttime,DATETIME__lte=_endtime).exclude(HTTP_CODE='200').order_by('FID', 'ID')


def GetAppName(_id):
    return Hostinfo.objects.values('AppName').get(ID=_id)


def GetAppIDCId(_id):

    ID_list = []

    try:
        cursor = connections['WebMonitor'].cursor()
        if _id == None:
            cursor.execute("select ID from yw_monitor_hostinfo")
        else:
            cursor.execute("select ID from yw_monitor_hostinfo where URL in (select URL from yw_monitor_hostinfo where ID='%d')"%(int(_id)))
        for row in cursor.fetchall():
            ID_list.append(row[0])
        return ID_list
    except Exception, e:
        logger.error('select database error!'+str(e))


def GetAppIDCName(_id):

    ID_list = []

    try:
        cursor = connections['WebMonitor'].cursor()
        if _id == None:
            cursor.execute("select IDC, AppName from yw_monitor_hostinfo")
        else:
            cursor.execute("select IDC, AppName from yw_monitor_hostinfo where URL in (select URL from yw_monitor_hostinfo where ID='%d')"%(int(_id)))
        for row in cursor.fetchall():
            ID_list.append(row)
        return ID_list
    except Exception, e:
        logger.error('select database error!'+str(e))


def GetHostinfo(_id):
    return Hostinfo.objects.filter(ID=_id)


def time2stamp(_datetime):
    return int(time.mktime(time.strptime(_datetime, '%Y-%m-%d %H:%M:%S')))


def stamp2time(_stamp):
    stamp = time.localtime(_stamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", stamp)


def GetLastweek(_today):
    date = _today
    year, mon, day = int(date[:4]), int(date[4:6]), int(date[6:])
    d = datetime.datetime(year, mon, day)
    b = d-datetime.timedelta(d.weekday() + 1)
    days = []
    for i in range(6, -1, -1):
        c = b-datetime.timedelta(i)
        days.append(c.strftime('%Y-%m-%d'))
    return days


def CheckURLok(url):
    p = re.compile(r'^(http://)?[a-zA-Z0-9]+(.[a-zA-Z0-9]+)*(\w|/)+$')
    m = p.match(url)
    if m:
        return True
    else:
        return False


def GetURLdopath(url):
    xurl = ""
    if url[:7] == "http://":
        xurl = url[8:]
    else:
        xurl = url
    return xurl[xurl.find('/'):]


def getID(url):
    URL = url
    HID = []
    cursor = connections['webmonitor'].cursor()
    cursor.execute("select ID from yw_monitor_hostinfo where URL='%s'"%(URL))
    for row in cursor.fetchall():
        HID.append(row[0])
    return HID


def create_rrd(url):
    URL = url
    domain = GetURLdomain(url)
    HID = []
    cur_time = str(int(time.time()))

    HID = getID(URL)
    for id in HID:
        try:
            rrd_time = rrdtool.create(RRDPATH+'/'+str(domain)+'/'+str(id)+ \
                    '_time.rrd','--step','300','--start', cur_time,
                    'DS:NAMELOOKUP_TIME:GAUGE:600:0:U',
                    'DS:CONNECT_TIME:GAUGE:600:0:U',
                    'DS:PRETRANSFER_TIME:GAUGE:600:0:U',
                    'DS:STARTTRANSFER_TIME:GAUGE:600:0:U',
                    'DS:TOTAL_TIME:GAUGE:600:0:U',
                    'RRA:AVERAGE:0.5:1:600',
                    'RRA:AVERAGE:0.5:6:700',
                    'RRA:AVERAGE:0.5:24:775',
                    'RRA:AVERAGE:0.5:288:797',
                    'RRA:MAX:0.5:1:600',
                    'RRA:MAX:0.5:6:700',
                    'RRA:MAX:0.5:24:775',
                    'RRA:MAX:0.5:444:797',
                    'RRA:MIN:0.5:1:600',
                    'RRA:MIN:0.5:6:700',
                    'RRA:MIN:0.5:24:775',
                    'RRA:MIN:0.5:444:797')
            if rrd_time:
                logger.error(rrdtool.error())

            rrd_download = rrdtool.create(RRDPATH+'/'+str(domain)+'/'+str(id)+ \
                    '_download.rrd','--step','300','--start',cur_time,
                    'DS:SPEED_DOWNLOAD:GAUGE:600:0:U',
                    'RRA:AVERAGE:0.5:1:600',
                    'RRA:AVERAGE:0.5:6:700',
                    'RRA:AVERAGE:0.5:24:775',
                    'RRA:AVERAGE:0.5:288:797',
                    'RRA:MAX:0.5:1:600',
                    'RRA:MAX:0.5:6:700',
                    'RRA:MAX:0.5:24:775',
                    'RRA:MAX:0.5:444:797',
                    'RRA:MIN:0.5:1:600',
                    'RRA:MIN:0.5:6:700',
                    'RRA:MIN:0.5:24:775',
                    'RRA:MIN:0.5:444:797')
            if rrd_download:
                logger.error(rrdtool.error())

            rrd_unavailable = rrdtool.create(RRDPATH+'/'+str(domain)+'/'+str(id)+'_unavailable.rrd','--step','300','--start',cur_time, \
                    'DS:UNAVAILABLE:GAUGE:600:0:U',
                    'RRA:AVERAGE:0.5:1:600',
                    'RRA:AVERAGE:0.5:6:700',
                    'RRA:AVERAGE:0.5:24:775',
                    'RRA:AVERAGE:0.5:288:797',
                    'RRA:MAX:0.5:1:600',
                    'RRA:MAX:0.5:6:700',
                    'RRA:MAX:0.5:24:775',
                    'RRA:MAX:0.5:444:797',
                    'RRA:MIN:0.5:1:600',
                    'RRA:MIN:0.5:6:700',
                    'RRA:MIN:0.5:24:775',
                    'RRA:MIN:0.5:444:797')
            if rrd_unavailable:
                logger.error(rrdtool.error())

            for root, dirs, files in os.walk(RRDPATH+'/'+str(domain)):
                for fiille in files:
                    logger.info(os.path.join(root, fiille))


        except Exception, e:
            logger.error('create rrd error!'+str(e))
