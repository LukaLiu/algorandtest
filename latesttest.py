from NoGossipNode import AlgoNode, Pipe
import simpy
import simpy.rt
import time
import numpy as np
from sample_block_delay import generate_block_delays, generate_message_delays
from networkgraph import generate_graph, Node
from processdelaycsv import gen_delay_map


def simu(num_nodes):

	delay_map = gen_delay_map()

	env = simpy.Environment()

	ct_tags = [i for i in range(0,28)]

	nodes = []
	print('initialize network')
	graph_nodes = generate_graph(num_nodes,4)
	block_delays = generate_block_delays(num_nodes)
	for node in graph_nodes:
		newNode = AlgoNode(env,node.id,True,500)
		newNode.set_block_delay(block_delays[node.id])
		nodes.append(newNode)

	print('network created')

	for node in nodes:
		tokens = 6000000
		node.add_tokens(tokens)


	time1 = time.time()
	for node in nodes:
									#600000000
		node.chain.set_total_toknes(1000000000)
		mdelay = generate_message_delays(num_nodes)
		ids = [x for x in range(0,num_nodes)]
		ids.pop(node.id)
		env.process(node.FixedGenerator())
		np.random.shuffle(mdelay)
		for id in ids:
			randdelay = mdelay[id]
			env.process(nodes[id].GossipReceiver(node.Connect(Pipe(env,randdelay))))

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

simu(100)

