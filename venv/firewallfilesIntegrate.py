#!/usr/bin/python
# -*- coding:utf-8 -*-

import re
import shutil
import sys, os
import datetime
import gzip
import tarfile

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
proxy_logfile = "/tmp/proxy_loop.log"
tmp_firewall_file = "/tmp/firewall"


def readFirewallIplist(filepath):
    if not os.path.exists(filepath):
        return []
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


def un_tar(tar_path, target_path):
    try:
        tar = tarfile.open(tar_path, "r:gz")
        file_names = tar.getnames()
        for file_name in file_names:
            tar.extract(file_name, target_path)
        tar.close()
    except Exception, e:
        raise Exception, e


def de_tar(filepath):
    tar = tarfile.open(filepath + ".gz", "w:gz")
    tar.add(filepath)
    tar.close()


if __name__ == "__main__":

    dir_files = {}
    for (root, dirs, files) in os.walk(sys.argv[1]):
        for filename in files:
            if filename[-6:] == "tar.gz":
                print os.path.join(root, filename)
                dir_files[root[-8:]].append(os.path.join(root, filename))
        for dirc in dirs:
            if len(dirc) == 8:
                print os.path.join(root, dirc)
                dir_files[dirc] = []


    resultPath = sys.argv[1] + "/result"
    if not os.path.exists(resultPath):
        os.makedirs(resultPath)

    for key in dir_files:
        iplist = []
        pathr = ""
        for f in dir_files[key]:
            #解压，返回iplist
            pathr = os.path.dirname(f) + ("/untmp/%s" % os.path.basename(f))
            un_tar(f, pathr)
            iplist += readFirewallIplist(pathr + "/etc/config/firewall")

        new_firewall = list(set(iplist))

        day_firewall = resultPath + "/" + key + "_firewall"
        writehead(day_firewall, len(new_firewall) + 5)
        for ips in new_firewall:
            ip = ips.split(':')[0]
            port = ips.split(':')[1]
            writeIP(day_firewall, ip, port)
        writeend(day_firewall)
        de_tar(day_firewall)
        os.remove(day_firewall)
        print "make ip:" + day_firewall
        if os.path.exists(os.path.dirname(pathr)):
            shutil.rmtree(os.path.dirname(pathr))
