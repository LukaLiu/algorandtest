import vrftool
from hashlib import sha256
import scipy.stats as ss
import random
import math
import time
string = b'a'
string2 = b'b'
hash1 = sha256(string).digest().hex()
hash2 = sha256(string2).digest().hex()
print(hash1)
max = math.pow(2,512)
h=hex(int(max))
print(h[2:])
print(len(h[3:]))
test = 'f'*64

def subuser(user_total_tokens,probs,hash):

	indexes_of_j= []
	hash = hash.decode('utf-8')
	val = bin(int(hash, 16))

	total = pow(2, 512)
	num = int(val, 2)

	hashprob = num / total

	j = 0
	flag = False
	print(hashprob)
	while j<user_total_tokens:

		lower=get_bond(j,user_total_tokens,probs)
		upper=get_bond(j+1,user_total_tokens,probs)
		print(f'lower {lower} upper{upper}')
		if j==0 and hashprob <lower:

			return j, indexes_of_j
		if lower<=hashprob and hashprob<upper:
			j+=1
			indexes_of_j.append(j)
			flag=True
			break

		elif hashprob<lower or hashprob>=upper:
			indexes_of_j.append(j)
			j+=1
	if not flag:
		j = 0
		indexes_of_j=[]
		return j, indexes_of_j
	return j, indexes_of_j

def get_bond(j,user_total,prob):
	sum =0
	while j >=0:
		sum+=ss.binom.pmf(j,user_total,prob)

		j-=1
	return sum

ms = '0x9d'
sk = vrftool.new_sk()
p = vrftool.get_proof(sk,ms)
h = vrftool.get_hash(p)
j,indexes_of_j = subuser(5, 26/100000000, h)

algolist = [vrftool.new_sk() for i in range(50000)]
hash = [vrftool.get_hash(vrftool.get_proof(sk,ms)) for sk in algolist ]
start = time.time()
count = 0
times=0
c=10
while c>0:
	for h in hash:
		times+=1
		weight =random.randint(1,500)
		print(f'counting for {h} with weight{weight}')
		j,indexes_of_j=subuser(weight, 26/1000000, h)
		if j >0:
			count+=1
		print(f'finsihed subuser counting with result j: {j} ')
	if count>1:
		print(f'{count} users have subuser')
	c-=1
endtime = time.time()
print(f'time ocst for {times} users is {start-endtime}')
