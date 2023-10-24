import os
import struct
import time
import select
import socket

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
ID = 0  # ID of icmp_header
SEQUENCE = 0  # sequence of ping_request_msg


def checksum(strings):
    csum = 0
    countTo = (len(strings) / 2) * 2
    count = 0
    while count < countTo:
        thisVal = strings[count + 1] * 256 + strings[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(strings):
        csum = csum + strings[len(strings) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(icmpSocket, ID, timeout):
    # Wait for the socket to receive a reply
    icmpSocket.settimeout(timeout)
    try:
        data, addr = icmpSocket.recvfrom(1024)
        icmpHeader = data[20:28]
        type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
        # Check if the packet is an ICMP echo reply and has the same ID as the request we sent
        if type == ICMP_ECHO_REPLY and packetID == ID:
            timeReceived = time.time() * 1000  # Convert to milliseconds
            return timeReceived
        else:
            return None
    except socket.timeout:
        return None


def sendOnePing(icmpSocket, destinationAddress, ID):
    icmp_checksum = 0
    icmp_header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)
    time_send = struct.pack('!d', time.time())
    icmp_checksum = checksum(icmp_header + time_send)
    icmp_header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)
    icmp_packet = icmp_header + time_send
    icmpSocket.sendto(icmp_packet, (destinationAddress, 1))


def doOnePing(destinationAddress, timeout):
    try:
        icmpName = socket.getprotobyname('icmp')
        icmp_Socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmpName)
        sendOnePing(icmp_Socket, destinationAddress, ID)
        totalDelay = receiveOnePing(icmp_Socket, ID, timeout)
        icmp_Socket.close()
        return totalDelay
    except socket.error as e:
        print(f"Socket error: {e}")
        return None


def ping(host, count, timeout):
    send = 0
    lost = 0
    receive = 0
    maxTime = 0
    minTime = 1000
    sumTime = 0
    desIp = socket.gethostbyname(host)
    global ID
    ID = os.getpid()
    for i in range(0, count):
        global SEQUENCE
        SEQUENCE = i
        delay = doOnePing(desIp, timeout) * 1000
        send += 1
        if delay > 0:
            receive += 1
            if maxTime < delay:
                maxTime = delay
            if minTime > delay:
                minTime = delay
            sumTime += delay
            print(f"Reply from {desIp}: bytes=32 time={int(delay)}ms TTL=50")
        else:
            lost += 1
            print("Request timed out.")
        time.sleep(1)

    if receive != 0:
        avgTime = sumTime / receive
        recvRate = receive / send * 100.0
        print(
            "\nPing statistics for {0}:".format(desIp))
        print(
            f"Packets: Sent = {send}, Received = {receive}, Lost = {lost} ({lost / send * 100}% loss),")
        print(
            "Approximate round trip times in milli-seconds:")
        print(
            f"Minimum = {int(minTime)}ms, Maximum = {int(maxTime)}ms, Average = {int(avgTime)}ms")
    else:
        print("\nPing statistics for {0}:".format(desIp))
        print(
            f"Packets: Sent = {send}, Received = {receive}, Lost = {lost} ({lost / send * 100}% loss),")
        print("Approximate round trip times in milli-seconds:")
        print("Minimum = 0ms, Maximum = 0ms, Average = 0ms")


if __name__ == '__main__':
    while True:
        try:
            hostName = str(input("Input ip/name of the host you want: "))
            count = int(input("How many times you want to detect: "))
            timeout = int(input("Input timeout: "))
            ping(hostName, count, timeout)
            break
        except Exception as e:
            print(e)
            continue
