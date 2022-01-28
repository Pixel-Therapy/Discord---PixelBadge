"""
Discord Notifications and Clock for Ipane and PixelBadge
Made by: Axel Roijers

"""

# import logging
import usocket as socket
import ubinascii as binascii
import ussl
from util import notify, connect_wifi
from util import RED, GREEN, BLUE
from protocol import Websocket, urlparse
import rgb, system, machine, time
from clock import update_clock
import urandom as random

rgb.framerate(30)


class WebsocketClient(Websocket):
    is_client = True


def connect_websocket(uri):
    # WARNING: i have no idea how this works but it works
    """
    Connect a websocket.
    """

    uri = urlparse(uri)
    assert uri

    # if __debug__: LOGGER.debug("open connection %s:%s",
    #                             uri.hostname, uri.port)

    sock = socket.socket()
    addr = socket.getaddrinfo(uri.hostname, uri.port)
    sock.connect(addr[0][4])
    if uri.protocol == "wss":
        sock = ussl.wrap_socket(sock)

    def send_header(header, *args):
        # if __debug__: LOGGER.debug(str(header), *args)
        sock.write(header % args + "\r\n")

    # Sec-WebSocket-Key is 16 bytes of random base64 encoded
    key = binascii.b2a_base64(bytes(random.getrandbits(8) for _ in range(16)))[:-1]

    send_header(b"GET %s HTTP/1.1", uri.path or "/")
    send_header(b"Host: %s:%s", uri.hostname, uri.port)
    send_header(b"Connection: Upgrade")
    send_header(b"Upgrade: websocket")
    send_header(b"Sec-WebSocket-Key: %s", key)
    send_header(b"Sec-WebSocket-Version: 13")
    send_header(
        b"Origin: http://{hostname}:{port}".format(hostname=uri.hostname, port=uri.port)
    )
    send_header(b"")

    header = sock.readline()[:-2]
    assert header.startswith(b"HTTP/1.1 101 "), header

    # We don't (currently) need these headers
    # FIXME: should we check the return key?
    while header:
        # if __debug__: LOGGER.debug(str(header))
        header = sock.readline()[:-2]

    return WebsocketClient(sock)


def connect_badgeserver(websocket):

    websocket.send("connect")
    rec = websocket.recv()
    if rec.startswith("connection waiting"):
        key = rec.split(":")[1] # key is the second part of the message
        rgb.clear()
        
        rgb.scrolltext(key)
        print(key)
    if websocket.recv() == "connection accepted":
        # save the key to nvs
        machine.nvs_setstr("Discord", "key", key)
        rgb.clear()
        rgb.scrolltext("Connected", GREEN)
        print("Connected")
    else:
        print("Connection failed")
        rgb.scrolltext("Connection failed", RED)
        time.sleep(6)


def reconnect_badgeserver(websocket, key):

    websocket.send("reconnect:" + key)
    rec = websocket.recv()
    if rec.startswith("connection waiting"):
        rgb.scrolltext("Reconnecting", BLUE)
        print("Reconnecting")
    if websocket.recv() == "connection accepted":
        rgb.clear()
        rgb.scrolltext("Connected", GREEN)
        print("Connected")
    else:
        print("Connection failed")
        rgb.clear()
        rgb.scrolltext("Connection failed", RED)
        #throw an exception
        raise Exception("Connection failed")
        


def main():
    connect_wifi()

    # connect websocket
    print("Awaiting Connection")
    rgb.clear()
    rgb.scrolltext("Seeking Server", BLUE)
    websocket = connect_websocket("ws://192.168.0.147:8765")
    websocket.settimeout(3600)
    rgb.clear()
    # REFERENCE
    # machine.nvs_setstr("system", "wifi.ssid", "YOUR SSID HERE")
    # machine.nvs_setstr("system", "wifi.password", "YOUR PASSWORD HERE")

    try:
        key = machine.nvs_getstr("Discord", "key")
        reconnect_badgeserver(websocket, key)
    except:
        connect_badgeserver(websocket)

    websocket.settimeout(120)
    while True:
        rec = websocket.recv()
        if rec != "ping":
            print(rec)
            who, what, guild, channel = rec.split(":")
            notify(who, what, guild, channel)
            update_clock(force_draw=True)
        else:
            print("pong")
            update_clock()


if __name__ == "__main__":

    interrupt = False
    while not interrupt:
        try:
            main()
        except KeyboardInterrupt:
            print("\nExiting")
            interrupt = True
        except Exception as e:
            rgb.clear()
            rgb.scrolltext("...")
            print("\nError:", e)

    print("rebooting")
    system.reboot()