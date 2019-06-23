class Message(object):
	# Proposal equal true
	# Vote message is false

	def __init__(self,pk, round, weight, block_hash, entire_block=None, vrf_proof=None, vrf_hash=None, priority = None, isProposal = True, votes=1):

		#proposal message
		self.pk = pk
		if isProposal:
			self.isProposal = True
			self.isVote=False
			self.priority = priority
			#block msg with entire block
			if entire_block:

				self.round = round
				self.block_hash = block_hash
				self.block = entire_block
				self.proof = vrf_proof
				self.vrf_hash = vrf_hash
				self.weight = weight


			#block msg with only priorities and proofs
			else:

				self.round = round
				self.block_hash = block_hash
				self.Priority = priority
				self.proof = vrf_proof
				self.vrf_hash = vrf_hash
				self.entire_block=False
				self.weight = weight

		else:
			# vote message
			self.round = round
			self.block_hash=block_hash
			self.isVote = True
			self.proof = vrf_proof
			self.isProposal = isProposal
			self.votes=votes
			self.pk = pk

	def add_vote_info(self,step, vrf_hash, ctx_last_block_hash):
		self.voteinfo=(step, vrf_hash, ctx_last_block_hash)
