# coding:utf-8

from __future__ import division
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import Q
from publicclass import GetURLdomain, create_rrd, Graphrrd_normal, Graphrrd_custom, time2stamp
from base.yw_conf import pages, my_render, ServerError
from base.config import *
from yw_monitor.models import Hostinfo, MonitorData, MONITOR_NODE, MONITOR_IDC
from yw_business.models import BusinessGroup, Business, Module, ModuleDetail
MONITOR_NODE_DIC = {1: '陕西', 2: '天津', 3: '上海', 4: '广东', 5: '香港', 6:'四川', 7:'浙江'}
MONITOR_IDC_DIC = {1: '电信', 2: '联通', 3: '移动'}
from updaterrd import UpdateRRD
from celery.schedules import crontab
from celery.task import periodic_task
import time
import os
import rrdtool
import json
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import HTMLParser
from config import *
from common.log import logger


def monitor_list(request):
    header_title, path1, path2 = "监控管理", "公网监控", "查看监控"
    monitor_nodes = MONITOR_NODE
    monitor_idcs = MONITOR_IDC
    host_list = Hostinfo.objects.all()
    businessgroups = BusinessGroup.objects.all()
    business_group_name = request.GET.get('businessgroup_name')
    business_group_name_id = BusinessGroup.objects.filter(Bs1Name=business_group_name).values('Bs1Id')
    businesses = Business.objects.filter(BusinessGroup_id=business_group_name_id)
    business_name = request.GET.get('business_name')
    business_name_id = Business.objects.filter(Bs2Name=business_name).filter(BusinessGroup_id=business_group_name_id).values('Bs2Id')
    modules = Module.objects.filter(Business_id=business_name_id)
    module_name = request.GET.get('module_name')
    monitor_node = request.GET.get('monitor_node', '')
    monitor_idc = request.GET.get('monitor_idc', '')
    keyword = request.GET.get('keyword', '')
    monitor_name = request.GET.get('monitor_name', '')

    if business_group_name:
        host_list = host_list.filter(BusinessGroup=business_group_name)
    if business_name:
        host_list = host_list.filter(Business=business_name)
    if module_name:
        host_list = host_list.filter(Module=module_name)
    if monitor_name:
        host_list = host_list.filter(APPName=monitor_name)
    if monitor_node:
        host_list = host_list.filter(NODE=monitor_node)
    if monitor_idc:
        host_list = host_list.filter(IDC=monitor_idc)
    if keyword:
        host_list = host_list.filter(Q(APPName__contains=keyword) | Q(URL__contains=keyword) | Q(Alarmtype__contains=keyword) | Q(Alarmconditions__contains=keyword))

    host_list, p, hosts, page_range, current_page, show_first, show_end = pages(host_list, request)

    return my_render('yw_monitor/monitor_list.html', locals(), request)


def monitor_detail(request, offset):
    header_title, path1, path2 = "监控管理", "公网监控", "监控详情"

    html_parser = HTMLParser.HTMLParser()
    monitor_data_id = request.GET.get('id')
    starttime = request.GET.get('start')
    endtime = request.GET.get('end')

    if monitor_data_id:
        if offset == 'pic':
            if not starttime or starttime == "":
                Hostinforow = Hostinfo.objects.get(ID=monitor_data_id)
                StartTime = int(str(time.time()).split('.')[0])-86400*3
                EndTime = int(str(time.time()).split('.')[0])
                UserFind = "0"
                Graphrrd_normal(Hostinforow.ID, Hostinforow.URL, Hostinforow.APPName)
                for root, dirs, files in os.walk(RRDPATH+'/'+GetURLdomain(Hostinforow.URL)):
                    for fiille in files:
                        logger.info(os.path.join(root, fiille))
            else:
                StartTime = time2stamp(html_parser.unescape(starttime).replace(u'\xa0', u' ').encode('utf-8'))
                EndTime = time2stamp(html_parser.unescape(endtime).replace(u'\xa0', u' ').encode('utf-8'))
                monitor_data_id = request.GET.get('id')
                Hostinforow = Hostinfo.objects.get(ID=monitor_data_id)
                UserFind = "1"
                try:
                    Graphrrd_custom(Hostinforow.ID, StartTime, EndTime, Hostinforow.URL, Hostinforow.APPName)
                except ServerError, e:
                    logger.error(u"图型绘制失败！"+str(e))

            return my_render('yw_monitor/monitor_detail_pic.html', locals(), request)

        elif offset == 'list':
            if not starttime or starttime == "":
                monitor_data_list = MonitorData.objects.filter(FID=monitor_data_id).order_by("-DATETIME")[:60]
                Hostinforow = Hostinfo.objects.get(ID=monitor_data_id)
                for root, dirs, files in os.walk(PNGPATH+'/'+GetURLdomain(Hostinforow.URL)):
                    for fiille in files:
                        logger.info(os.path.join(root, fiille))
            else:
                StartTime = time2stamp(html_parser.unescape(starttime).replace(u'\xa0', u' ').encode('utf-8'))
                EndTime = time2stamp(html_parser.unescape(endtime).replace(u'\xa0', u' ').encode('utf-8'))
                monitor_data_id = request.GET.get('id')
                monitor_data_list = MonitorData.objects.filter(FID=monitor_data_id, DATETIME__gte=StartTime, DATETIME__lte=EndTime).order_by("-DATETIME")

            monitor_data_list_values = monitor_data_list.values()
            Hostinforow = Hostinfo.objects.get(ID=monitor_data_id)
            monitor_data_list, p, contacts, page_range, current_page, show_first, show_end = pages(monitor_data_list, request)

            return my_render('yw_monitor/monitor_detail_list.html', locals(), request)
    else:
        if offset == 'pic':
            return my_render('yw_monitor/monitor_detail_pic.html', locals(), request)
        elif offset == 'list':
            return my_render('yw_monitor/monitor_detail_list.html', locals(), request)


