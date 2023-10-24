import socket
import os
import sys
import struct
import time
import select
import binascii

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


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    # Wait for the socket to receive a reply
    icmpSocket.settimeout(timeout)
    try:
        data, addr = icmpSocket.recvfrom(1024)
        time_received = time.time() * 1000  # Convert to milliseconds
        return data, time_received
    except socket.timeout:
        return None, None


def sendOnePing(icmpSocket, destinationAddress, ID):
    # Build ICMP header
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, ID, 1)
    data = struct.pack("d", time.time())

    # Checksum ICMP packet using given function
    checksum_val = checksum(header + data)

    # Insert checksum into packet
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(checksum_val), ID, 1)

    # Send packet using socket
    icmpSocket.sendto(header + data, (destinationAddress, 1))

    # Record time of sending
    time_sent = time.time() * 1000  # Convert to milliseconds
    return time_sent


def doOnePing(destinationAddress, timeout):
    try:
        # Create ICMP socket
        icmpSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

        # Generate a unique identifier for this ping
        ID = os.getpid() & 0xFFFF

        # Call sendOnePing function
        time_sent = sendOnePing(icmpSocket, destinationAddress, ID)

        # Call receiveOnePing function
        response, time_received = receiveOnePing(icmpSocket, destinationAddress, ID, timeout)

        # Close ICMP socket
        icmpSocket.close()

        if response is not None and time_received is not None:
            # Calculate total network delay
            network_delay = time_received - time_sent
            return network_delay
        else:
            return None

    except socket.error as e:
        print(f"Socket error: {e}")
        return None


def ping(host, timeout=1, count=4):
    try:
        # Look up hostname, resolving it to an IP address
        destinationAddress = socket.gethostbyname(host)
        print(f"Pinging {host} [{destinationAddress}] with 32 bytes of data:")

        total_delay = 0
        packets_sent = 0
        packets_received = 0

        for _ in range(count):
            # Call doOnePing function, approximately every second
            network_delay = doOnePing(destinationAddress, timeout)

            if network_delay is not None:
                packets_sent += 1
                packets_received += 1
                total_delay += network_delay
                print(f"Reply from {destinationAddress}: bytes=32 time={int(network_delay)}ms TTL=50")
                time.sleep(1)  # Wait for 1 second before sending the next ping
            else:
                print("Request timed out.")

        if packets_sent > 0:
            # Calculate packet loss and statistics
            packet_loss = (packets_sent - packets_received) / packets_sent * 100
            average_delay = total_delay / packets_received
            print(f"\nPing statistics for {host}:")
            print(
                f"    Packets: Sent = {packets_sent}, Received = {packets_received}, Lost = {int(packet_loss)}% ({packets_sent - packets_received} lost),")
            print(
                f"Approximate round trip times in milliseconds:\n    Minimum = {int(average_delay)}ms, Maximum = {int(average_delay)}ms, Average = {int(average_delay)}ms")

    except socket.gaierror as e:
        print(f"Could not resolve hostname: {e}")
    except KeyboardInterrupt:
        print("\nPing terminated by user.")


# Example usage:
ping("lancaster.ac.uk")
