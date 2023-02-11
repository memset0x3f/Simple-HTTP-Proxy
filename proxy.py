#! /usr/bin/python3
import socket
import threading

class HTTPParser:
	"""
	Parse the HTTP data.
	Includes raw message: msg
	url: url
	http request method: method
	http version: version
	valid message data: data
	header dictionary: header
	request host: host
	request port: port
	"""
	def __init__(self, msg: bytes):
		# Massage Example:
		# GET http://xxxxxxx/xxxx HTTP/1.1\r\n
		# Host: host:port\r\n
		self.msg = msg
		req_line = msg.split(b'\r\n')[0]
		(self.method, self.url, self.version) = req_line.split(b' ')
		header_lines = msg.split(b'\r\n\r\n')[0].split(b'\r\n')[1:]
		self.data = msg.partition(b'\r\n\r\n')[2]
		self.header = {}
		for line in header_lines:
			key, _, value = line.partition(b':')
			key = key.strip()
			value = value.strip()
			self.header[key] = value
		self.host = self.header[b'Host']
		if self.host.find(b':') == -1:
			if self.method == b'CONNECT':
				self.port = 443
			else:
				self.port = 80
		else:
			self.port = int(self.host.partition(b':')[2])
			self.host = self.host.partition(b':')[0]


class Proxy:
	def __init__(self, host='0.0.0.0', port=8080, buf_size=8):
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Release port when the server ends.
		self.client_socket.bind((host, port))
		self.client_socket.listen(5)
		self.buf_size = buf_size * 1024

	def transfer(self, sender, listener):
		"""
		Get data from the listener socket, and transfer it through the sender socket.
		:param sender: socket that transfer the data
		:param listener: source of data
		:return: None
		"""
		while True:
			try:
				data = listener.recv(self.buf_size)
				if not data:
					break
				sender.sendall(data)
			except OSError:
				break

	def proxy(self, conn: socket.socket, msg: HTTPParser):
		"""
		:param conn: Client socket
		:param msg: Parsed HTTP request message
		:return: None
		"""
		family, sock_type, _, _, sock_addr = socket.getaddrinfo(msg.host, msg.port)[0]      # Get host information
		proxy_socket = socket.socket(family, sock_type)
		try:
			proxy_socket.settimeout(60)
			proxy_socket.connect(sock_addr)
			if msg.method == b'CONNECT':    # HTTPS
				confirm_line = b'%s 200 Connection Established\r\n\r\n' % msg.version
				conn.sendall(confirm_line)  # send confirmation
				thread = threading.Thread(target=self.transfer, args=(proxy_socket, conn))  # Waiting for real data.
				thread.start()
			else:   # HTTP
				proxy_socket.sendall(msg.msg)
			self.transfer(conn, proxy_socket)       # Transfer the data
		except OSError as e:
			proxy_socket.close()
			# print(e)

	def handle_client(self, conn: socket.socket):
		conn.settimeout(60)
		msg = conn.recv(self.buf_size)
		if not msg:
			conn.close()
			return
		data = HTTPParser(msg)
		self.proxy(conn, data)
		conn.close()

	def start(self):
		print('Proxy is ready')
		while True:
			try:
				conn, _ = self.client_socket.accept()
				thread = threading.Thread(target=self.handle_client, args=(conn,))
				thread.start()
			except KeyboardInterrupt:
				self.client_socket.close()
				break


proxy = Proxy()
proxy.start()
