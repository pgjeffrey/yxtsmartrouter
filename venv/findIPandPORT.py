#
# -*- coding:utf-8 -*-
# File: sync_socket_client.py
#

import sys,  re


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


if __name__ == "__main__":
    firewallFile = sys.argv[1]
    out_file = sys.argv[2]
    iplist = readFirewallIplist(firewallFile)

    with open(out_file, 'w') as f:
        for ip in iplist:
            f.writelines(ip + "\r\n")
