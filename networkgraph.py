import networkx
import matplotlib.pyplot as plt
import random


class Node(object):

	def __init__(self,id,peer_lim=4):
		self.id = id
		self.peers =set()
		self.peer_lim=peer_lim

	def full_connected(self):
		if len(self.peers)==self.peer_lim:
			return True
		else:
			return False

	def add_peers(self,id):

		if id !=self.id:
			if not self.full_connected():
				self.peers.add(id)




def generate_graph(nodes_num, peer_limit):
	ids = [i for i in range(nodes_num)]
	nodes = [Node(id,peer_limit) for id in ids]
	graph = networkx.Graph()

	while True:
		graph.add_nodes_from(ids)
		for node in nodes:
			while not node.full_connected():

				random_ids = random.sample(ids,4)
				for id in random_ids:
					node.add_peers(id)

			selfid = node.id
			edges =[]
			for peerid in node.peers:
				edge=(selfid, peerid)
				edges.append(edge)

			graph.add_edges_from(edges)
		if networkx.is_connected(graph):
			f = True
			# peer_list=[]
			# for node in nodes:
			#
			# 	for pid in node.peers:
			# 		peer_list.append(pid)

			# for id in ids:
			# 	if id not in peer_list:
			# 		f = False

			if f:
				return nodes


#
# print('trying')
# graph = generate_graph(100,4)
# print('success')
# print(len(graph.edges))
# graph = networkx.generators.gnp_random_graph(100,0.2)
#
# print(len(graph.edges))
# networkx.draw(graph, with_labels=True, font_weight='bold')
# plt.show()

