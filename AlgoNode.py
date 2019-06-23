from BlockChain import BlockChain
import vrftool
import simpy
from utils import *
from Block import Block
from hashlib import sha256
import pysnooper
import time
import uuid
import random

system_sk = b'413a67a03a4da74902bc061429a2a7b63425b55cad6f31ede3e6764c2374c8254265c247c6b2583b2c49a868c63b910181d315646d486e4b193d89a6152bf996'
system_pk = b'4265c247c6b2583b2c49a868c63b910181d315646d486e4b193d89a6152bf996'
NULL_HASH = 0x00.to_bytes(32, byteorder='little')
block_proposer = 'b'
committe_member = 'c'
total_tokens = 100000
BA_Thresh=2/3
Final_State = 'final'
Tenative_State = 'tenative'
proposer_probs = 50/10000
block_proposer_size = 26
time_out_block_proposal=2
time_out_step = 5
Reduction_one=1
Reduction_two=2
manual_committe_size = 2




class Links(object):

	def __init__(self,env,capacity=simpy.core.Infinity):
		self.env=env
		self.capacity=capacity
		self.pipes= []



	#put msg
	def put(self,msg):

		if not self.pipes:
			raise RuntimeError('no peer linked')

		events = [store.put(msg) for store in self.pipes]
		return self.env.all_of(events)

	#create new connection
	def get_out_put_conn(self):
		pipe = simpy.Store(self.env, capacity=self.capacity)
		self.pipes.append(pipe)
		return pipe

class Gossip_pipe(object):

	def __init__(self,env, capacity=simpy.core.Infinity):

		self.env=env
		self.capacity = capacity




