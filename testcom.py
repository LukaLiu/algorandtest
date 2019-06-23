from NewAlgoNode import AlgoNode
import simpy
import simpy.rt
import random
import pysnooper
from SortitionNode import AlgoNode as Proposer



def simulate():
	env = simpy.rt.RealtimeEnvironment(factor=0.5,strict=False)
	manual_threshold = 2
	nodes = [AlgoNode(env, id, True,manual_threshold) for id in range(3)]

	nodes[0].peers.append(nodes[1])
	nodes[0].peers.append(nodes[2])

	nodes[1].peers.append(nodes[0])
	nodes[1].peers.append(nodes[2])

	nodes[2].peers.append(nodes[0])
	nodes[2].peers.append(nodes[1])
	for node in nodes:
		node.add_tokens(100)
		env.process(node.FixedGenerator())
		for peer in node.peers:
			env.process(peer.GossipReceiver(node.gossip_pipes.get_out_put_conn()))

	env.run(until=30)
	print(nodes[0].gossip_pipes.pipes)



def simu():
	env = simpy.rt.RealtimeEnvironment(factor=0.5,strict=False)
	nodes = [AlgoNode(env, id, True,1000) for id in range(5)]

	nodes[0].peers.append(nodes[1])
	nodes[0].peers.append(nodes[2])
	nodes[0].peers.append(nodes[4])

	nodes[1].peers.append(nodes[0])
	nodes[1].peers.append(nodes[2])
	nodes[1].peers.append(nodes[4])

	nodes[2].peers.append(nodes[0])
	nodes[2].peers.append(nodes[1])
	nodes[2].peers.append(nodes[3])

	nodes[3].peers.append(nodes[2])
	nodes[3].peers.append(nodes[1])
	nodes[3].peers.append(nodes[4])

	nodes[4].peers.append(nodes[3])
	nodes[4].peers.append(nodes[2])
	nodes[4].peers.append(nodes[1])

	for node in nodes:
		num_token = random.randint(2,300)
		node.add_tokens(num_token)
		env.process(node.FixedGenerator())
		for peer in node.peers:
			env.process(peer.GossipReceiver(node.gossip_pipes.get_out_put_conn()))
	env.run(until=None)
	for node in nodes:
		hashes = [node.chain.chain[round].block_hash for round in node.chain.chain]
		print(f'node {node.id} chain is  hashes {hashes}')

def run_simutlation(node_number, manual_threshhold):
	env = simpy.Environment()
	nodes = [AlgoNode(env,id,True,manual_threshhold) for id in range(node_number)]

	#set up peers
	for node in nodes:

		selfid = node.id

		possible_peer_amount = random.randint(20,node_number-1)

		possible_peers = random.sample(range(0,node_number-1),possible_peer_amount)

		for id in possible_peers:
			if id !=selfid:
				node.peers.append(nodes[id])

	total = 0
	for node in nodes:
		random_token = random.randint(300, 10000)
		node.add_tokens(random_token)
		total +=random_token

	for node in nodes:
		node.chain.set_total_toknes(total)

	for node in nodes:
		env.process(node.FixedGenerator())

		for peer in node.peers:
		 	env.process(peer.GossipReceiver(node.gossip_pipes.get_out_put_conn()))

	env.run(until=None)

def run_Proposers(node_number, manual_threshhold):
	env = simpy.Environment()
	nodes = [Proposer(env,id,True,manual_threshhold) for id in range(node_number)]

	#set up peers
	for node in nodes:

		selfid = node.id

		possible_peer_amount = random.randint(20,node_number-1)

		possible_peers = random.sample(range(0,node_number-1),possible_peer_amount)

		for id in possible_peers:
			if id !=selfid:
				node.peers.append(nodes[id])

	total = 0
	for node in nodes:
		random_token = random.randint(300, 10000)
		node.add_tokens(random_token)
		total +=random_token

	for node in nodes:
		node.chain.set_total_toknes(total)
	count = 0
	for node in nodes:
		result = node.Sortition(node.sk,1,'c'+'1'+'final', 60)

		if result:
			count+=result[2]

	print(f'{count} proposers selected from total {node_number} nodes chain total{total}')
