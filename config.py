#!/usr/bin/env python
# coding=utf-8

import os

#BASE_DIR = '/data/BKTest_App_FilePool/yw_tocnew/bkdownload'
BASE_DIR = '/data/BK_App_FilePool/yw_tocnew/bkdownload'
BASE_DIR1 = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

RRDPATH = BASE_DIR+"/yw_monitor/rrd"
PNGPATH = BASE_DIR1+"/static/rrdtool"
MAINAPPPATH = BASE_DIR1+"/yw_monitor"

TIME_ALARM = 1
TIME_YMAX = 1
DOWN_APEED_YMAX = 8388608

DBNAME='yw_netmonitor'
DBUSER='networkmonitor'
DBPASSWORD='networkmonitor161014'
DBHOST='gamedb.netmonitor.TXWX.db'
DBPORT=10016