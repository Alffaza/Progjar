from socket import *
import socket
import threading
import logging
from datetime import datetime
import time
import sys

def valid_request(string):
	return string[:6] == 'b\'TIME' and string[-5:] == '\\r\\n\''

class ProcessTheClient(threading.Thread):
	def __init__(self,connection,address):
		self.connection = connection
		self.address = address
		threading.Thread.__init__(self)

	def run(self):
		while True:
			data = self.connection.recv(32)
			if data:
				print(data)
				if valid_request(str(data)):
					self.connection.sendall(('TIME ' + str(datetime.now().strftime("%H:%M:%S")) + '\r\n').encode())
					print('valid')
				else:
					self.connection.sendall(('Wrong command').encode())
			else:
				break
		self.connection.close()

class Server(threading.Thread):
	def __init__(self):
		self.the_clients = []
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		threading.Thread.__init__(self)

	def run(self):
		self.my_socket.bind(('0.0.0.0',45000))
		self.my_socket.listen(1)
		while True:
			self.connection, self.client_address = self.my_socket.accept()
			logging.warning(f"connection from {self.client_address}")
			
			clt = ProcessTheClient(self.connection, self.client_address)
			clt.start()
			self.the_clients.append(clt)
	

def main():
	svr = Server()
	svr.start()

if __name__=="__main__":
	main()

