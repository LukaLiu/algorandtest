import socket
from gossip.util import packing
from gossip.util import message

__author__ = 'Anselm Binninger, Ralph Schaumann, Thomas Maier'

sock1 = socket.socket()
sock2 = socket.socket()
sock1.connect(('192.168.1.11', 6001))
sock2.connect(('192.168.1.11', 6001))
values = packing.pack_gossip_peer_request()
packing.send_msg(sock1, values['code'], values['data'])
values = packing.receive_msg(sock1)
print(values)
message_object = message.MessageGossipPeerResponse(values['message'])
value = message_object.get_values()
print(message_object.connections)
sock1.close()
sock2.close()