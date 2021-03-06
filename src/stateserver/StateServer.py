
from panda3d.core import *
from direct.task.TaskManagerGlobal import *
from direct.task.Task import Task
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from src.stateserver.DoInterestManager import DoInterestManager
from src.util.types import *

class StateServer(QueuedConnectionManager):
    
    def __init__(self, client_address, client_port):
        QueuedConnectionManager.__init__(self)
        self.client_address = client_address
        self.client_port = client_port
    
    def configure(self):
        self.cl = QueuedConnectionListener(self, 0)
        self.cr = QueuedConnectionReader(self, 0)
        self.cw = ConnectionWriter(self, 0)
        self.our_channel = STATE_SERVER_CHANNEl
        self.do_interest_manager = DoInterestManager()
        self.run_connection()
    
    def unconfigure(self):
        for participant in self.interface:
            self.cr.removeConnection(participant)
        self.closeConnection(self.tcp_socket)
        self.closeConnection(self.tcp_conn)
        self.cl = self.cr = self.cw = self.tcp_socket = self.tcp_conn = None

    def register_for_channel(self, channel):
        datagram = PyDatagram()
        datagram.addServerHeader(self.our_channel, channel, CONTROL_SET_CHANNEL)
        self.cw.send(datagram, self.tcp_conn)
	
    def unregister_for_channel(self, channel):
        datagram = PyDatagram()
        datagram.addServerHeader(self.our_channel, channel, CONTROL_REMOVE_CHANNEL)
        self.cw.send(datagram, self.tcp_conn)
    
    def run_connection(self):
        self.tcp_conn = self.openTCPClientConnection(self.client_address, self.client_port, 3000)
        if self.tcp_conn:
			self.register_for_channel(self.our_channel)
			self.cr.addConnection(self.tcp_conn)

			taskMgr.add(self.task_reader_poll_reciever, "task reader reciever")
    
    def close_connection(self, code, reason, connection):
		datagram = PyDatagram()
		datagram.addUint16(CLIENT_GO_GET_LOST)
		datagram.addUint16(int(code))
		datagram.addString(str(reason))
		self.cw.send(datagram, connection)

    def task_reader_poll_reciever(self, taskname):
        if self.cr.dataAvailable():
            datagram = NetDatagram()
			
            if self.cr.getData(datagram):
                self.handle_datagram_reciever(datagram)

        return Task.cont

    def handle_datagram_reciever(self, datagram):
        di = PyDatagramIterator(datagram)
        reciever_channel = di.getUint64()
        sender_channel = di.getUint64()
        msg_type = di.getUint16()

        if msg_type == STATESERVER_OBJECT_GENERATE_WITH_REQUIRED:
            location = (di.getUint32(), di.getUint32())
            self.current_reciever = reciever_channel

            if location == (0, 0):
                print ("Tried to generate an object for an unknown location!")
                return

            self.do_interest_manager.handleGenerateWithRequired(self.current_reciever, location, di.getUint32())
        if msg_type == STATESERVER_OBJECT_GENERATE_WITH_REQUIRED_OTHER:
            doId = di.getUint32()
            location = (di.getUint32(), di.getUint32())
            self.current_reciever = reciever_channel

            if location == (0, 0):
                print ("Tried to generate an object for an unknown location!")
                return

            self.do_interest_manager.handleGenerateWithRequiredAndId(self.current_reciever, doId, location, di.getUint32())
        else:
            print ("Stateserver: Recieved a message that's unknown to the protocol, from %s" % str(sender_channel)) # debug error
            return
