from AlgoNode import AlgoNode
import random
import simpy

users =[AlgoNode(x, True) for x in range(10)]
Simulated_Rounds = 2
role1 = hex(1)
print(role1)
print(bytes(role1,'utf-8'))

while True:
	count = 0
	total_tokens_sys = 0
	for user in users:
		user.run()
		user.add_tokens(random.randint(0,1001))
		total_tokens_sys+=user.tokens


	if count ==0:
		break
	#First Sort BlockProposer and propose block and nodes sort committee

	#

