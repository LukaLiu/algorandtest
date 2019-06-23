import vrftool
import math
from utils import bino_bond
import random
subusers = 200
total_tokens = 10000
thresh=2/3
prob=subusers/total_tokens
nodes=[vrftool.new_sk() for x in range(100)]
ms = '0x9d'
proofs=[vrftool.get_proof(node, ms) for node in nodes]
hash =[vrftool.get_hash(proof) for proof in proofs]
p = vrftool.get_proof(nodes[0],ms)
h = vrftool.get_hash(p)
print('vrfproof length', len(p))
print('vrfhash lenthg', len(h), h)
user_tokens=[100 for x in range(100)]


def subusers(user_total_tokens, probs, hash):
	print(hash)
	bonds = bino_bond(user_total_tokens, probs)
	js=0
	hash = hash.decode('utf-8')
	val = bin(int(hash,16))

	total = pow(2,512)
	num = int(val,2)
	hashprob = num/total
	print(hashprob)
	flag=True
	print(hashprob)
	indexes_of_j=[]
	j = 0
	for bond in bonds:
		j+=1

		low, up = bond

		if hashprob>=low and hashprob<=up:
			js=j
			indexes_of_j.append(j)
			break
		indexes_of_j.append(j)
	if js>0:
		print("selected user subusers:",j)

	return js, indexes_of_j
js=[]
pr = 30/100000

for x in range(100):
	js.append(subusers(user_tokens[x], pr, hash[x]))
count=0
for x in js:
	if x[0]!=0:
		count+=x[0]
		print(x[0], ' and ', x[1])
print('count ', count)
