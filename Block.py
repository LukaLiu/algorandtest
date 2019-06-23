import ed25519
from hashlib import sha256

NULL_HASH = b'0'*64

default_sk = b'413a67a03a4da74902bc061429a2a7b63425b55cad6f31ede3e6764c2374c8254265c247c6b2583b2c49a868c63b910181d315646d486e4b193d89a6152bf996'
default_sk= default_sk.decode('utf-8')
b=bytes.fromhex(default_sk)

default_sk = ed25519.SigningKey(b)


#signk = ed25519.SigningKey(default_sk)
class Block(object):

	def __init__(self, round, prev_hash, author=None,
	             author_proof=None,seed=None, genius = False, bhash=None, isEmpty=False):
		if genius:
			self.isGenius = True
			self.gen_gen_block()
		elif isEmpty:
			self.isEmpty=True
			self.round = round
			self.prev_hash= prev_hash
			self.block_hash=NULL_HASH.hex()
			self.author = author
			self.author_proof=author_proof
			self.seed = seed
			self.isGenius = False
			self.gen_bhash()

		else:
			self.round=round
			self.prev_hash = prev_hash
			self.author = author
			self.author_proof = author_proof
			self.seed = seed
			self.block_hash=bhash
			self.isGenius=False
			self.isEmpty=False

	#field to store transactions, implementation TBD
	#genenerate genius block
	def gen_gen_block(self):
		self.round = 0
		self.prev_hash=NULL_HASH
		self.author = None
		self.author_proof=None
		self.signature = default_sk.sign(self.prev_hash)
		signstring = self.prev_hash+self.signature
		self.block_hash = sha256(signstring).digest().hex()
		self.seed = self.block_hash
		# self.isGenius=True

	def get_previous(self):
		return self.prev_hash

	def add_priority(self,priority):
		self.priority = priority
	#set block hash, node sign it manually

	def gen_bhash(self):


		if type(self.prev_hash) is bytes:
			hashstring = self.prev_hash+ self.author + self.author_proof+bytes(self.round)
		else:
			hashstring = self.prev_hash.encode('utf-8') + self.author + self.author_proof+bytes(self.round)
		self.block_hash = sha256(hashstring).digest().hex()

