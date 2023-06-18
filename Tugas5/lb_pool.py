import socket
import time
import sys
import asyncore
import logging
from concurrent.futures import ProcessPoolExecutor


class BackendList:
	def __init__(self):
		self.servers=[]
		self.servers.append(('127.0.0.1',8002))
		self.servers.append(('127.0.0.1',8003))
		self.servers.append(('127.0.0.1',8004))
		self.servers.append(('127.0.0.1',8005))
		self.current=0
	def getserver(self):
		s = self.servers[self.current]
		self.current=self.current+1
		if (self.current>=len(self.servers)):
			self.current=0
		return s


class Backend():
	def __init__(self,targetaddress):
		asyncore.dispatcher_with_send.__init__(self)
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# self.connect(targetaddress)
		# self.connection 

	def handle_read(self, data):
			self.client_socket.sendall(data)
	def handle_close(self):
		try:
			self.close()
			self.client_socket.close()
		except:
			pass


class ProcessTheClient():
	def __init__(self, sock):
		self.my_socket = sock
	def handle_read(self):
		data = self.my_socket.recv(64)
		if data:
			self.backend.client_socket = self.my_socket
			self.backend.my_socket = self.my_socket
			self.backend.handle_read(data)
			self.backend.handle_close()
			# self.my_socket.send(data)
	def handle_close(self):
		self.my_socket.close()

class Server():
	def __init__(self,portnumber):
		asyncore.dispatcher.__init__(self)
		my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		my_socket.bind(('127.0.0.1',portnumber))
		my_socket.listen(5)
		executor = ProcessPoolExecutor(max_workers=10)
		logging.warning("load balancer running on port {}" . format(portnumber))
		self.bservers = BackendList()
		while True:
			pair = my_socket.accept()
			if pair is not None:
				sock, addr = pair
				logging.warning("connection from {}" . format(repr(addr)))

				#menentukan ke server mana request akan diteruskan
				bs = self.bservers.getserver()
				logging.warning("koneksi dari {} diteruskan ke {}" . format(addr, bs))
				backend = Backend(bs)

				#mendapatkan handler dan socket dari client
				handler = ProcessTheClient(sock)
				handler.backend = backend
				handler.handle_read()
				handler.handle_close()



	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			sock, addr = pair
			logging.warning("connection from {}" . format(repr(addr)))

			#menentukan ke server mana request akan diteruskan
			bs = self.bservers.getserver()
			logging.warning("koneksi dari {} diteruskan ke {}" . format(addr, bs))
			backend = Backend(bs)

			#mendapatkan handler dan socket dari client
			handler = ProcessTheClient(sock)
			handler.backend = backend


def main():
	portnumber=44444
	try:
		portnumber=int(sys.argv[1])
	except:
		pass
	svr = Server(portnumber)

if __name__=="__main__":
	main()


