import math
from math import factorial as fac
import scipy.stats as ss
#factorial function

# fac(n) / (fac(k) * fac(n - k)) * p**k * (1-p)**(n-k)
#caculate binominal probability
def binominal(k,n,p):
	return ss.binom.pmf(k,n,p)

#caculate_right or left bondary, which is the sum of binominal probs
def cal_bond(bond, total_tokens, probability):
	result=0
	for x in bond:
		result+=binominal(x,total_tokens, probability)
	return result

#calculate binominal boundary for verification
#input total numbers of user's tokens, and probability of that round
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

def get_bond(j,user_total,prob):
	sum = 0
	while j >= 0:
		sum += ss.binom.pmf(j, user_total, prob)
		j -= 1
	return sum