#run_Proposers(300,60)
simulate()
# def GossipGenerator(self):
# 	start_time = time.time()
# 	print(f'node {self.id} starts running\n')
#
# 	flag = True
# 	current_round = 1
# 	tenative = False
# 	# tetup process
# 	yield self.env.timeout(0)
# 	while flag:
# 		print()
#
# 		print(f'node {self.id} in round {current_round} at time {self.env.now} ')
# 		print(f'node {self.id} chain is {self.chain.chain}')
# 		round = current_round
#
# 		# highest priority if not proposer and in case not recieving anything from peers
# 		null_priority = hex(0)
# 		# current round number
#
# 		# manual set proposer number
# 		manual_size = 2
#
# 		# self sort if is proposer
# 		proposer = self.Sortition(self.sk, current_round, block_proposer, manual_size)
#
# 		# if selected as proposer, propose new block
# 		if proposer:
# 			# sortiion result
# 			# (proof,hash,js,indexes)
# 			proof, hash, js, indexes = proposer
#
# 			# get new seed for this block
# 			hashstring_for_seed = self.get_seed(current_round) + str(current_round)
# 			proof_for_seed = vrftool.get_proof(self.sk, hashstring_for_seed)
# 			new_seed = vrftool.get_hash(proof_for_seed)
#
# 			new_block = Block(round, self.chain.chain[round - 1].block_hash,
# 			                  self.pk, proof, new_seed)
# 			new_block.gen_bhash()
#
# 			# caculate the max priority among all subusers
# 			priority, max_index = self.max_priority(new_block.block_hash, indexes)
# 			new_block.add_priority(priority)
# 			# self is proposer then add hihest proority block into self block block_candidates
# 			self.block_candidates[current_round] = list()
# 			# store hash and proof
# 			# hash for seed and proof for random seed for next round
# 			self.block_candidates[current_round].append(new_block)
# 			empty_block = self.generate_empty_block(current_round)
# 			self.block_candidates[current_round].append(empty_block)
# 			highest_priority = priority
#
# 			# construc max pritority message
# 			block_message = Message(self.pk, round, self.tokens, new_block.block_hash, entire_block=new_block,
# 			                        vrf_proof=proof, vrf_hash=hash, priority=priority)
#
# 			gossip_message = (env.now, f'node {self.id} at time {self.env.now} for round{current_round}', block_message)
# 			# test message delay
#
# 			self.gossip_pipes.put(gossip_message)
# 			print(
# 				f'node {self.id} sent out proposal msg with block hash {new_block.block_hash}for its peer at time{self.env.now}')
# 			yield self.env.timeout(4)
#
#
# 		else:
# 			self.block_candidates[current_round] = list()
# 			print(f'node {self.id} failed at proposal sort')
# 			yield self.env.timeout(4)
#
# 		# timeout either proposal or not to
#
# 		if current_round in self.message_buffer.keys():
#
# 			messages = self.message_buffer[current_round]
#
# 			for mes in messages:
# 				if mes.isProposal:
#
# 					new_candidate = mes.block
#
# 					# substitue priorities and check if proposer is new
# 					is_exist = False
#
# 					for candidate in self.block_candidates[current_round]:
# 						if new_candidate.author == candidate.author:
# 							# is_exist=True
# 							if new_candidate.block_hash == candidate.block_hash:
# 								if new_candidate.priority > candidate.priority:
# 									index = self.block_candidates[current_round].index(candidate)
# 									self.block_candidates[current_round][index] = new_candidate
# 								is_exist = True
#
# 					if not is_exist:
# 						self.block_candidates[current_round].append(new_candidate)
#
# 		# set a null block candidates
# 		if not self.block_candidates[current_round]:
# 			empty_block = self.generate_empty_block(current_round)
# 			self.block_candidates[current_round] = [empty_block]
# 		print(f'node {self.id} block candidates after waiting {self.block_candidates}')
# 		ctx = self.get_ctx(current_round)
# 		# iterate through candidates to get hash of block to enter the ba
# 		index = 0
# 		count = 0
# 		highest_priority = 0
# 		for block in self.block_candidates[current_round]:
# 			if count == 0:
# 				index = 0
# 				highest_priority = block.priority
#
# 			else:
# 				if block.priority > highest_priority:
# 					index = self.block_candidates[current_round].index(block)
# 					highest_priority = block.priority
# 			count += 1
#
# 		block_hash = self.block_candidates[current_round][index].block_hash
#
# 		print('\n' + '*' * 50 + f'node {self.id} ' + 'START BA' + '*' * 50)
# 		print(f'\n node {self.id} enters ba process at time{self.env.now} with blockhash {block_hash}')
# 		result = yield self.env.process(self.BA(ctx, round, block_hash))
#
# 		if result[0] == Final_State:
# 			rflag = True
# 			print(f'node {self.id} reaches final at time{self.env.now} for round {current_round}')
# 			if result[1] == NULL_HASH.hex():
# 				block = empty_block
# 			else:
# 				hash = result[1]
# 				for candidate in self.block_candidates[current_round]:
# 					if candidate.block_hash == hash:
# 						block = candidate
# 						rflag = False
# 			if rflag:
# 				print(
# 					f'node {self.id} request {result[1]} while self.candidates are{[b.block_hash for b in self.block_candidates[current_round]]}')
# 				request_msg = ('request', current_round, result[1])
# 				self.waiting_reply = True
# 				self.waiting_block[current_round] = result[1]
# 				self.gossip_pipes.put(request_msg)
#
# 				print(f'node {self.id} finished wating response {self.chain.chain}')
# 			else:
# 				print(f'appending block after consensus, currentround{current_round}, and chain{self.chain.chain}')
# 				self.chain.chain[current_round] = block
# 			print(f'at time {self.env.now} new chain is created {self.chain.chain} with block_hash {result[1]}')
# 			if block.isEmpty:
# 				print(f'round {current_round} consens is reached on empty block')
# 			if not self.waiting_block:
# 				current_round = current_round + 1
# 			else:
# 				yield self.env.timeout(1)
# 				if self.waiting_reply:
# 					print(f"node {self.id} got no response from its peers for block request")
#
# 			# self.block_candidates.clear()
#
# 			self.vote_buffer.clear()
# 		elif result[0] == Tenative_State:
# 			print(f'at time {self.env.now} node {self.id} reaches tenative consensus at round {current_round}')
#
# 		print('\n' + '*' * 50 + f'node {self.id} ' + 'end of BA' + '*' * 50)
#
# 		end = time.time()
# 		print(f'round {current_round} time costs {start_time-end}')
# 		yield self.env.timeout(3)