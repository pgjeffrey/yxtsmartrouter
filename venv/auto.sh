#!/usr/bin/expect

set timeout -1

#spawn rm  /Users/jeffrey/.ssh/known_hosts
spawn scp root@192.168.1.1:/tmp/proxy_loop.log .
expect {
	"yes/no" {
		send "yes\n"
        exp_continue
	}
    "password" {
		send "admin\n"
		exp_continue
	}
}


spawn python firewall_factory.py firewall proxy_loop.log
expect {
	"make over" {
		send "yes\n"
        exp_continue
	}
    "password" {
		send "admin\n"
		exp_continue
	}
}


spawn scp firewall root@192.168.1.1:/etc/config/firewall
expect {
	"yes/no" {
		send "yes\n"
        exp_continue
	}
    "password" {
		send "admin\n"
		exp_continue
	}
}


spawn ssh root@192.168.1.1
expect {
	"yes/no" {
		send "yes\n"
		exp_continue
	}

    "password" {
		send "admin\n"
		exp_continue
	}
    ":~#" {
		send "/etc/init.d/firewall restart\n"
		send "exit\n"
	}
}
interact