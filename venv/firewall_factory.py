#
# -*- coding:utf-8 -*-
# File: sync_socket_client.py
#

import sys
import re
import urllib2
import json
import os
import sys
from IPInfo import *
import datetime

import sys   #reload()之前必须要引入模块
reload(sys)
sys.setdefaultencoding('utf-8')

HEAD = '''
#ver %s
#rule count %s

config rule
	option name 'Allow-DHCP-Renew'
	option src 'wan'
	option proto 'udp'
	option dest_port '68'
	option target 'ACCEPT'
	option family 'ipv4'

config rule
	option name 'Allow-Ping'
	option src 'wan'
	option proto 'icmp'
	option icmp_type 'echo-request'
	option family 'ipv4'
	option target 'ACCEPT'

config rule
	option target 'ACCEPT'
    option src 'lan'
	option dest 'wan'
	option name 'allow dns'
	option dest_port '53'

config rule
	option target 'ACCEPT'
	option dest 'wan'
	option name 'allow yxt'
	option proto 'tcp'
	option dest_ip '202.108.133.234'
	
config rule
	option target 'ACCEPT'
	option dest 'wan'
	option name 'allow wxpro'
	option proto 'tcp'
	option dest_ip '192.168.0.1'
	option dest_port '80'
'''
IPmodel = """
#%s
config rule
	option target 'ACCEPT'
	option dest 'wan'
	option name 'allow wx'
	option proto 'tcp'
	option dest_ip '%s'
	option dest_port '%s'
"""
END = '''
config rule
	option src 'lan'
	option dest 'wan'
	option target 'REJECT'

config defaults
	option syn_flood '1'
	option input 'ACCEPT'
	option output 'ACCEPT'
	option forward 'REJECT'

config zone
	option name 'lan'
	list network 'lan'
	option input 'ACCEPT'
	option output 'ACCEPT'
	option forward 'ACCEPT'

config zone
	option name 'wan'
	list network 'wan'
	option input 'REJECT'
	option output 'REJECT'
	option forward 'REJECT'
	option masq '1'
	option mtu_fix '1'

config forwarding
	option src 'lan'
	option dest 'wan'

config include 'firewalluser'
	option path '/etc/firewall.user'
	option reload '1'
'''


TIME = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
FIREWALL_ALL_FILENAME = 'firewall_ALL_%s' % TIME
FIREWALL_CN_FILENAME = 'firewall_CN_%s' % TIME
CN_ShengName = ['北京','天津','上海','重庆','河北','山西','辽宁','吉林','黑龙','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','海南','四川','贵州','云南','陕西','甘肃','青海','台湾','内蒙','广西','西藏','宁夏','新疆','香港','澳门']

def readFirewallIplist(filepath):
    with open(filepath, 'r') as f:
        fr = f.read()
    it = re.findall(r"config rule.+?'allow wx'.+?option dest_ip '(.+?)'.+?option dest_port '(.+?)'",
                    fr, flags=re.DOTALL)
    ipportlist = []
    iplist = []
    for match in it:
        iplist.append(match[0])
        ipportlist.append('%s:%s' % (match[0], match[1]))
    return ipportlist


def readProxyloopIplist(filepath):
    with open(filepath, 'r') as f:
        fr = f.read()
    it = re.findall(r".*ERROR \[w\](.+?):(.+)", fr)
    ipportlist = []
    iplist = []
    for match in it:
        iplist.append(match[0])
        ipportlist.append('%s:%s' % (match[0], match[1]))
    return ipportlist

def getIPtaobao(ip):
    try:
        url = "http://ip.taobao.com/service/getIpInfo.php?ip=%s" % ip

        req = urllib2.Request(url=url)
        res = urllib2.urlopen(req)
        res = res.read()
        resjson = json.loads(res)
        if resjson['code'] != 0:
            return 'unkonw'

        country = '%s %s %s' % (resjson['data']['country'], resjson['data']['region'], resjson['data']['city'])
        country_id = resjson['data']['country_id']
    except:
        country_id = 'unkonw'
        country = 'unkonw'
    return country_id, country

def getIPipcn(ip):
    try:
        header_dict = {
            'User-Agent': 'curl/7.54.0',
            'Accept': '*/*'
        }

        url = "http://ip.cn/index.php?ip=%s" % ip

        req = urllib2.Request(url=url, headers=header_dict)
        res = urllib2.urlopen(req)
        fr = res.read()

        country_id = ''
        country = str(fr.strip())
    except:
        country_id = 'unkonw'
        country = 'unkonw'
    return country_id, country

def getIPqqwry(ip):
    try:
        i = IPInfo('qqwry.dat')
        c, a = i.getIPAddr(ip)
        #print len(c)
        b = c[:6]
        if b in CN_ShengName:
            return 'CN', '%s %s' % (c, a)
        else:
            return 'OTHER', '%s %s' % (c, a)
    except:
        return "unkonw","unkonw"


def writeIP(filename, country, ip, port):
    str = IPmodel % (country, ip, port)
    #str = IPmodel % (ip, port)
    with open(filename, 'a') as f:
        f.write(str.encode('utf-8'))

def write(countryid, country, ip, port):
    if country_id in ['CN', 'HK', 'unkonw']:
        writeIP(FIREWALL_CN_FILENAME, country, ip, port)
    writeIP(FIREWALL_ALL_FILENAME, country, ip, port)
    if country_id == 'OTHER':
        print '%s:%s %s' % (ip, port, country)

def writehead(ipcount):
    head = HEAD % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ipcount)
    with open(FIREWALL_CN_FILENAME, 'w') as f:
        f.write(head.encode('utf-8'))
    with open(FIREWALL_ALL_FILENAME, 'w') as f:
        f.write(head.encode('utf-8'))
def writeend():
    with open(FIREWALL_CN_FILENAME, 'a') as f:
        f.write(END.encode('utf-8'))
    with open(FIREWALL_ALL_FILENAME, 'a') as f:
        f.write(END.encode('utf-8'))

if __name__ == "__main__":
    old_firewall = sys.argv[1]
    proxy_loop_logfile = sys.argv[2]
    # if os.path.exists('firewall_CN'):
    #     os.remove('firewall_CN')
    # if os.path.exists('firewall_ALL'):
    #     os.remove('firewall_ALL')


    firewall_iplist = readFirewallIplist(old_firewall)
    proxy_loop_logfile_iplist = readProxyloopIplist(proxy_loop_logfile)

    print 'firewal ip count: %s\tproxy_loop ip count:%s' % (len(firewall_iplist), len(proxy_loop_logfile_iplist))
    iplist = firewall_iplist + proxy_loop_logfile_iplist
    print 'iplist count: %s' % len(iplist)
    iplist = set(iplist)
    print 'set(iplist) count: %s' % len(iplist)

    writehead(len(iplist) + 5) #5个头规则
    oldip = ''
    country_id = 'CN'
    country = ''
    ipcount = len(iplist)
    i = 1
    for ips in set(iplist):
        ip = ips.split(':')[0]
        port = ips.split(':')[1]
        if ip != oldip:
            country_id, country = getIPqqwry(ip)
        oldip = ip
        write(country_id, country, ip, port)
        print '%s/%s' % (i, ipcount)
        i = i + 1
    writeend()
    cmd = 'cp ' + FIREWALL_CN_FILENAME + ' firewall'
    os.system(cmd)
    print 'make over'





