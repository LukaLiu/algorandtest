from NewMesgNode import AlgoNode, Pipe
import simpy
import simpy.rt
import time
import random
from sample_block_delay import generate_block_delays
import pysnooper
from SortitionNode import AlgoNode as Proposer
from Message import Message
import networkx
from networkgraph import generate_graph, Node
from processdelaycsv import gen_delay_map



def simulate():
	delay_map = gen_delay_map()
	env = simpy.rt.RealtimeEnvironment(factor=1,strict=False)
	manual_threshold = 1000
	nodes = [AlgoNode(env, id, True, manual_threshold) for id in range(4)]


	nodes[0].tag_as_ct(0)
	nodes[1].tag_as_ct(1)
	nodes[2].tag_as_ct(2)

	nodes[0].peers.append(1)
	nodes[0].peers.append(2)

	nodes[1].peers.append(2)


	nodes[2].peers.append(3)

	nodes[3].peers.append(1)

	for node in nodes:

		node.add_tokens(100)

		env.process(node.FixedGenerator())

		for peer_id in node.peers:

			source_ct = node.ct_tag
			detination = nodes[peer_id].ct_tag
			delay = delay_map[source_ct][detination]

			env.process(nodes[peer_id].GossipReceiver(node.Connect(Pipe(env,delay))))


	env.run()

	print('test chains')
	for node in nodes:
		print(f'node {node.id} chain as follow')
		print(f'{[node.chain.chain[round].block_hash for round in node.chain.chain]}')


def simu(num_nodes):

	delay_map = gen_delay_map()
	print(delay_map[0][1])
	env = simpy.Environment()

	ct_tags = [i for i in range(0,28)]

	nodes = []
	print('initialize network')
	graph_nodes = generate_graph(num_nodes,5)
	block_delays = generate_block_delays(num_nodes)
	for node in graph_nodes:
		newNode = AlgoNode(env,node.id,True,2000)

		#
		ct_tag = random.sample(ct_tags[0:5],1)[0]
		#ct_tag = 1
		newNode.tag_as_ct(ct_tag)
		newNode.set_block_delay(block_delays[node.id])


		for pid in node.peers:

			newNode.peers.append(pid)
		nodes.append(newNode)



	print('network created')
	total = 0
	for node in nodes:
		tokens = 260000
		node.add_tokens(tokens)
		total+=tokens

	time1 = time.time()
	for node in nodes:
		node.chain.set_total_toknes(100000000)
		env.process(node.FixedGenerator())
		for peerid in node.peers:

			source_ct = node.ct_tag

			detination = nodes[peerid].ct_tag

			delay = delay_map[source_ct][detination]

			env.process(nodes[peerid].GossipReceiver(node.Connect(Pipe(env,delay))))

	env.run(until=None)
	time2=time.time()
	flag=True
	print(f'total time cost {time2-time1}')
	for node in nodes:
		for n in nodes:
			if node.id !=n.id:
				for round in range(1,2):
					if node.chain.chain[round].block_hash!=n.chain.chain[round].block_hash:
						print('different ledger detected')
						print(f'the differen bhash are {node.chain.chain[round].block_hash} and {n.chain.chain[round].block_hash}')
						flag =False
	if flag:
		print('no diverge found')

	for node in nodes:
		print(f'node {node.id} gossiped {len(node.Gossiped_Msg)} msgs')

	total = 0
	for node in nodes:
		total+=node.counttime
	print('total time to count ', total)

simu(1000)

# random_network = generate_graph(200,4)
# print('success')
#
# ids = random_network.nodes
#
#
# for id in ids:
# 	peers = set()
# 	for edge in random_network.edges:
# 		if edge[0] == id:
# 			peers.add(edge[1])
# 		elif edge[1] == id:
# 			peers.add(edge[0])
# 	node = AlgoNode(env,id,True,20000)
#
# 	for p in peers:
# 		node.peers.append(p)
#
# 	nodes.append(node)
