#!/usr/bin/python
# -*- coding:utf-8 -*-

import ConfigParser
import itertools
import mimetools
import mimetypes
import os
import sys
import urllib2
import re

ISDEBUG = False
firewall_file = "/etc/config/firewall"
yxt_config_path = "/etc/yxt/routerconfig.ini"
firewall_gzfile = "/tmp/"

class MultiPartForm():
    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()

    def add_field(self, name, value):
        #"""添加field数据到form表单"""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, file_obj, mimetype=None):
        #"""添加文件到表单"""
        if not mimetype:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, file_obj.read()))
    def __str__(self):
        #"""拼接form报文"""
        parts = []
        part_boundary = "--%s" % self.boundary

        # 添加fields
        parts.extend(
            [part_boundary,
            'Content-Disposition: form-data; name="%s"' %name,
            '',
            value,] for name, value in self.form_fields
            )

        # 添加要上传的files
        parts.extend(
            [part_boundary,
            'Content-Disposition: form-data; name="%s"; filename="%s"' % (field_name, filename),
            'Content-Type: %s' % content_type,
            '',
            body,] for field_name, filename, content_type, body in self.files
            )

        # 压平parts添加boundary终止符
        flattened = list(itertools.chain(*parts))
        flattened.append('--%s--' % self.boundary)
        flattened.append('')
        return '\r\n'.join(flattened)


def get_dev_id_mac(nic):
    # 获取设备ID及MAC地址
    cmd = "ifconfig " + nic + " |grep -w HWaddr |awk -F \" \" \'{print $5}\'"
    tmp_mac = os.popen(cmd).read()
    mac = tmp_mac.replace(":", "-").strip("\n")
    devid = tmp_mac.replace(":", "").strip("\n")

    return devid, mac

def load_yxt_config_ini(path):
    # 读取yxt 配置文件，默认设置在 /etc/yxt目录下 ，文件名默认为 routerconfig.ini
    cf = ConfigParser.ConfigParser()
    cf.read(path)
    sections = cf.sections()
    yxt = "program:yxtconfig"

    hb_time = cf.get(yxt, "heartbeat_time")
    odr_time = cf.getint(yxt, "order_time")
    at_time = cf.get(yxt, "at_time")
    svr_url = cf.get(yxt, "server_url")
    ver_code = cf.get(yxt, "ver_code")
    on_time = cf.get(yxt, "on_time")
    retry_time = cf.get(yxt, "retry_time")

    return hb_time, odr_time, at_time, svr_url, ver_code, on_time, retry_time

if __name__ == "__main__":

    if len(sys.argv) > 1:
        if sys.argv[1] == "-debug":
            ISDEBUG = True
            firewall_file = "firewall"
            yxt_config_path = "routerconfig.ini"
            firewall_gzfile = ""
    nic = "eth0"
    devid, mac = get_dev_id_mac(nic)

    if ISDEBUG:
        devid = "00e04c6b7140"

    uploadfirename = devid + "_firewall.tar.gz"
    firewall_gzfile += uploadfirename
    cmd = "tar -zcf %s %s" % (firewall_gzfile, firewall_file)
    os.system(cmd)

    hb_time, order_time, at_time, server_url, ver_code, on_time, retry_time = load_yxt_config_ini(yxt_config_path)
    uploadurl = "http://%s/router/file/upload" % re.match("http://(.*?)/", server_url, flags=0).group(1)
    #uploadurl = "http://wifi.jzlkbj.com:8182/router/file/upload"
    form = MultiPartForm()
    form.add_file('fileContent', uploadfirename, file_obj=open(firewall_gzfile))
    request = urllib2.Request(uploadurl)
    body = str(form)
    request.add_header('Content-type', 'multipart/form-data; boundary=%s' % form.boundary)
    request.add_header('Content-length', len(body))
    request.add_header('User-Agent', 'yxtsmartrouter')
    request.add_data(body)

    print(urllib2.urlopen(request).read())
    print "uploaded."
