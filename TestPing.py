import socket
import os
import sys
import struct
import time
import select
import binascii
import threading
import array

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    answer = socket.htons(answer)
    return answer


def receiveoneping(icmp_socket, sent_time, timeout):
    time_left = timeout
    while True:
        started_select = time.time()
        what_ready = select.select([icmp_socket], [], [], time_left)
        wait_time = (time.time() - started_select)
        if what_ready[0] == []:  # Timeout
            return None, None

        time_received = time.time()
        rec_packet, addr = icmp_socket.recvfrom(1024)
        icmp_header = rec_packet[20:28]
        icmp_type, code, checksum, packet_id, sequence = struct.unpack(
            "bbHHh", icmp_header
        )

        if packet_id < 0:
            return None, None

        time_left -= wait_time
        if time_left <= 0:
            return None, None

        if icmp_type == ICMP_ECHO_REPLY:
            return time_received - sent_time, addr

        time_left = timeout



def sendoneping(icmp_socket, dest_addr, packet_id):
    checksum_value = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, checksum_value, packet_id, 1)
    data = struct.pack("d", time.time())
    checksum_value = checksum(header + data)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(checksum_value), packet_id, 1)
    packet = header + data
    icmp_socket.sendto(packet, (dest_addr, 1))


def dooneping(dest_addr, timeout):
    icmp = socket.getprotobyname("icmp")
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    my_ID = os.getpid() & 0xFFFF
    sendoneping(icmp_socket, dest_addr, my_ID)
    delay, addr = receiveoneping(icmp_socket, time.time(), timeout)
    icmp_socket.close()
    return delay, addr


def ping(host, timeout=1, count=4):
    dest_addr = socket.gethostbyname(host)
    for i in range(count):
        print(f"Pinging {host} [{dest_addr}] with 32 bytes of data:")
        delay, addr = dooneping(dest_addr, timeout)
        if delay is None:
            print("Request timed out.")
        else:
            delay = round(delay * 1000, 2)
            print(f"Reply from {addr}: bytes=32 time={delay}ms")


# Example usage:
ping("www.canva.com")