class AlgoNode(object):

	def __init__(self, env, id,  honest, manual_committee_size=2):
		self.env = env
		self.id = id
		self.chain=BlockChain()
		self.gossip_pipes = Links(self.env)
		#store peer AlgoNode for shuffling
		self.peers=list()
		self.pipe = simpy.Store(self.env)
		self.sk = vrftool.new_sk()
		self.pk= vrftool.get_pk(self.sk)
		self.proposers = 100

		self.manual_committee_size = manual_committee_size
		self.block_candidates = dict()
		#buffer structure: round:messages
		self.blocks_and_proof=dict()
		#record incoming msg
		self.message_buffer=dict()
		#store votes for each step
		self.vote_buffer = dict()
		#store voters and their votes for each round an step
		self.voters = dict()
		self.request = list()
		self.unprocessed_msg = list()
		self.waiting_block=dict()
		self.waiting_reply = False
		self.Tenative = False
		#set node type honest or malicious
		if honest:
			self.honest = True
		else:
			self.honest = False

	# def new_secret_key(self):
	# 	self.sk = vrftool.new_sk()

	#give tokens to account
	def add_tokens(self, tokens):
		self.tokens = tokens

	#add id of new peer list, which is set as integer for convinient simulation
	def add_peers(self,id):
		if id not in self.peers:
			self.peers.append(id)

	def propose_block(self,sortition_result, current_round):

		proof,hash,j,indexes = sortition_result

		#getting seed
		hashstring_for_seed = self.get_seed(current_round) + str(current_round)
		proof_for_seed = vrftool.get_proof(self.sk, hashstring_for_seed)
		new_seed = vrftool.get_hash(proof_for_seed)

		new_block = Block(current_round, self.chain.chain[current_round - 1].block_hash,
		                  self.pk, proof, new_seed)
		new_block.gen_bhash()

		# caculate the max priority among all subusers
		priority, max_index = self.max_priority(new_block.block_hash, indexes)
		new_block.add_priority(priority)
		# self is proposer then add hihest proority block into self block block_candidates
		self.block_candidates[current_round] = list()
		# store hash and proof
		# hash for seed and proof for random seed for next round
		self.block_candidates[current_round].append(new_block)



		# construc max pritority message
		block_message = Message(self.pk, current_round, self.tokens, new_block.block_hash, entire_block=new_block,
		                        vrf_proof=proof, vrf_hash=hash, priority=priority)

		gossip_message = (self.env.now, (self.id,current_round), block_message)
		# test message delay

		self.gossip_pipes.put(gossip_message)
		print(f'node {self.id} sent out proposal msg with block hash {new_block.block_hash}for its peer at time{self.env.now}')

	def gossip_incoming_msg(self):

		for msg in self.unprocessed_msg:
			self.gossip_pipes.put(msg)

	def process_proposal(self,current_round):

		if current_round in self.message_buffer.keys():

			messages = self.message_buffer[current_round]
			if messages:
				for msg in messages:
					gossip = (self.env.now, (self.id,current_round),msg)
					self.gossip_pipes.put(gossip)


			for mes in messages:

					##print(f'node {self.id} send proposal to its peerr from other source')

				if mes.isProposal:

					new_candidate = mes.block

					# substitue priorities and check if proposer is new
					is_exist = False
					if self.block_candidates[current_round]:
						for candidate in self.block_candidates[current_round]:
							if new_candidate.author == candidate.author:
								# is_exist=True
								if new_candidate.block_hash == candidate.block_hash:
									if new_candidate.priority > candidate.priority:
										index = self.block_candidates[current_round].index(candidate)
										self.block_candidates[current_round][index] = new_candidate
									is_exist = True

						if not is_exist:
							self.block_candidates[current_round].append(new_candidate)
					else:
						self.block_candidates[current_round].append(new_candidate)

	# implementation of Gossip message to peers
	# Simpy Msg generator


	def handle_result(self,current_round, block_hash):
		empty_block=self.generate_empty_block(current_round)

		if block_hash == empty_block.block_hash:
			new_block = empty_block
			self.chain.chain[current_round] = new_block

			print(f'node {self.id} reaches final consensus at time {self.env.now} with empty block ')
			return True
		else:

			new_block = None
			for candidate in self.block_candidates[current_round]:
				if candidate.block_hash == block_hash:
					new_block = candidate
			if new_block:
				self.chain.chain[current_round] = new_block
				print(
					f'node {self.id} reaches final consensus at time {self.env.now} with blockhash{new_block.block_hash} ')
				return True
			else:
				# request message
				print(
					f'node {self.id} request {block_hash} while self.candidates are{[b.block_hash for b in self.block_candidates[current_round]]}')
				request_msg = ('request', current_round, block_hash)
				self.waiting_reply = True
				self.waiting_block[current_round] = block_hash
				self.gossip_pipes.put(request_msg)

				print(f'node {self.id} request block from peers for round {current_round}')
				return False

	def FixedGenerator(self):

		start_time =time.time()

		current_round = 1
		#manual size for committe size

		manual_proposers = 26
		flag = True
		while flag:

			print(f'node {self.id} enters round {current_round}')
			if not self.Tenative and not self.waiting_reply:

				empty_block = self.generate_empty_block(current_round)
				proposer = self.Sortition(self.sk, current_round, block_proposer, block_proposer_size)

				if proposer:

					self.propose_block(proposer, current_round)
					print(f'node {self.id} is proposer timeout for 2')
					yield self.env.timeout(2)
					#print(f'node {self.id} checking incoming proposal at time {self.env.now}')
					self.process_proposal(current_round)

				else:
					self.block_candidates[current_round]=list()
					yield self.env.timeout(2)

				if self.block_candidates[current_round]:
					#print(f'node {self.id} is proposer so timeout for 2\n')
					yield self.env.timeout(2)
				else:
					#print(f'node {self.id} not proposer so timeout for another 2\n')
					yield self.env.timeout(2)



				self.process_proposal(current_round)
				print(f'node {self.id} at time {self.env.now}')
				exit()
				#print(f'node {self.id} block candidates after waiting is {self.block_candidates} at time {self.env.now}')

				#if still null, add empty block to it
				if not self.block_candidates[current_round]:
					self.block_candidates[current_round]=[empty_block]

				index = self.find_max_priority_proposal(current_round)
				bhash = self.block_candidates[current_round][index].block_hash

				#print(f"node {self.id} ready to start ba with block_hash {bhash} at time {self.env.now}")

				ctx = self.get_ctx(current_round)
				result = yield self.env.process(self.BA(ctx, current_round, bhash))

				if result[0]==Final_State:
					if self.handle_result(current_round, result[1]):
						current_round+=1

				elif result[0]==Tenative_State:
					self.Tenative=True

			elif self.Tenative:

				print('in tenative')


				break;
				yield self.env.timeout(1)
				result = self.CountVotes(ctx,current_round,Final_State,self.manual_committee_size)


				if result:
					if self.handle_result(current_round, result):
						current_round+=1
				else:
					pass
			elif self.waiting_reply:
				block_hash = self.waiting_block[current_round]

				request_msg = ('request', current_round, block_hash, self.id)
				self.waiting_reply = True
				self.waiting_block[current_round] = block_hash
				self.gossip_pipes.put(request_msg)
				yield self.env.timeout(1)
				print(f'not the first time node {self.id} request block from peers for round {current_round}')


	#connect new peers, add pipes to output conn in simpy
	# Simpy Msg receiver
	#@pysnooper.snoop()
	def GossipReceiver(self,gossips_in):


		while True:
			# if self.id ==2:
			# 	yield self.env.timeout(3)
			# print(f'\n node {self.id} was  delayed for {latency} \n')
			# yield self.env.timeout(latency)

			#print(f'node {self.id} start receiver at time {self.env.now}')

			msg = yield gossips_in.get()


			if not msg:
				#print(f'node {self.id} doesnt have incoming msg at time {self.env.now}')
				#print(f'node {self.id} not recieve any incoming msg yet at time {self.env.now}')
				pass
			elif msg[0]=='request':
				#print(f'node {self.id} get request block msg')
				request_bhash = msg[2]
				round = msg[1]
				if round in self.block_candidates.keys():
					for block in self.block_candidates[round]:
						if block.block_hash == request_bhash:
							rp_msg = ('reply', block, round)
							self.gossip_pipes.put(rp_msg)
							yield self.env.timeout(0)


			elif msg[0]=='reply':
				#print(f'node {self.id} got request msg')
				if not self.waiting_reply:
					pass
				else:
					round = msg[2]
					block = msg[1]
					bhash = block.block_hash
					if bhash == self.waiting_block[round]:
						self.chain.chain[round]= block
						self.waiting_reply=False
						print(f'\nnode {self.id} request block has been fullfilled\n')

			else:

				if msg[2]:

					if msg[2].isProposal:
						#simulateing latency here for block proposale
						#print(f'node {self.id} process block proposal msg at time{self.env.now}\n')
						print(f'node {self.id} has incoming proposal at time {self.env.now}')
						round = msg[2].round

						if round not in self.message_buffer:

							self.message_buffer[round] = [msg[2]]


						else:
							if msg[2] not in self.message_buffer[round]:
								self.message_buffer[round].append(msg[2])

							else:
								pass

					else:

						#self.gossip_pipes.put(msg)

						self.unprocessed_msg.append(msg[2])



			self.gossip_pipes.put(msg)
			yield self.env.timeout(1)

			# print(f'\n node {self.id} was  delayed for {latency} \n')


	#@pysnooper.snoop()
	def BA(self, ctx, current_round, block_hash):

		#

		h_block = yield self.env.process(self.Reduction(ctx, current_round, block_hash))




		#print(f'at time {self.env.now} after reduction node {self.id} check vote buffer: {self.vote_buffer}')


		h_block_from_bba = yield self.env.process(self.Binary_BA(ctx,current_round,h_block))


		final_step_committee = self.manual_committee_size

		yield self.env.timeout(1)
		r = self.CountVotes(ctx,current_round,Final_State, final_step_committee)


		if h_block_from_bba==r:
			return (Final_State, h_block_from_bba)
		else:
			return (Tenative_State, h_block_from_bba)

	#@pysnooper.snoop()
	def Reduction(self, ctx, current_round, block_hash):
		empty_block = self.generate_empty_block(current_round)
		#step 1


		reduction_step_one = 'reduction1'

		#threshnum = self.manual_committee_size
		threshnum = 2
		#yield self.env.process(self.Committe_vote(ctx, round, reduction_step_one, threshnum, block_hash))
		print(f'\n node {self.id} starts calling committe votes at time {self.env.now}')
		self.Committe_vote(ctx, current_round, reduction_step_one, self.manual_committee_size, block_hash)

		yield self.env.timeout(2)

		#set for committe_size whilte testing
		manual_committee_size = 2

		step_one_result = self.CountVotes(ctx, current_round, step=reduction_step_one, committe_size=self.manual_committee_size)



		#start of reduction 2
		print('\n'+'*'*50+f' node{self.id} '+'start of reduction2'+'*'*50)
		reduction_step_two='reduction2'


		if not step_one_result:
			#commitee vote for empty block


			self.Committe_vote(ctx, current_round, reduction_step_two, self.manual_committee_size, empty_block.block_hash)
		else:


			self.Committe_vote(ctx, current_round, reduction_step_two, self.manual_committee_size, step_one_result)

		yield self.env.timeout(2)



		step_two_result = self.CountVotes(ctx,current_round, step=reduction_step_two,committe_size= self.manual_committee_size)

		if not step_two_result:

			return empty_block.block_hash
		else:

			return step_two_result




	def Binary_BA(self, ctx, round, block_hash):
		max_step = 10

		step=1

		r = block_hash
		manual_threshold = self.manual_committee_size

		empty_block = self.generate_empty_block(round)

		while step <= max_step:
			step_prefix = 'bba'
			#yield self.env.process(self.Committe_vote(ctx, round, step_prefix+str(step), manual_threshold, r))
			self.Committe_vote(ctx, round, step_prefix + str(step), manual_threshold, r)
			yield self.env.timeout(2)

			r = self.CountVotes(ctx,round,step_prefix+str(step),manual_threshold)

			#print(f'node {self.id} check if block hash is equal to empty {r == empty_block.block_hash}')
			if not r:
				r = block_hash

			elif r != empty_block.block_hash:
				for step_prime in range(step+1,max_step+1):

					#yield self.env.process(self.Committe_vote(ctx,round,step_prefix+str(step_prime), manual_threshold,r))
					self.Committe_vote(ctx, round, step_prefix + str(step_prime), manual_threshold, r)
				if step == 1:

					#yield self.env.process(self.Committe_vote(ctx, round, Final_State, manual_threshold, r))
					self.Committe_vote(ctx, round, Final_State, manual_threshold, r)

				return r

			step+=1


			self.Committe_vote(ctx, round, step_prefix + str(step), manual_threshold, r)


			yield self.env.timeout(1)

			r = self.CountVotes(ctx,round,step_prefix+str(step),manual_threshold)


			if not r:
				r = empty_block.block_hash
			elif r == empty_block.block_hash:
				for step_prime in range(step+1,step+4):
					#yield self.env.process(self.Committe_vote(ctx,round, step_prefix+str(step_prime),manual_threshold,r))
					self.Committe_vote(ctx, round, step_prefix + str(step_prime), manual_threshold, r)

				return r

			step+=1

			#yield self.env.process(self.Committe_vote(ctx, round,step_prefix+str(step),manual_threshold,r))
			self.Committe_vote(ctx, round, step_prefix + str(step), manual_threshold, r)

			yield self.env.timeout(1)
			r = self.CountVotes(ctx,round,step_prefix+str(step),self.manual_committee_size)

			if not r:

				if self.CommonCoin(ctx, round, step_prefix+str(step),manual_threshold) == 0:

					r = block_hash
				else:
					r = empty_block.block_hash

			step+=1




		#construct votes into gossip messages
		#check if user is in committer
		#if true, construct votes and gossip the message
	def Committe_vote(self, ctx, round, step, threshold, value):

		seed, user_tokens, prev_blockhash= ctx

		role = committe_member+str(round)+str(step)

		sort_result = self.Sortition(self.sk, round, role, threshold)

		if sort_result:
			#value is the incoming candidate blockhash
			print(f'node {self.id} selected as committe in step {step} and round {step} with votes {sort_result[2]}')
			vote_message = Message(self.pk, round, self.tokens, value, vrf_proof=sort_result[0],isProposal=False,votes=sort_result[2])
			vote_message.add_vote_info(step, sort_result[1], prev_blockhash)

			selfvotes = vote_message.votes

			#vote_message=(self.env.now, self.pk,vote_message,self.id)
			vote_message=(self.env.now, self.pk,vote_message)
			self.store_voters(round, step,selfvotes,self.pk)
			self.store_vote(round, step, value, selfvotes)
			self.gossip_pipes.put(vote_message)



	#count committe votes in the network,
	# time_out is the lambada parameter to control waiting time
	# input argument to be finished

	def CountVotes(self,ctx, round, step, committe_size, step_thresh=None,timeout_lambda=2):
		ba_thresh = 2/3
		if step == Final_State:
			ba_thresh = 0.74


		msgs= self.unprocessed_msg

		#timeout for others to recieve gossip
		#temporatly use false to represent timeout in first procedure

		if not msgs:
			#return false if there is no incoming votes, which is timeout in paper

			return False
		else:
			#process and verify all the incmoing votes and count vote values
			processed_key=[]
			for msg in msgs:
				if not msg.isProposal:
					index = msgs.index(msg)

					if self.store_voters(msg.round, msg.voteinfo[0], msg.votes, msg.pk):
						self.store_vote(msg.round, msg.voteinfo[0], msg.block_hash, msg.votes)
						processed_key.append(index)


			#remove unprocessed msg
			# rev_keys = sorted(processed_key,reverse=True)
			# for k in rev_keys:
			# 	pk = self.unprocessed_msg[k].pk
			# 	f = True
			# 	for peer in self.peers:
			# 		if pk == peer.pk:
			# 			f=False
			# 	if f:
			# 		# print('sending peer vote from other resource')
			# 		vote_msg = (self.env.now,pk,self.unprocessed_msg[k])
			# 		self.gossip_pipes.put(vote_msg)
				# self.unprocessed_msg.pop(k)

			#check if there is votes passed
			#print(f'\nnode {self.id} vote buffer in round {round} step {step} after count is {self.vote_buffer}')
			thresh_vote = ba_thresh*self.manual_committee_size
			test_thresh_vote=2
			key = (round, step)

			if key in self.vote_buffer.keys():
				print(f'vote buffer {self.vote_buffer}')
				for hash in self.vote_buffer[key]:
					if self.vote_buffer[key][hash]>=thresh_vote:
						return hash
					else:
						print(f'at time {self.env.now} node {self.id} failed count vote at {key}')


			return False

	#common coin
	def CommonCoin(self, ctx, round, step, thresh_num):
		minhash = 'f'*64
		for msg in self.unprocessed_msg:
			if (msg.round,msg.voteinfo[0]) == (round,step):
				js = msg.votes
				sort_hash = msg.voteinfo[1]
				for j in range(0,js):

					hash_string = sort_hash.decode('utf-8')+str(j)
					new_hash = sha256(hash_string.encode('utf-8')).digest().hex()

					if new_hash<minhash:
						minhash = new_hash

		minhash = int(minhash,16)

		return minhash%2

	#crypto sortition
	# if there is selected subuser, return number of subusers and indexes
	# if sortition is null, return False
	def Sortition(self,secret_key, round, role, thresh_num):


		vrfstring = self.get_seed(round) + role

		proof = vrftool.get_proof(secret_key, vrfstring)

		hash = vrftool.get_hash(proof)

		# probs shoud be equal to the threshhold set by the system
		# proposers/totla_tokens, varing from 26 to 70
		probs = thresh_num / self.chain.total_tokens

		#get the subuser number and indexes
		js, indexes = self.sub_users(self.tokens, probs, hash)

		if js==0:

			return False
		else:
			result =(proof,hash,js,indexes)

			return result
		# if role == block_proposer:elif role == committe_member:

	#get context info using current round_number
	# return seed, user_total_tokens, previous block in the chain

	def get_ctx(self,current_round):

		return (self.get_seed(current_round), self.tokens, self.chain.chain[current_round-1].block_hash)

	#current ongoing round shoud be chain rounds+1
	#chain stores valid
	def get_current_round(self):
		return self.chain.rounds+1

	def find_max_priority_proposal(self,current_round):
		index = 0
		count = 0
		highest_priority = 0
		for block in self.block_candidates[current_round]:
			if count == 0:
				index = 0
				highest_priority = block.priority

			else:
				if block.priority > highest_priority:
					index = self.block_candidates[current_round].index(block)
					highest_priority = block.priority
			count += 1
		return index

	def Verify_Sort(self, pk, hash, proof, seed, thresh_num, role, user_total_tokens):

		#to be implemented

		return vrftool.verify_proof(proof,pk, (seed+role))
	#store vote buffer
	def store_vote(self, round, step, block_hash, votes):
		key = (round,step)

		if key in self.vote_buffer.keys():

			if block_hash in self.vote_buffer[key].keys():
				self.vote_buffer[key][block_hash]+=votes
			else:
				self.vote_buffer[key][block_hash]=votes

		else:

			self.vote_buffer[key]=dict()
			self.vote_buffer[key][block_hash]=votes

	def store_voters(self,round,step, votes, voter):
		key = (round, step)
		if key in self.voters:
			val = (voter,votes)
			if val not in self.voters[key]:
				self.voters[key].append(val)
				return True
			else:

				return False
		else:
			self.voters[key]= list()
			self.voters[key].append((voter,votes))
			return True

	def generate_empty_block(self,current_round):
		null_priority = hex(0)
		hashstring_for_seed = self.get_seed(current_round) + str(current_round)
		proof_for_seed = vrftool.get_proof(system_sk, hashstring_for_seed)
		new_seed = vrftool.get_hash(proof_for_seed)
		empty_block = Block(current_round, self.chain.chain[current_round-1].block_hash, author=system_pk,author_proof=proof_for_seed, seed = new_seed, isEmpty=True)

		empty_block.add_priority(null_priority)

		return empty_block

	def Verify_Gossip(self, message, ctx=None):
		pk = message.pk
		proof = message.proof
		round = message.round

		if message.isProposal:
			if round - len(self.chain.chain)>1:
				print(f'node {self.id} cant verify coz outdated chain')
				return False
			seed =self.get_seed(round)
			hashstring = seed + block_proposer

			return vrftool.verify_proof(proof,pk, hashstring)

		else:
			if not ctx:
				return False
			else:
				vote_vrfstring = committe_member+str(message.round)+str(message.voteinfo[0])
				return vrftool.verify_proof(proof, pk, vote_vrfstring)




	def get_seed(self,current_round):

		seed = self.chain.chain[current_round-1].seed
		if current_round>1:
			seed = seed.decode('utf-8')

		return seed

	#generating new seed when proposing block, where j is the subuser index;
	def new_seed(self,current_round):
		#format round from int to bytes
		newround = str(current_round).encode('utf-8')
		seed = self.get_seed(1).encode('utf-8')
		return seed+newround

	#get number and index of qualified subusers
	#return how many subusers along with their indexes
	def sub_users(self,user_total_tokens,probs,hash):
		indexes_of_j = []
		hash = hash.decode('utf-8')
		val = bin(int(hash, 16))

		total = pow(2, 512)
		num = int(val, 2)
		hashprob = num / total

		j = 0
		flag = False

		while j < user_total_tokens:
			lower = get_bond(j, user_total_tokens, probs)
			upper = get_bond(j + 1, user_total_tokens, probs)
			if j == 0 and hashprob < lower:
				return j, indexes_of_j
			if lower <= hashprob and hashprob < upper:
				j += 1
				indexes_of_j.append(j)
				flag = True
				break
			elif hashprob < lower or hashprob >= upper:
				indexes_of_j.append(j)
				j += 1
		if not flag:
			j = 0
			indexes_of_j = []
			return j, indexes_of_j
		return j, indexes_of_j


	#  sort the max priority subuser of user
	def max_priority(self, block_hash, subuser_indexes):
		max_p = hex(0)
		max_subindex = 0
		for x in subuser_indexes:
			hashstring = block_hash.encode('utf-8')+str(x).encode('utf-8')
			hash_res = sha256(hashstring).digest().hex()

			if hash_res>max_p:
				max_p=hash_res
				max_subindex=x
		return max_p, max_subindex

	#sotre block and author
	def store_blockHash_to_proof(self,hash, proof):

		if hash not in self.blocks_and_proof.keys():
			self.blocks_and_proof[hash] = proof
