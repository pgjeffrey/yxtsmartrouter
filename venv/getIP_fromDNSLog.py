#!/usr/bin/python
# -*- coding:utf-8 -*-


import re
import sys, os
import datetime

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
ISDEBUG = False
firewall_file = "/etc/config/firewall"
dns_logfile = "/tmp/dnsmasq.log"
tmp_firewall_file = "/tmp/firewall"


def isip(str):
    '''
    正则匹配方法
    判断一个字符串是否是合法IP地址
    '''
    compile_ip=re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
    if compile_ip.match(str):
        return True
    else:
        return False

def readDNSLogIPList(filepath):
    with open(filepath, 'r') as f:
        fr = f.read()
    it = re.findall(r".*reply (.+?) is (.+)", fr)
    urliplist = []
    ipportlist = []
    iplist = []
    for match in it:
        url = match[0]
        ip = match[1]
        if isip(ip) == True:
            iplist.append(ip)
            urliplist.append('%s|%s' % (url, ip))
            for port in [80, 8080, 443]:
                ipportlist.append("%s:%s" % (ip, port))
    iplist = list(set(iplist))
    urliplist = list(set(urliplist))
    ipportlist = list(set(ipportlist))
    iplist.sort()
    urliplist.sort()
    ipportlist.sort()
    return iplist, urliplist, ipportlist

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

def writeIP(filepath, ip, port):
    str = IPmodel % ("", ip, port)
    with open(filepath, 'a') as f:
        f.write(str.encode('utf-8'))

def writehead(filepath, ipcount):
    head = HEAD % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ipcount)
    with open(filepath, 'w') as f:
        f.write(head.encode('utf-8'))

def writeend(filepath):
    with open(filepath, 'a') as f:
        f.write(END.encode('utf-8'))


if __name__ == "__main__":

    if len(sys.argv) > 1:
        if sys.argv[1] == "-debug":
            ISDEBUG = True
            firewall_file = "firewall"
            dns_logfile = "dnsmasq.log"
            tmp_firewall_file = "firewall_tmp"

    iplist, urliplist, dns_ipportlist = readDNSLogIPList(dns_logfile)
    firewall_iplist = readFirewallIplist(firewall_file)
    new_firewall = list(set(firewall_iplist + dns_ipportlist))

    print "firewall len:%d,dns_iplist len:%d, new_firewall len:%d" % (len(firewall_iplist), len(dns_ipportlist), len(new_firewall))

    if len(new_firewall) - len(firewall_iplist) >= 3*3:
        writehead(tmp_firewall_file, len(new_firewall) + 5)
        for ips in new_firewall:
            ip = ips.split(':')[0]
            port = ips.split(':')[1]
            writeIP(tmp_firewall_file, ip, port)
        writeend(tmp_firewall_file)
        if not ISDEBUG:
            cmd = "cp %s %s" % (tmp_firewall_file, firewall_file)
            os.system(cmd)
            cmd = "/etc/init.d/firewall restart"
            os.system(cmd)
        print "make over."
    else:
        print "NOT MAKE."
