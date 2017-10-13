import sys
import thread
from socket import *
from datetime import *

class Server:
    def __init__(self, port):
        self.port = port
        self.hostname = ""
        self.sock = None
        self.peerlist = []
        self.latest_cookie = 0
    
    def create_and_bind_socket(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
        except: # Change this line.
            print "Socket could not be created" # log instead.
            sys.exit(1)
        if self.sock is not None:
            try:
                self.sock.bind((self.hostname, self.port))
            except Exception as e:
                print e.message
                print "Could not bind socket to port! Exiting"
                self.shutdown_and_close()
                sys.exit(1)

    def shutdown_and_close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            print "Socket shutdown successfully."
        except Exception as e:
            print e.message, " Couldn't shutdown the socket on the server."
        try:
            self.sock.close()
        except Exception as e:
            print e.message, " Couldn't close the socket"

    def main_loop(self):
        while True:
            self.sock.listen(1)
            conn, cli_addr = self.sock.accept()
            print "Accepting conn with", cli_addr
            thread.start_new_thread(self.process_request, (conn,))
        
    def process_request(self, conn):
        msg = conn.recv(4096)
        if msg.split()[0] == "Register":
            self.process_reg(msg, conn)
        elif msg.split()[0] == "Leave":
            self.process_leave(msg, conn)
        elif msg.split()[0] == "PQuery":
            self.process_pquery(msg, conn)
        elif msg.split()[0] == "Keepalive":
            self.process_keepalive(msg, conn)

    def process_reg(self, msg, conn):
        '''
            Message format: "Register<sp>hostname<sp>cookie<sp>rfc_server_port"
        '''
        # conn.send() of new/existing cookie value.
        # Extract cookie, hostname, RFC Server port and update records.
        hostname = msg.split()[1]
        cookie = int(msg.split()[2])
        # If cookie is not a number or something negative, return an error to the client
        if cookie == 0:
            cookie = self.create_cookie()
        rfc_server_port = msg.split()[3]
        if self.update_records(True, hostname, cookie, rfc_server_port):
            reg_reply = "Register-OK " + str(cookie)
            conn.send(reg_reply)
        else:
            pass # ToDo: Better error message back to the client.

    def process_leave(self, msg, conn):
        '''
            Message format: "Leave<sp>hostname<sp>cookie<sp>rfc_server_port"
        '''
        hostname = msg.split()[1]
        cookie = int(msg.split()[2])
        rfc_server_port = msg.split()[3]
        if self.update_records(False, hostname, cookie, rfc_server_port):
            conn.send("Leave-OK")
        else:
            conn.send("Leave-Fail")

    def process_pquery(self, msg, conn):
        '''
            Message format: "PQuery<sp>cookie"
        '''
        cookie = msg.split()[1]
        peerlist = self.fetch_peer_list() # peerlist: dict
        conn.send(peerlist)
    
    def process_keepalive(self, msg, conn):
        '''
            Message format: "Keepalive<sp>hostname<sp>cookie<sp>"
        '''
        # What if a peer sends a keepalive after being inactive? Shouldn't it register first?
        hostname = msg.split()[1]
        cookie = int(msg.split()[2])
        peer = self.find_peer(cookie)
        if not peer:
            conn.send("Keepalive-Fail")
        else:
            peer.ttl = 7200
            peer.flag = True    # Set flag to true irrespective of what it was.
        
        # ToDo: Manage timing of client.
    
    def update_records(self, isReg, hostname, cookie, rfc_server_port):
        # Use this method for "Register" and "Leave" messages.
        if isReg:
            # Check if peer is already present using cookie.
            peer = self.find_peer(cookie)
            if not peer:
                peer_exists = False
                peer = Peer(hostname, cookie, rfc_server_port)
            else:
                peer_exists = True
            peer.ttl = 7200
            peer.flag = True
            peer.latest_register = datetime.now().strftime('%s')
            peer.num_registers += 1
            
            if not peer_exists:
                self.peerlist.append(peer)
            return True
        else:
            print cookie, self.find_peer(cookie)
            peer = self.find_peer(cookie)
            if not peer:
                return False
            else:
                if peer.flag == False:
                    # A peer that is inactive wants to leave. Return False.
                    return False
                peer.flag = False
                peer.ttl = 0
                return True

    def find_peer(self, cookie):
        for i in self.peerlist:
            if i.cookie == cookie:
                return i
        return None
        
    def create_cookie(self):
        self.latest_cookie += 1
        return self.latest_cookie


class Peer:
    def __init__(self, hostname, cookie, rfc_server_port):
        self.hostname = hostname
        self.cookie = cookie
        self.rfc_server_port = rfc_server_port
        self.ttl = 0
        self.flag = False
        self.latest_register = 0
        self.num_registers = 0


def main():
    port = 65423
    s = Server(port)
    s.create_and_bind_socket()
    s.main_loop()
if __name__ == '__main__':
    main() 

# Create main_loop which runs forever.
# Accept connections and create a thread to process the request.





