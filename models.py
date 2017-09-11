# coding:utf-8

from django.db import models

MONITOR_NODE = (
    (1, u"西安"),
    (2, u"天津"),
    (3, u"上海"),
    (4, u"深圳"),
    (5, u"香港"),
    (6, u"成都"),
    (7, u"杭州")
    )

MONITOR_IDC = (
    (1, u"电信"),
    (2, u"联通"),
    (3, u"移动")
    )


class Hostinfo(models.Model):
    ID = models.AutoField(primary_key=True, max_length=6)
    BusinessGroup = models.CharField(max_length=128, blank=True, default='', null=True)
    Business = models.CharField(max_length=128, blank=True, default='', null=True)
    Module = models.CharField(max_length=128, blank=True, default='', null=True)
    Alarm_Person = models.CharField(max_length=1000, null=True, blank=True, default='')
    APPName = models.CharField(max_length=128, blank=True, default='', null=True)
    URL = models.CharField(max_length=128, blank=True, default='', null=True)
    POST = models.CharField(max_length=1000, null=True, blank=True, default='')
    IDC = models.IntegerField(choices=MONITOR_IDC, blank=True, null=True, default=1)
    NODE = models.IntegerField(choices=MONITOR_NODE, blank=True, null=True, default=1)
    Alarmtype = models.CharField(max_length=16, blank=True, default='', null=True)
    Alarmconditions = models.CharField(max_length=64, blank=True, default='', null=True)

    def __unicode__(self):
        return self.APPName


class MonitorData(models.Model):
    ID = models.AutoField(primary_key=True, max_length=6)
    FID = models.SmallIntegerField()
    HOST = models.ForeignKey(Hostinfo)
    NAMELOOKUP_TIME = models.FloatField()
    CONNECT_TIME = models.FloatField()
    PRETRANSFER_TIME = models.FloatField()
    STARTTRANSFER_TIME = models.FloatField()
    TOTAL_TIME = models.FloatField()
    HTTP_CODE = models.CharField(max_length=100)
    SIZE_DOWNLOAD = models.FloatField()
    HEADER_SIZE = models.SmallIntegerField()
    REQUEST_SIZE = models.SmallIntegerField()
    CONTENT_LENGTH_DOWNLOAD = models.FloatField()
    SPEED_DOWNLOAD = models.FloatField()
    DATETIME = models.IntegerField()
    MARK = models.CharField(max_length=8, blank=True, default='', null=True)

    def __unicode__(self):
        return self.MARK
