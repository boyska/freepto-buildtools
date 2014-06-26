from fabric.api import *


def get_my_ips():
    for iface in run('ip -o -4 addr list').split('\n'):
        ip_and_mask = iface.split()[3]
        ip, mask = ip_and_mask.split('/')
        yield (ip, mask)


def is_my_ip(test_ip):
    for my_ip, my_mask in get_my_ips():
        if test_ip == my_ip:
            return True
    return False