def picture(request, picture_name):
    monitor_data_id = request.GET.get('id')
    Hostinforow = Hostinfo.objects.get(ID=monitor_data_id)
    pic_path = os.path.join(PNGPATH, GetURLdomain(Hostinforow.URL), picture_name)
    image_data = open(pic_path).read()
    return HttpResponse(image_data, content_type='image/png')


def monitor_add(request):
    header_title, path1, path2 = "监控管理", "公网监控", "添加监控"
    monitor_nodes = MONITOR_NODE
    monitor_idcs = MONITOR_IDC
    businessgroups = BusinessGroup.objects.all()
    business_group_name = request.GET.get('businessgroup_name')
    business_group_name_id = BusinessGroup.objects.filter(Bs1Name=business_group_name).values('Bs1Id')
    businesses = Business.objects.filter(BusinessGroup_id=business_group_name_id)
    business_name = request.GET.get('business_name')
    business_name_id = Business.objects.filter(Bs2Name=business_name).filter(BusinessGroup_id=business_group_name_id).values('Bs2Id')
    modules = Module.objects.filter(Business_id=business_name_id)
    module_name = request.GET.get('module_name')
    module_name_id = Module.objects.filter(Business_id=business_name_id).filter(Bs3Name=module_name).values('Bs3Id')

    if request.method == 'POST':
        APPName = request.POST.get('monitor_name')
        APPName_full = str(business_group_name)+'-'+str(business_name)+'-'+str(module_name)+'-'+str(APPName)
        URL = request.POST.get('url')
        IDC = request.POST.getlist('monitor_idcs', [])
        NODE = request.POST.getlist('monitor_node', [])
        Alarmtype = request.POST.get('Alarmtype')
        status = request.POST.get('status')
        responsechar = request.POST.get('comment')
        POST = request.POST.get('post')
        try:
            monitor_person = ModuleDetail.objects.values('main_handler', 'relate_handler').get(cmdb_node_id=module_name_id)
        except:
            monitor_person = ''
        if monitor_person:
            a, b = [], []
            for key, value in monitor_person.items():
                a.append(value)
            for i in a:
                b.extend(i.split(';'))
            b = [i.encode('utf-8') for i in b]
            alarm_person = list(set(b))
            alarm_person = ",".join(alarm_person)

        if status:
            Alarmconditions = "200"
        elif responsechar:
            Alarmconditions = responsechar

        try:
            for _node in NODE:
                for _idc in IDC:
                    if _node == u'5':
                        _idc = u'1'
                        host = Hostinfo.objects.filter(APPName=APPName_full).filter(URL=URL).filter(IDC=_idc).filter(NODE=_node)
                        if host:
                            pass
                        else:
                            p = Hostinfo(BusinessGroup=business_group_name, Business=business_name, Module=module_name, APPName=APPName_full, Alarm_Person=alarm_person, URL=URL, IDC=_idc, NODE=_node, Alarmtype=Alarmtype, Alarmconditions=Alarmconditions, POST=POST)
                            p.save()
                            break
                    elif _node == u'1':
                        _idc = u'2'
                        host = Hostinfo.objects.filter(APPName=APPName_full).filter(URL=URL).filter(IDC=_idc).filter(NODE=_node)
                        if host:
                            pass
                        else:
                            p = Hostinfo(BusinessGroup=business_group_name, Business=business_name, Module=module_name, APPName=APPName_full, Alarm_Person=alarm_person, URL=URL, IDC=_idc, NODE=_node, Alarmtype=Alarmtype, Alarmconditions=Alarmconditions, POST=POST)
                            p.save()
                            break
                    elif _node == u'7':
                        _idc = u'1'
                        host = Hostinfo.objects.filter(APPName=APPName_full).filter(URL=URL).filter(IDC=_idc).filter(NODE=_node)
                        if host:
                            pass
                        else:
                            p = Hostinfo(BusinessGroup=business_group_name, Business=business_name, Module=module_name, APPName=APPName_full, Alarm_Person=alarm_person, URL=URL, IDC=_idc, NODE=_node, Alarmtype=Alarmtype, Alarmconditions=Alarmconditions, POST=POST)
                            p.save()
                            break
                    elif _node == u'6' and _idc == u'3':
                        break
                    host = Hostinfo.objects.filter(APPName=APPName_full).filter(URL=URL).filter(IDC=_idc).filter(NODE=_node)
                    if host:
                        pass
                    else:
                        p = Hostinfo(BusinessGroup=business_group_name, Business=business_name, Module=module_name, APPName=APPName_full, Alarm_Person=alarm_person, URL=URL, IDC=_idc, NODE=_node, Alarmtype=Alarmtype, Alarmconditions=Alarmconditions, POST=POST)
                        p.save()
        except ServerError, e:
            error = e

        try:
            if not os.path.isdir(RRDPATH+'/'+GetURLdomain(URL)):
                os.makedirs(RRDPATH+'/'+GetURLdomain(URL))
                logger.info(RRDPATH+'/'+GetURLdomain(URL))
            if not os.path.isdir(PNGPATH+'/'+GetURLdomain(URL)):
                os.makedirs(PNGPATH+'/'+GetURLdomain(URL))
                logger.info(PNGPATH+'/'+GetURLdomain(URL))
        except ServerError, e:
            return HttpResponse(u"目录创建失败！"+str(e))

        try:
            create_rrd(str(URL))
            return HttpResponseRedirect(reverse('monitor_list'))
        except ServerError, e:
            return HttpResponse(u"目录RRD文件失败！"+str(e))

    return my_render('yw_monitor/monitor_add.html', locals(), request)


