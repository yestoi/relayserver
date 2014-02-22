relayserver
===========

Listener to listener relay server

'''
$ nc localhost 444
--- Super Cool Relay Server v0.1 ---

Commands:
show - Show last connections
list - List scheduled relays
add - Add relay (ex. add <host> <target> <port>)
del - Delete relay(s) (ex. del <target> or del all)
clean - Clear out last connections cache

show
192.168.1.20     -- 05:55PM
192.168.1.40     -- 05:56PM

add 192.168.1.40 192.168.1.5 333

list
192.168.1.40 will be relayed to 192.168.1.5 on port 333

quit
$ ssh root@192.168.1.5
root@192.168.1.5's password: 
Last login: Sat Feb 15 02:52:32 2014 from 64.107.11.26
#
# nc -lp 333
 18:07:01 up 1 day, 10:49,  2 users,  load average: 0.23, 0.21, 0.22
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.168.1.5      Fri17   24:37m 19:58  19:58  watch -n 0.1 ne
root     pts/1    192.168.1.5      Fri22   19:20m  7:07   0.06s -bash
Linux lamp 3.2.0-4-amd64 #1 SMP Debian 3.2.51-1 x86_64 GNU/Linux
uid=0(root) gid=0(root) groups=0(root 18:07:01 up 1 day, 10:49,  2 users,  load average: 0.23, 0.21, 0.22
# ip addr show eth0 | grep inet
    inet 192.168.1.40/24 brd 192.168.1.255 scope global eth0
    inet6 fe80::5054:ff:fe01:38eb/64 scope link
'''
