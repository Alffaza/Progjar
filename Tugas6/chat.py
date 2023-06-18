import base64
import os
from os.path import join, dirname, realpath
import json
import uuid
import logging
from queue import Queue
import threading
import socket
from datetime import datetime


class RealmThreadCommunication(threading.Thread):
    def __init__(self, chats, realm_dest_address, realm_dest_port):
        self.chats = chats
        self.chat = {}
        self.realm_dest_address = realm_dest_address
        self.realm_dest_port = realm_dest_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.realm_dest_address, self.realm_dest_port))
        threading.Thread.__init__(self)

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivedmsg = ""
            while True:
                data = self.sock.recv(1024)
                print("diterima dari server", data)
                if (data):
                    # data harus didecode agar dapat di operasikan dalam bentuk string
                    receivedmsg = "{}{}" . format(receivedmsg, data.decode())
                    if receivedmsg[-4:] == '\r\n\r\n':
                        print("end of string")
                        return json.loads(receivedmsg)
        except:
            self.sock.close()
            return {'status': 'ERROR', 'message': 'Gagal'}

    def put(self, message):
        dest = message['msg_to']
        try:
            self.chat[dest].put(message)
        except KeyError:
            self.chat[dest] = Queue()
            self.chat[dest].put(message)


class Chat:
    def __init__(self):
        self.sessions = {}
        self.users = {}
        self.users['messi'] = {'nama': 'Lionel Messi', 'negara': 'Argentina',
                               'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
        self.users['henderson'] = {'nama': 'Jordan Henderson', 'negara': 'Inggris',
                                   'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
        self.users['lineker'] = {'nama': 'Gary Lineker', 'negara': 'Inggris',
                                 'password': 'surabaya', 'incoming': {}, 'outgoing': {}}
        self.realms = {}

    def proses(self, data):
        j = data.split(" ")
        try:
            command = j[0].strip()
            if (command == 'auth'):
                username = j[1].strip()
                password = j[2].strip()
                logging.warning(
                    "AUTH: auth {} {}" . format(username, password))
                return self.autentikasi_user(username, password)

            elif (command == 'send'):
                sessionid = j[1].strip()
                username_to = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}" . format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SEND: session {} send message from {} to {}" . format(
                    sessionid, usernamefrom, username_to))
                return self.send_message(sessionid, usernamefrom, username_to, message)
            
            elif (command == 'sendgroup'):
                sessionid = j[1].strip()
                usernames_to = j[2].strip().split(',')
                message = ""
                for w in j[3:]:
                    message = "{} {}" . format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SEND: session {} send message from {} to {}" . format(
                    sessionid, usernamefrom, usernames_to))
                return self.send_group_message(sessionid, usernamefrom, usernames_to, message)
            
            elif (command == 'inbox'):
                sessionid = j[1].strip()
                username = self.sessions[sessionid]['username']
                logging.warning("INBOX: {}" . format(sessionid))
                return self.get_inbox(username)

            elif (command == 'ackrealmadd'):
                realm_id = j[1].strip()
                realm_dest_address = j[3].strip()
                realm_dest_port = int(j[4].strip())
                return self.recv_realm(realm_id, realm_dest_address, realm_dest_port, data)

            elif (command == 'ackrealmsend'):
                realm_id = j[1].strip()
                usernamefrom = j[3].strip()
                username_to = j[4].strip()
                message = ""
                for w in j[5:]:
                    message = "{} {}".format(message, w)
                print(message)
                logging.warning("ACK REALM SEND: recieve message from {} to {} in realm {}".format(
                    usernamefrom, username_to, realm_id))
                return self.recv_realm_message(realm_id, usernamefrom, username_to, message, data)

            elif (command == 'ackrealmsendgroup'):
                realm_id = j[1].strip()
                usernamefrom = j[3].strip()
                usernames_to = j[4].strip().split(',')
                message = ""
                for w in j[5:]:
                    message = "{} {}".format(message, w)
                logging.warning("ACK REALM SENDGROUP: send message from {} to {} in realm {}".format(
                    usernamefrom, usernames_to, realm_id))
                return self.recv_group_realm_message(realm_id, usernamefrom, usernames_to, message, data)
            
            elif (command == 'ackrealminbox'):
                realm_id = j[1].strip()
                username = j[2].strip()
                logging.warning("ACK REALM INBOX: from realm {}".format(realm_id))
                return self.get_realm_chat(realm_id, username)
            
            elif (command == 'realm'):
                realm_id = j[1].strip()
                realm_command = j[2].strip()

                if (realm_command == 'add'):
                    realm_dest_address = j[3].strip()
                    realm_dest_port = int(j[4].strip())
                    return self.add_realm(realm_id, realm_dest_address, realm_dest_port, data)

                elif (realm_command == 'send'):
                    sessionid = j[3].strip()
                    username_to = j[4].strip()
                    message = ""
                    for w in j[5:]:
                        message = "{} {}".format(message, w)
                    print(message)
                    usernamefrom = self.sessions[sessionid]['username']
                    logging.warning("SENDPRIVATEREALM: session {} send message from {} to {} in realm {}".format(
                        sessionid, usernamefrom, username_to, realm_id))
                    return self.send_realm_message(sessionid, realm_id, usernamefrom, username_to, message, data)
                
                elif (realm_command == 'sendgroup'):
                    sessionid = j[3].strip()
                    usernames_to = j[4].strip().split(',')
                    message = ""
                    for w in j[5:]:
                        message = "{} {}".format(message, w)
                    usernamefrom = self.sessions[sessionid]['username']
                    logging.warning("SENDGROUPREALM: session {} send message from {} to {} in realm {}".format(
                        sessionid, usernamefrom, usernames_to, realm_id))
                    return self.send_group_realm_message(sessionid, realm_id, usernamefrom, usernames_to, message, data)
                
                elif (realm_command == 'inbox'):
                    sessionid = j[3].strip()
                    username = self.sessions[sessionid]['username']
                    logging.warning(
                        "GETREALMINBOX: {} from realm {}".format(sessionid, realm_id))
                    return self.get_realm_inbox(username, realm_id)            
            
            else:
                print(command)
                return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
        except KeyError:
            return {'status': 'ERROR', 'message': 'Informasi tidak ditemukan'}
        except IndexError:
            return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}

    def autentikasi_user(self, username, password):
        if (username not in self.users):
            return {'status': 'ERROR', 'message': 'User Tidak Ada'}
        if (self.users[username]['password'] != password):
            return {'status': 'ERROR', 'message': 'Password Salah'}
        tokenid = str(uuid.uuid4())
        self.sessions[tokenid] = {
            'username': username, 'userdetail': self.users[username]}
        return {'status': 'OK', 'tokenid': tokenid}

    def get_user(self, username):
        if (username not in self.users):
            return False
        return self.users[username]

    def send_message(self, sessionid, username_from, username_dest, message):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if (s_fr == False or s_to == False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        message = {'msg_from': s_fr['nama'],
                   'msg_to': s_to['nama'], 'msg': message}
        outqueue_sender = s_fr['outgoing']
        inqueue_receiver = s_to['incoming']
        try:
            outqueue_sender[username_from].put(message)
        except KeyError:
            outqueue_sender[username_from] = Queue()
            outqueue_sender[username_from].put(message)
        try:
            inqueue_receiver[username_from].put(message)
        except KeyError:
            inqueue_receiver[username_from] = Queue()
            inqueue_receiver[username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}

    def send_group_message(self, sessionid, username_from, usernames_dest, message):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        for username_dest in usernames_dest:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {'msg_from': s_fr['nama'],
                       'msg_to': s_to['nama'], 'msg': message}
            outqueue_sender = s_fr['outgoing']
            inqueue_receiver = s_to['incoming']
            try:
                outqueue_sender[username_from].put(message)
            except KeyError:
                outqueue_sender[username_from] = Queue()
                outqueue_sender[username_from].put(message)
            try:
                inqueue_receiver[username_from].put(message)
            except KeyError:
                inqueue_receiver[username_from] = Queue()
                inqueue_receiver[username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}

    def get_inbox(self, username):
        s_fr = self.get_user(username)
        incoming = s_fr['incoming']
        msgs = {}
        for users in incoming:
            msgs[users] = []
            while not incoming[users].empty():
                msgs[users].append(s_fr['incoming'][users].get_nowait())
        return {'status': 'OK', 'messages': msgs}

    def add_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        j = data.split()
        j[0] = "ackrealmadd"
        data = ' '.join(j)
        data += "\r\n"
        if realm_id in self.realms:
            return {'status': 'ERROR', 'message': 'Realm sudah ada'}

        self.realms[realm_id] = RealmThreadCommunication(
            self, realm_dest_address, realm_dest_port)
        result = self.realms[realm_id].sendstring(data)
        return result

    def recv_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        self.realms[realm_id] = RealmThreadCommunication(
            self, realm_dest_address, realm_dest_port)
        return {'status': 'OK'}

    def send_realm_message(self, sessionid, realm_id, username_from, username_dest, message, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr == False or s_to == False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        message = {'msg_from': s_fr['nama'],
                   'msg_to': s_to['nama'], 'msg': message}
        self.realms[realm_id].put(message)

        j = data.split()
        j[0] = "ackrealmsend"
        j[3] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}

    def recv_realm_message(self, realm_id, username_from, username_dest, message, data):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr == False or s_to == False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        message = {'msg_from': s_fr['nama'],
                   'msg_to': s_to['nama'], 'msg': message}
        self.realms[realm_id].put(message)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}

    def send_group_realm_message(self, sessionid, realm_id, username_from, usernames_to, message, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if realm_id not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {'msg_from': s_fr['nama'],
                       'msg_to': s_to['nama'], 'msg': message}
            self.realms[realm_id].put(message)

        j = data.split()
        j[0] = "ackrealmsendgroup"
        j[3] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}

    def recv_group_realm_message(self, realm_id, username_from, usernames_to, message, data):
        if realm_id not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {'msg_from': s_fr['nama'],
                       'msg_to': s_to['nama'], 'msg': message}
            self.realms[realm_id].put(message)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}

    def get_realm_inbox(self, username, realm_id):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        result = self.realms[realm_id].sendstring(
            "ackrealminbox {} {}\r\n".format(realm_id, username))
        return result

    def get_realm_chat(self, realm_id, username):
        s_fr = self.get_user(username)
        msgs = []
        while not self.realms[realm_id].chat[s_fr['nama']].empty():
            msgs.append(self.realms[realm_id].chat[s_fr['nama']].get_nowait())
        return {'status': 'OK', 'messages': msgs}


if __name__ == "__main__":
    j = Chat()
    sesi = j.proses("auth messi surabaya")
    print(sesi)
    tokenid = sesi['tokenid']
    print(j.proses("send {} henderson hello gimana kabarnya son " . format(tokenid)))
    print(j.proses("send {} messi hello gimana kabarnya mess " . format(tokenid)))

    # print j.send_message(tokenid,'messi','henderson','hello son')
    # print j.send_message(tokenid,'henderson','messi','hello si')
    # print j.send_message(tokenid,'lineker','messi','hello si dari lineker')

    print("isi mailbox dari messi")
    print(j.get_inbox('messi'))
    print("isi mailbox dari henderson")
    print(j.get_inbox('henderson'))