def monitor_edit(request):
    header_title, path1, path2 = "监控管理", "公网监控", "编辑监控"

    host_id = request.GET.get('id')
    host = Hostinfo.objects.get(ID=host_id)
    APPName = host.APPName.split('-')[-1]
    businessgroups = BusinessGroup.objects.all()
    monitor_nodes = MONITOR_NODE
    monitor_idcs = MONITOR_IDC
    alarmtype_role = {'mobile+email': u'短信+邮件', 'email': u'邮件'}
    business_group_name = request.GET.get('businessgroup_name')
    business_group_name_id = BusinessGroup.objects.filter(Bs1Name=business_group_name).values('Bs1Id')
    businessess = Business.objects.filter(BusinessGroup_id=business_group_name_id)
    business_name = request.GET.get('business_name')
    business_name_id = Business.objects.filter(Bs2Name=business_name).values('Bs2Id')
    moduless = Module.objects.filter(Business_id=business_name_id)
    module_name = request.GET.get('module_name')
    module_name_id = Module.objects.filter(Business_id=business_name_id).filter(Bs3Name=module_name).values('Bs3Id')

    if request.method == 'POST' and host_id:
        APPName = request.POST.get('monitor_name')
        business_group_name = request.GET.get('businessgroup_name')
        business_name = request.GET.get('business_name')
        module_name = request.GET.get('module_name')
        APPName_full = str(business_group_name)+'-'+str(business_name)+'-'+str(module_name)+'-'+str(APPName)
        URL = request.POST.get('url')
        IDC = request.POST.get('monitor_idcs')
        NODE = request.POST.get('monitor_node')
        POST = request.POST.get('post')
        Alarmtype = request.POST.get('role')
        status = request.POST.get('status')
        responsechar = request.POST.get('comment')
        try:
            monitor_person = ModuleDetail.objects.values('main_handler', 'relate_handler').get(cmdb_node_id=module_name_id)
        except:
            monitor_person = ''
        if monitor_person:
            a, b = [], []
            for key, value in monitor_person.items():
                a.append(value)
            for i in a:
                b.extend(i.split(';'))
            b = [i.encode('utf-8') for i in b]
            alarm_person = list(set(b))
            alarm_person = ",".join(alarm_person)

        if status:
            Alarmconditions = "200"
        elif responsechar:
            Alarmconditions = responsechar

        try:
            Hostinfo.objects.filter(ID=host_id).update(BusinessGroup=business_group_name, Business=business_name, Module=module_name, APPName=APPName_full, Alarm_Person=alarm_person, URL=URL, IDC=IDC, NODE=NODE, Alarmtype=Alarmtype, Alarmconditions=Alarmconditions, POST=POST)
            return HttpResponseRedirect(reverse('monitor_list'))
        except ServerError, e:
            error = e
    return my_render('yw_monitor/monitor_edit.html', locals(), request)


