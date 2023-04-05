
import socket
from scapy.all import *


def seperate_ip(self, ip: str) -> tuple:
    ip = str(ip).split('.')
    host_part = ip[-1]
    ip_part = ".".join(ip[:3]) + "."
    return ip_part, host_part


def get_resolution_name(ip: str):
    try:
        name, a, b = socket.gethostbyaddr(ip)
        return ip, name
    except socket.herror:
        return ip, None


def fast_scan() -> dict:
    adresses = []
    address = {}
    my_ip_address = IP(dst="0.0.0.0").src
    ip_part, host_part = seperate_ip(my_ip_address)

    for i in range(0, 255):
        ip_value = ip_part + str(i)
        print(ip_value, "---------------->")
        rep, non_rep = sr(IP(dst=ip_value) / ICMP(), timeout=10)
        for elt in rep:
            if elt[1].type == 0:
                adresses.append(elt[1].src)
                print(elt[1].src + ' a renvoye un reply')

            for host in adresses:
                try:
                    name, a, b = socket.gethostbyaddr(host)
                    address[host] = name
                except:
                    name = "Not Found"
                print("|" + host + " |" + name)

        return address
