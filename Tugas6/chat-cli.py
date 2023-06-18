import socket
import json
import base64
import json
import os
import sys

TARGET_IP = "0.0.0.0"
TARGET_PORT = 8889

if len(sys.argv) > 2:
    TARGET_IP = sys.argv[1]
    TARGET_PORT = int(sys.argv[2])
    print('using server ' + TARGET_IP + ":" + str(TARGET_PORT))

class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP, TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid = ""

    def proses(self, cmdline):
        j = cmdline.split(" ")
        try:
            command = j[0].strip()
            if (command == 'auth'):
                username = j[1].strip()
                password = j[2].strip()
                return self.login(username, password)

            elif (command == 'send'):
                username_to = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}" . format(message, w)
                return self.send_message(username_to, message)
            
            elif (command == 'sendgroup'):
                usernames_to = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}" . format(message, w)
                return self.send_group_message(usernames_to, message)
            
            elif (command == 'inbox'):
                return self.inbox()
            
            elif (command == 'realm'):
                realm_id = j[1].strip()
                realm_command = j[2].strip()

                if (realm_command == 'add'):
                    realm_address = j[3].strip()
                    realm_port = j[4].strip()
                    return self.add_realm(realm_id, realm_address, realm_port)

                elif (realm_command == 'send'):
                    username_to = j[3].strip()
                    message = ""
                    for w in j[4:]:
                        message = "{} {}" . format(message, w)
                    return self.send_realm_message(realm_id, username_to, message)
                
                elif (realm_command == 'sendgroup'):
                    usernames_to = j[3].strip()
                    message = ""
                    for w in j[4:]:
                        message = "{} {}" . format(message, w)
                    return self.send_group_realm_message(realm_id, usernames_to, message)
                
                elif (realm_command == 'inbox'):
                    return self.realm_inbox(realm_id)
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
            return "-Maaf, command tidak benar"

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server", data)
                if (data):
                    receivemsg = "{}{}" . format(receivemsg, data.decode())
                    if receivemsg[-4:] == '\r\n\r\n':
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return {'status': 'ERROR', 'message': 'Gagal'}

    def login(self, username, password):
        string = "auth {} {} \r\n" . format(username, password)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            self.tokenid = result['tokenid']
            return "username {} logged in, token {} " .format(username, self.tokenid)
        else:
            return "Error, {}" . format(result['message'])

    def add_realm(self, realm_id, realm_address, realm_port):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "realm {} add {} {} \r\n" . format(
            realm_id, realm_address, realm_port)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "Realm {} added" . format(realm_id)
        else:
            return "Error, {}" . format(result['message'])

    def send_message(self, username_to="xxx", message="xxx"):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "send {} {} {} \r\n" . format(
            self.tokenid, username_to, message)
        print(string)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "message sent to {}" . format(username_to)
        else:
            return "Error, {}" . format(result['message'])

    def send_realm_message(self, realm_id, username_to, message):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "realm {} send {} {} {}\r\n" . format(
            realm_id, self.tokenid, username_to, message)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "Message sent to realm {}".format(realm_id)
        else:
            return "Error, {}".format(result['message'])

    def send_group_message(self, usernames_to="xxx", message="xxx"):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "sendgroup {} {} {} \r\n" . format(
            self.tokenid, usernames_to, message)
        print(string)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "message sent to {}" . format(usernames_to)
        else:
            return "Error, {}" . format(result['message'])

    def send_group_realm_message(self, realm_id, usernames_to, message):
        if self.tokenid == "":
            return "Error, not authorized"
        string = "realm {} sendgroup {} {} {} \r\n" . format(
            realm_id, self.tokenid, usernames_to, message)

        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "message sent to group {} in realm {}" .format(usernames_to, realm_id)
        else:
            return "Error {}".format(result['message'])

    def inbox(self):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "inbox {} \r\n" . format(self.tokenid)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "{}" . format(json.dumps(result['messages']))
        else:
            return "Error, {}" . format(result['message'])

    def realm_inbox(self, realm_id):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "realm {} inbox {} \r\n" . format(realm_id, self.tokenid)
        print("Sending: " + string)
        result = self.sendstring(string)
        print("Received: " + str(result))
        if result['status'] == 'OK':
            return "Message received from realm {}: {}".format(realm_id, result['messages'])
        else:
            return "Error, {}".format(result['message'])


if __name__ == "__main__":
    cc = ChatClient()
    while True:
        print("\n")
        cmdline = input("Command {}:" . format(cc.tokenid))
        print(cc.proses(cmdline))