def monitor_delete(request):
    host_ids = request.GET.get('id')
    host_id_list = host_ids.split(',')
    for host_id in host_id_list:
        Hostinfo.objects.filter(ID=host_id).delete()

    return HttpResponse(u"删除成功")


def monitor_group_list(request):
    header_title, path1, path2 = "监控管理", "公网监控", "查看监控组"

    host_list = Hostinfo.objects.values('APPName', 'URL').distinct()
    monitor_groups_list = []
    for i in host_list:
        i['monitor_count'] = Hostinfo.objects.filter(APPName=i.get('APPName')).count()
        monitor_groups_list.append(i)

    monitor_groups_list, p, monitor_groups, page_range, current_page, show_first, show_end = pages(monitor_groups_list, request)

    return my_render('yw_monitor/monitor_group_list.html', locals(), request)


def monitor_group_detail(request):
    header_title, path1, path2 = "监控管理", "公网监控", "可用性详情"

    monitor_name = request.GET.get('monitor_name', '')
    Hostinforow = monitor_name
    host_list = Hostinfo.objects.filter(APPName=monitor_name).values('ID', 'NODE', 'IDC')
    dxzd, ltzd, ydzd = [], [], []
    cd_dx, xa_lt, hz_dx, cd_lt, tj_dx, tj_lt, tj_yd, sh_dx, sh_lt, sh_yd, sz_dx, sz_lt, sz_yd, xg_dx = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

    for i in host_list:
        a = MonitorData.objects.filter(FID=i.get('ID')).values('HTTP_CODE').order_by("-DATETIME")[:60]
        b = []
        for ii in a:
            b.append(ii.get('HTTP_CODE'))
        availability = str(int(round(b.count(u'200')/60*100)))
        print availability
        if i.get('NODE') == 6 and i.get('IDC') == 1:
            cd_dx['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            cd_dx['value'] = availability
            dxzd.append(cd_dx)
        elif i.get('NODE') == 1 and i.get('IDC') == 2:
            xa_lt['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            xa_lt['value'] = availability
            ltzd.append(xa_lt)
        elif i.get('NODE') == 7 and i.get('IDC') == 1:
            hz_dx['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            hz_dx['value'] = availability
            dxzd.append(hz_dx)
        elif i.get('NODE') == 6 and i.get('IDC') == 2:
            cd_lt['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            cd_lt['value'] = availability
            ltzd.append(cd_lt)
        elif i.get('NODE') == 2 and i.get('IDC') == 1:
            tj_dx['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            tj_dx['value'] = availability
            dxzd.append(tj_dx)
        elif i.get('NODE') == 2 and i.get('IDC') == 2:
            tj_lt['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            tj_lt['value'] = availability
            ltzd.append(tj_lt)
        elif i.get('NODE') == 2 and i.get('IDC') == 3:
            tj_yd['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            tj_yd['value'] = availability
            ydzd.append(tj_yd)
        elif i.get('NODE') == 3 and i.get('IDC') == 1:
            sh_dx['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            sh_dx['value'] = availability
            dxzd.append(sh_dx)
        elif i.get('NODE') == 3 and i.get('IDC') == 2:
            sh_lt['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            sh_lt['value'] = availability
            ltzd.append(sh_lt)
        elif i.get('NODE') == 3 and i.get('IDC') == 3:
            sh_yd['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            sh_yd['value'] = availability
            ydzd.append(sh_yd)
        elif i.get('NODE') == 4 and i.get('IDC') == 1:
            sz_dx['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            sz_dx['value'] = availability
            dxzd.append(sz_dx)
        elif i.get('NODE') == 4 and i.get('IDC') == 2:
            sz_lt['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            sz_lt['value'] = availability
            ltzd.append(sz_lt)
        elif i.get('NODE') == 4 and i.get('IDC') == 3:
            sz_yd['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            sz_yd['value'] = availability
            ydzd.append(sz_yd)
        elif i.get('NODE') == 5 and i.get('IDC') == 1:
            xg_dx['name'] = MONITOR_NODE_DIC[i.get('NODE')]
            xg_dx['value'] = availability
            dxzd.append(xg_dx)

    dxzd = json.dumps(dxzd)
    ltzd = json.dumps(ltzd)
    ydzd = json.dumps(ydzd)

    return my_render('yw_monitor/monitor_group_detail.html', locals(), request)


@periodic_task(run_every=crontab(minute='0', hour='*/2', day_of_week='*'))
def updaterrd():
    app = UpdateRRD()
    app.getNewdata()
