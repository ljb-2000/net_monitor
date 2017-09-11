#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import os, sys
import time
import sys
import pycurl
import rrdtool
import string
import MySQLdb
from config import *
from common.log import logger


class UpdateRRD(object):
    def __init__(self):

        try:
            self.conn = MySQLdb.Connection(DBHOST, DBUSER, DBPASSWORD, DBNAME, DBPORT)
            self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
        except Exception, e:
            logger.error('connect database error!'+str(e))

        self.rrdfiletype=['time', 'download', 'unavailable']

    def __del__(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception, e:
            logger.debug('__del__ object error!'+str(e))

    def updateRRD(self, rowobj):
        if str(rowobj["HTTP_CODE"]) == "200":
            unavailablevalue = 0
        else:
            unavailablevalue = 1
        FID = rowobj["FID"]

        time_rrdpath = RRDPATH+'/'+str(self.getURL(FID))+'/'+str(FID)+'_'+str(self.rrdfiletype[0])+'.rrd'
        download_rrdpath = RRDPATH+'/'+str(self.getURL(FID))+'/'+str(FID)+'_'+str(self.rrdfiletype[1])+'.rrd'
        unavailable_rrdpath = RRDPATH+'/'+str(self.getURL(FID))+'/'+str(FID)+'_'+str(self.rrdfiletype[2])+'.rrd'

        try:
            rrdtool.updatev(time_rrdpath, '%s:%s:%s:%s:%s:%s' % (str(rowobj["DATETIME"]), str(rowobj["NAMELOOKUP_TIME"]), str(rowobj["CONNECT_TIME"]), str(rowobj["PRETRANSFER_TIME"]), str(rowobj["STARTTRANSFER_TIME"]), str(rowobj["TOTAL_TIME"])))
            rrdtool.updatev(download_rrdpath, '%s:%s' % (str(rowobj["DATETIME"]), str(rowobj["SPEED_DOWNLOAD"])))
            rrdtool.updatev(unavailable_rrdpath, '%s:%s' % (str(rowobj["DATETIME"]), str(unavailablevalue)))
            logger.debug(rrdtool.last(time_rrdpath))
            self.setMARK(rowobj["ID"])
        except Exception, e:
            logger.error('Update rrd error:'+str(e))

    def setMARK(self, _id):
        try:
            self.cursor.execute("update yw_monitor_monitordata set MARK='1' where ID='%s'"%(_id))
            self.conn.commit()
        except Exception, e:
            logger.error('SetMark datebase  error:'+str(e))

    def getNewdata(self):
        try:
            self.cursor.execute("select ID, FID, NAMELOOKUP_TIME, CONNECT_TIME, PRETRANSFER_TIME, STARTTRANSFER_TIME, TOTAL_TIME, HTTP_CODE, SPEED_DOWNLOAD, DATETIME from yw_monitor_monitordata where MARK='0'")
            for row in self.cursor.fetchall():
                self.updateRRD(row)
        except Exception, e:
            logger.error('Get new database  error:'+str(e))

    def GetURLdomain(self, url):
        xurl = ""
        if url[:7] == "http://":
            xurl = url[7:]
        elif url[:8] == "https://":
            xurl = url[8:]
        else:
            xurl = url
        return string.split(xurl, '/')[0]

    def getURL(self, _id):
        try:
            self.cursor.execute("select URL from yw_monitor_hostinfo where ID='%s'"%(_id))
            return self.GetURLdomain(self.cursor.fetchall()[0]["URL"])
        except Exception, e:
            logger.error('Get FID URL  error:'+str(e))


