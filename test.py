import vrftool
import math
import binascii
newsk = vrftool.new_sk()
print(newsk)
newpk=vrftool.get_pk(newsk)
print(newpk)
ms = '0x9d'
newproof = vrftool.get_proof(newsk,ms)
print(newproof)
newhash = vrftool.get_hash(newproof)
print(newhash)

flag = vrftool.verify_proof(newproof,newpk,ms,newhash)
print(flag)

hash = newhash.decode('utf-8')
print(hash)
val = bin(int(hash,16))
total = pow(2,len(val))
num = int(val,2)
print(num)
print(total)
hashres = num/total
user_total_tokens=5
total = 100

prob = 0.2

#factorial function
def factorial(num):
	if num <2:
		return 1
	else:
		return num*factorial(num-1)

#caculate binominal probability
def binominal(k,n,p):
	pk=math.pow(p,k)
	pk_prime = math.pow((1-p),(n-k))
	factor= factorial(n)/(factorial(k)*factorial(n-k))

	return factor*pk*pk_prime

#caculate_bond, which is the sum of binominal probs
def cal_bond(bond, total_tokens, probability):
	result=0
	for x in bond:
		result+=binominal(x,total_tokens, probability)
	return result

#calculate binominal boundary for verification
def bino_bond(user_total_tokens, prob):

	#bonds for binomial boundary
	bonds = []

	# new_j to be used to caculate binomial boundary
	j=[[num for num in range(x+1)] for x in range(user_total_tokens+1)]
	new_j=[(j[x],j[x+1]) for x in range(len(j)-1)]

	for element in new_j:
		right,left = element
		bond = (cal_bond(right,user_total_tokens, prob),cal_bond(left,user_total_tokens,prob))
		bonds.append(bond)

	return bonds

def get_subusers():

	return

import vrftool
import binascii
sk = vrftool.new_sk()
msg='hello'
proof = vrftool.get_proof(sk,msg)

from treelib import tree


class Node(object):

	def __init__(self,id):
		self.id = id
		self.peers =set()
		self.peer_limit=4

	def full_connected(self):
		if len(self.peers)==self.peer_limit:
			return True
		else:
			return False

	def add_peer(self,id):

		if not self.full_connected():
			self.peers.add(id)
		else:
			return False



nodes = [Node(i) for i in range(10)]



