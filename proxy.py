from codecs import strict_errors
import logging
import selectors
import socket
import types
import sys
import json
from enum import Enum, unique
from requests.exceptions import HTTPError
import requests
from .service.proxy_interface import ProxyInterface

forward_to = ('google.com', 80)

@unique
class HttpMethod(Enum):

    POST_METHOD: str = 'POST'
    GET_METHOD: str = 'GET'
    DELETE_METHOD: str = 'DELETE'
    PUT_METHOD: str = 'PUT'

    MAX_TCP_PORT:int = 65535

class RequestForwarder:

    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as ex:
            raise logging.exception(
                f"Error occur while trying to connect to {host}" + str(ex))

class Proxy(ProxyInterface):

    input_list = []
    channel = {}

    def __init__(self, host: str, port: int, func=None):
        self.selector = selectors.DefaultSelector()
        self.sock = None
        self.__host = host
        self.__port = port
        self.func = func
        self.start_server()

    def start_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.__host, self.__port))
        self.sock.listen(20000)
        self.sock.setblocking(False)
        self.selector.register(
            self.sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

        try:
            while 1:
                events = self.selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("close connection by keyboard...")
        finally:
            self.selector.close()

    def accept_wrapper(self, sock):
        forward = RequestForwarder().start(forward_to[0], forward_to[1])
        con, addr = sock.accept()

        if forward:
            print(f"accepting connecting from {addr}.....")
            con.setblocking(False)
            data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
            self.selector.register(con, events, data=data)
            self.input_list.append(con)
            self.input_list.append(forward)
            self.channel[con] = forward
            self.channel[forward] = con
            self.from_byte_to_string(data)
        else:
            con.close()

    def service_connection(self, key, mask):
        self.sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = self.sock.recv(1024)
            if recv_data:
                data.outb += recv_data
                self.channel[self.sock].send(data.outb)
            else:
                self.selector.unregister(self.sock)
                self.sock.close()
                self.input_list.remove(self.sock)
                self.input_list.remove(self.channel[self.sock])
                out = self.channel[self.sock]
                self.channel[out].close()
                del self.channel[out]
                del self.channel[self.sock]

        if mask & selectors.EVENT_WRITE:
            if data.outb:
                self.from_byte_to_string(data.outb)
                self.read_file()

                sent = self.sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

    def _get_host(self) -> str:
        return self.__host

    def _set_host(self, host: str) -> None:
        self.__host = host

    def _get_port(self) -> int:
        return self.__port

    def _set_port(self, port: str) -> None:
        self.__port = port

    @staticmethod
    def get_open_port(host: str) -> list:
        port_list = []
        forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for port in range(1, HttpMethod.MAX_TCP_PORT):
            try:
                forward.connect((host, port))
                port_list.append(port)
            except Exception as error:
                raise logging.exception(error)
        return port_list

    def filter_trafic(self):
        pass

    
    def get_request_status_code(self, url) -> int:
        try:
            response = requests.get(url, timeout=5)
            return response.status_code
        except HTTPError as error:
            print(f"Error occur {error}")
            raise logging.exception(error)

    def from_byte_to_string(self, value: bytes):
        if isinstance(value, bytes):
            try:
                str_value = value.decode()
                with open("data.txt", "w") as file:
                    file.write(str_value)
            except UnicodeDecodeError:
                pass

    def read_file(self):
        print("in file reading....", end='\n')
        with open("data.txt", "r") as file:
            print(file.read())

    property(fget=_get_host, fset=_set_host, doc="host gettter and settter")
    property(fget=_get_port, fset=_set_port, doc="port gettter and settter")


if __name__ == '__main__':
    try:
        print("server launching....")
        server = Proxy("192.168.140.211", 33333)
        server.start_server()
    except KeyboardInterrupt:
        print("Server shooting down")
        sys.exit(1)