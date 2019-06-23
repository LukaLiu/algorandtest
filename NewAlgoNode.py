from BlockChain import BlockChain
import vrftool
import simpy
from utils import *
from Block import Block
from hashlib import sha256
from Message import Message
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


class Pipe(object):

	def __init__(self, env, capacity = simpy.core.Infinity):

		self.env = env
		self.capacity = capacity
		self.pipe = simpy.Store(self.env, self.capacity)

class AlgoNode(object):

	def __init__(self, env, id,  honest, manual_committee_size=100):
		self.env = env
		self.id = id
		self.chain=BlockChain()

		#store peer AlgoNode for shuffling
		self.peers=list()
		self.sk = vrftool.new_sk()
		self.pk= vrftool.get_pk(self.sk)

		#sortition parameters
		self.proposers = 100
		self.manual_committee_size = manual_committee_size

		self.Pipes=[]
		self.Gossiped_Msg=[]

		self.block_candidates = dict()
		#buffer structure: round:messages
		self.Block_Proposals_Msg=dict()
		self.Vote_Msg =dict()

		self.voters=dict()
		self.vote_buffer=dict()

		self.waiting_Proposal=False
		self.waiting_block =dict()
		self.SortForC= dict()
		self.SortForB=dict()
		self.Tenative = False
		self.ReductionTime=0
		self.SortTime=0
		self.BBAtime=0
		self.filtermsgtime=0
		#set node type honest or malicious
		if honest:
			self.honest = True
		else:
			self.honest = False

	# def new_secret_key(self):
	# 	self.sk = vrftool.new_sk()
	def Connect(self, Pipe):

		self.Pipes.append(Pipe)

		return Pipe

	def Gossip_Msg(self, msg):

		if not self.Pipes:
			raise RuntimeError('There are no peer connected')

		events = [pipe.pipe.put(msg) for pipe in self.Pipes]

		return self.env.all_of(events)

	#give tokens to account
	def add_tokens(self, tokens):
		self.tokens = tokens

	#add id of new peer list, which is set as integer for convinient simulation
	def add_peers(self,id):
		if id not in self.peers:
			self.peers.append(id)







	def FixedGenerator(self):



		current_round = 1
		#manual size for committe size



		roundflag = True

		while roundflag:
			start_time = time.time()
			#print(f'node {self.id} enters round {current_round}')
			if not self.Tenative and not self.waiting_Proposal:

				empty_block = self.generate_empty_block(current_round)

				proposer = self.Sortition(self.sk, current_round, block_proposer, block_proposer_size)


				if proposer:
					self.SortForB[current_round]=True
					self.propose_block(proposer, current_round)
					print(f'node {self.id} sorted as proposer at time {self.env.now}')
					yield self.env.timeout(1)

					#print(f'node {self.id} checking incoming proposal at time {self.env.now}')
					self.process_proposal(current_round)

				else:
					print(f'node {self.id} not sorted for poposer at time {self.env.now}')
					self.SortForB[current_round]=False
					self.block_candidates[current_round]=list()
					yield self.env.timeout(1)

				if self.block_candidates[current_round]:
					#print(f'node {self.id} is proposer so timeout for 2\n')
					yield self.env.timeout(1)
				else:
					#print(f'node {self.id} not proposer so timeout for another 2\n')
					yield self.env.timeout(1)

				# f




				self.process_proposal(current_round)


				#print(f'node {self.id} block candidates after propcesing {self.block_candidates} at time {self.env.now}')


				#if still null, add empty block to it
				if not self.block_candidates[current_round]:
					self.block_candidates[current_round]=[empty_block]

				index = self.find_max_priority_proposal(current_round)

				max_prio_proposal = self.block_candidates[current_round][index].block_hash

				ctx = self.get_ctx(current_round)

				BA_result = yield self.env.process(self.BA(ctx,current_round,max_prio_proposal))
				print('end of BA')
				if BA_result[0]==Final_State:

					new_block_hash = BA_result[1]

					if new_block_hash==empty_block.block_hash:
						self.chain.chain[current_round]=empty_block
						current_round+=1
						endtime = time.time()
						print(
							f' at time {self.env.now} node {self.id} reaches final in {endtime-start_time} secs and appending empty block into chain')


					else:
						if current_round in self.block_candidates.keys():
							flag= True

							for block in self.block_candidates[current_round]:
								if block.block_hash==BA_result[1]:
									self.chain.chain[current_round]=block
									flag = False
									current_round+=1
									endtime=time.time()
									print(f'at time {self.env.now} node {self.id} reaches final in {endtime-start_time} secs and appending block into chain')


							if flag:
								print(f'node {self.id} needs to wait proposal message coming in ')
								self.waiting_Proposal=True
								self.waiting_block[current_round]= new_block_hash

				elif BA_result[0] == Tenative_State:
					self.Tenative=True
					print(f'node {self.id} reches tenative state and needs more count result')
					print(f'node {self.id} vote buffer after tenative {self.vote_buffer}')

			elif self.waiting_block:
				print(f'node {self.id} needs to wait more proposal to come in')
				break
				self.process_proposal(current_round)
				if self.block_candidates[current_round]:
					for block in self.block_candidates[current_round]:
						if block.block_hash == self.waiting_block[current_round]:
							self.chain.chain[current_round] = block
							self.waiting_Proposal=False
							self.waiting_block.clear()
				else:
					continue

			elif self.Tenative:
				print(f'node {self.id} enters tenative again')
				yield self.env.timeout(200)

				ctx = self.get_ctx(current_round)
				new_block_hash = self.CountVotes(ctx, current_round, Final_State,self.manual_committee_size)
				empty_block = self.generate_empty_block(current_round)
				if new_block_hash == empty_block.block_hash:
					self.chain.chain[current_round] = empty_block
					current_round += 1
					endtime = time.time()
					print(f'node {self.id} reaches final in {endtime-start_time} secs and appending empty block into chain')

					self.Tenative = False

				else:
					if current_round in self.block_candidates.keys():
						flag = True

						for block in self.block_candidates[current_round]:
							if block.block_hash == BA_result[1]:
								self.chain.chain[current_round] = block
								flag = False
								current_round += 1
								self.Tenative=False
								self.waiting_Proposal=False
								endtime = time.time()
								print(
									f'node {self.id} reaches final in {endtime-start_time} secs and appending block into chain')

						if flag:
							print(f'node {self.id} needs to wait proposal message coming in ')
							self.waiting_Proposal = True
							self.waiting_block[current_round] = new_block_hash
							self.Tenative=False

			if current_round == 2:
				roundflag =False


	#connect new peers, add pipes to output conn in simpy
	# Simpy Msg receiver

	def GossipReceiver(self, inpipe):


		while True:


			msg = yield inpipe.pipe.get()

			if msg not in self.Gossiped_Msg:

				self.Gossiped_Msg.append(msg)

				if msg[1].isProposal:

					round = msg[0]
					block_proposal = msg[1]

					if round in self.Block_Proposals_Msg.keys():

						if block_proposal not in self.Block_Proposals_Msg[round]:
							self.Block_Proposals_Msg[round].append(block_proposal)

					else:

						self.Block_Proposals_Msg[round]=[block_proposal]

					self.Gossip_Msg(msg)
					#print(f'node {self.id} gossip proposal late for {latency}')
					#yield self.env.timeout(latency)

				else:
					#(round, step)

					key = msg[0]

					if key in self.Vote_Msg.keys():

						if msg[1] not in self.Vote_Msg[key]:

							self.Vote_Msg[key].append(msg[1])

					else:
						self.Vote_Msg[key]=[msg[1]]

					self.Gossip_Msg(msg)
					#yield self.env.timeout(2)



			else:


				continue

		#construct votes into gossip messages
		#check if user is in committer
		#if true, construct votes and gossip the message


	def CountVotes(self,ctx, round, step, committe_size, step_thresh=None,timeout_lambda=2):

		ba_thresh = 2/3
		if step == Final_State:
			ba_thresh = 0.74

		print(f'node {self.id} counting votes for round {round} step {step}')
		key = (round, step)
		thresh_vote = ba_thresh * self.manual_committee_size
		test_thresh_vote = 2
		try:

			# processed_votemsg_index=[]

			for msg in self.Vote_Msg[key]:

				# index = self.Vote_Msg[key].index(msg)
				msg_round = msg.round
				msg_step = msg.voteinfo[0]
				msg_votes=msg.votes
				msg_owner = msg.pk

				if self.store_voters(msg_round,msg_step,msg_votes,msg_owner):

					self.store_vote(msg_round,msg_step, msg.block_hash,msg_votes)
					if self.vote_buffer[key][msg.block_hash] >=test_thresh_vote:
						return msg.block_hash
				# processed_votemsg_index.append(index)


			#clear vote_msg
			# if processed_votemsg_index:
			# 	rev_indexes = sorted(processed_votemsg_index, reverse=True)
			#
			# 	for index in rev_indexes:
			# 		self.Vote_Msg[key].pop(index
			# if key in self.vote_buffer.keys():
			# 	print(f'vote buffer {self.vote_buffer} in round{round} and step {step}')
			# 	for hash in self.vote_buffer[key]:
			# 		if self.vote_buffer[key][hash]>=test_thresh_vote:
			# 			return hash

		except KeyError as e:
			print(f'node {self.id} doesnot recived any votes msg at time {self.env.now} with error {e}')

		return False



	#@pysnooper.snoop()
	def BA(self, ctx, current_round, block_hash):


		h_block = yield self.env.process(self.Reduction(ctx, current_round, block_hash))


		print(f'node {self.id} finshed reduction')
		print(f'node {self.id} gossiped mes {len(self.Gossiped_Msg)}')

		print(f'node {self.id} calls bba')
		h_block_from_bba = yield self.env.process(self.Binary_BA(ctx,current_round,h_block))
		print(f'node{self.id} ends bba')

		final_step_committee = self.manual_committee_size

		yield self.env.timeout(2)

		print('node {self.id} beofre counting final votes')
		r = self.CountVotes(ctx, current_round,Final_State, final_step_committee)

		print(f'node {self.id} final count result {r}')
		print(f'node {self.id} result from bba {h_block_from_bba}')
		if h_block_from_bba==r:
			return (Final_State, h_block_from_bba)
		else:
			return (Tenative_State, h_block_from_bba)

	#@pysnooper.snoop()
	def Reduction(self, ctx, current_round, block_hash):
		empty_block = self.generate_empty_block(current_round)
		#step 1

		print(f'node {self.id} calls reduction at time {self.env.now}')
		reduction_step_one = 'reduction1'

		#threshnum = self.manual_committee_size
		self.Committe_vote(ctx, current_round, reduction_step_one, self.manual_committee_size, block_hash)

		yield self.env.timeout(1)

		#set for committe_size whilte testing
		print(f'node {self.id} starts couting votes at {self.env.now}')

		#step_one_result = self.CountVotes(ctx, current_round, step=reduction_step_one, committe_size=self.manual_committee_size)
		step_one_result = self.CountVotes(ctx, current_round, step=reduction_step_one,
		                                  committe_size=self.manual_committee_size)



		#start of reduction 2

		reduction_step_two='reduction2'

		print(f'node {self.id} calls reduction 2')
		if not step_one_result:
			#commitee vote for empty block


			self.Committe_vote(ctx, current_round, reduction_step_two, self.manual_committee_size, empty_block.block_hash)
			yield self.env.timeout(1)
		else:


			self.Committe_vote(ctx, current_round, reduction_step_two, self.manual_committee_size, step_one_result)
			yield self.env.timeout(1)





		#step_two_result = self.CountVotes(ctx,current_round, step=reduction_step_two,committe_size= self.manual_committee_size)
		step_two_result = self.CountVotes(ctx, current_round, step=reduction_step_two,
		                                  committe_size=self.manual_committee_size)
		if not step_two_result:

			return empty_block.block_hash
		else:

			return step_two_result




	def Binary_BA(self, ctx, round, block_hash):
		max_step = 20
		print(f'node {self.id} enters bba')
		step=1

		r = block_hash
		manual_threshold = self.manual_committee_size

		empty_block = self.generate_empty_block(round)

		while step <= max_step:
			step_prefix = 'bba'
			#yield self.env.process(self.Committe_vote(ctx, round, step_prefix+str(step), manual_threshold, r))
			self.Committe_vote(ctx, round, step_prefix + str(step), manual_threshold, r)
			yield self.env.timeout(1)

			#r = self.CountVotes(ctx,round,step_prefix+str(step),manual_threshold)
			r = self.CountVotes(ctx, round, step_prefix + str(step), manual_threshold)

			#print(f'node {self.id} check if block hash is equal to empty {r == empty_block.block_hash}')
			if not r:
				r = block_hash

			elif r != empty_block.block_hash:
				print(f'node {self.id} calling final at bba1 with hash {r}')
				for step_prime in range(step+1,step+4):

					#yield self.env.process(self.Committe_vote(ctx,round,step_prefix+str(step_prime), manual_threshold,r))
					self.Committe_vote(ctx, round, step_prefix + str(step_prime), manual_threshold, r)

				if step == 1:
					#yield self.env.process(self.Committe_vote(ctx, round, Final_State, manual_threshold, r))
					self.Committe_vote(ctx, round, Final_State, manual_threshold, r)

				return r

			step+=1


			self.Committe_vote(ctx, round, step_prefix + str(step), manual_threshold, r)


			yield self.env.timeout(1)

			#r = self.CountVotes(ctx,round,step_prefix+str(step),manual_threshold)
			r = self.CountVotes(ctx, round, step_prefix + str(step), manual_threshold)

			if not r:
				r = empty_block.block_hash
			elif r == empty_block.block_hash:
				for step_prime in range(step+1,step+4):
					#yield self.env.process(self.Committe_vote(ctx,round, step_prefix+str(step_prime),manual_threshold,r))
					self.Committe_vote(ctx, round, step_prefix + str(step_prime), manual_threshold, r)
				self.Committe_vote(ctx,round,Final_State, manual_threshold, r)
				return r

			step+=1

			#yield self.env.process(self.Committe_vote(ctx, round,step_prefix+str(step),manual_threshold,r))
			self.Committe_vote(ctx, round, step_prefix + str(step), manual_threshold, r)
			yield self.env.timeout(1)
			#r = self.CountVotes(ctx,round,step_prefix+str(step),self.manual_committee_size)
			r = self.CountVotes(ctx, round, step_prefix + str(step), self.manual_committee_size)

			if not r:

				if self.CommonCoin(ctx, round, step_prefix+str(step),manual_threshold) == 0:

					r = block_hash
				else:
					r = empty_block.block_hash

			step+=1

		return r

	def Committe_vote(self, ctx, round, step, threshold, value):

		seed, user_tokens, prev_blockhash= ctx

		role = committe_member+str(round)+str(step)

		sort_result = self.Sortition(self.sk, round, role, threshold)

		if sort_result:
			self.SortForC[(round,step)]=(True, sort_result[2])
			#value is the incoming candidate blockhash
			print(f'node {self.id} selected as committe in step {step} and round {step} with votes {sort_result[2]}')
			vote_message = Message(self.pk, round, self.tokens, value, vrf_proof=sort_result[0],isProposal=False,votes=sort_result[2])
			vote_message.add_vote_info(step, sort_result[1], prev_blockhash)

			selfvotes = vote_message.votes

			#vote_message=(self.env.now, self.pk,vote_message,self.id)
			vote_message=((round,step), vote_message)

			self.store_voters(round, step,selfvotes,self.pk)
			self.store_vote(round, step, value, selfvotes)


			self.Gossip_Msg(vote_message)
			self.Gossiped_Msg.append(vote_message)
		else:
			self.SortForC[(round,step)]=(False,0)
			self.Vote_Msg[(round,step)]=[]


	def process_proposal(self,current_round):

		if self.Block_Proposals_Msg:

			if current_round in self.Block_Proposals_Msg.keys():

				for msg in self.Block_Proposals_Msg[current_round]:
					new_candidate = msg.block
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
			else:
				self.block_candidates[current_round]=[]


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
			self.voters[key] = [(voter,votes)]
			return True

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

		proposal_msg = (current_round, block_message)
		# test message delay

		self.Gossip_Msg(proposal_msg)
		self.Gossiped_Msg.append(proposal_msg)
		print(f'node {self.id} sent out proposal msg with block hash {new_block.block_hash}for its peer at time{self.env.now}')

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

				return False
	#common coin
	def CommonCoin(self, ctx, round, step, thresh_num):
		minhash = 'f'*64

		#print('timeout for msg to coming in ')
		yield self.env.timeout(1)
		if self.Vote_Msg[(round,step)]:

			for msg in self.Vote_Msg[(round,step)]:

					js = msg.votes
					sort_hash = msg.voteinfo[1]
					for j in range(0,js):

						hash_string = sort_hash.decode('utf-8')+str(j)
						new_hash = sha256(hash_string.encode('utf-8')).digest().hex()

						if new_hash<minhash:
							minhash = new_hash

		minhash = int(minhash,16)
		#print('comming coin minhash result ', minhash%2)
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
