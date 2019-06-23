from Block import Block
class BlockChain(object):

	def __init__(self):

		#storeing blocks
		#key is round, value is block
		self.chain=dict()
		self.gen_gen_block()
		#record the heights, which named rounds in algorand
		self.rounds=max(self.chain.keys())
		self.total_tokens = 10000

	#set total tokens in simulation
	def set_total_toknes(self, number_of_tokens):
		self.total_tokens = number_of_tokens

	#generate genius block
	def gen_gen_block(self):
		self.chain[0] = Block(0,0,0,0,0,genius=True)

	def last_round(self):

		return self.chain[self.rounds]

	def add_block(self,block):

		return
