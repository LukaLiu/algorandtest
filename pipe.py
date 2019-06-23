import simpy
import pysnooper


class Gossip_Pipe(object):

	def __init__(self,env,capacity=simpy.core.Infinity):
		self.env =env
		self.capacity = capacity
		self.pipe=simpy.Store(self.env,self.capacity)




class Node(object):

	def __init__(self,env,id):
		self.env = env
		self.id = id
		self.Gossip_Pipes = []

	def Gossip(self,msg):
		if not self.Gossip_Pipes:
			raise RuntimeError('no peers connected')
		events = [Pipe.pipe.put(msg) for Pipe in self.Gossip_Pipes]
		return self.env.all_of(events)

	def New_Pipe(self,Gossip_Pipe):

		self.Gossip_Pipes.append(Gossip_Pipe)
		print(f'node {self.id} added pipe {Gossip_Pipe} tp G_Pipes {self.Gossip_Pipes}')
		return Gossip_Pipe

	def Generator(self):
		round = 1
		print('generator call')
		while True:

			print(f"In round {round} node {self.id} sent out hello msg at time{self.env.now}")
			msg = (self.env.now, f'{self.id} said hello at {self.env.now}')
			self.Gossip(msg)

			yield self.env.timeout(1)
			round+=1

	def Gossip_out(self):
		return

	def Consumer(self, inpipe):
		print(f'node {self.id} consumer activated')
		while True:

			msg = yield inpipe.pipe.get()

			yield self.env.timeout(1)
			print(f'node {self.id} reciever got gossip {msg[1]} sendt again at time {msg[0]} ')
			newmsg = (self.env.now, f'node {self.id}  gosip msg created at {msg[0]} resent at time{self.env.now}')

			self.Gossip(newmsg)
			#print(f'in reciever {self.id} after put the pipe is {self.Gossip.pipe.items} at time {self.env.now}')



def run():
	env=simpy.Environment()
	node1=Node(env,1)
	node2=Node(env,2)
	node3 = Node(env,3)
	print('nodes initialize finshed')
	env.process(node1.Generator())

	env.process(node2.Consumer(node1.New_Pipe(Gossip_Pipe(env))))
	env.process(node3.Consumer(node1.New_Pipe(Gossip_Pipe(env))))

	env.process(node2.Generator())

	env.process(node1.Consumer(node2.New_Pipe(Gossip_Pipe(env))))
	env.process(node3.Consumer(node2.New_Pipe(Gossip_Pipe(env))))

	env.process(node3.Generator())

	env.process(node1.Consumer(node3.New_Pipe(Gossip_Pipe(env))))
	env.process(node2.Consumer(node3.New_Pipe(Gossip_Pipe(env))))
	#
	# env.process(node2.Generator())
	# env.process(node1.Consumer(node2.Gossip.pipe))
	# env.process(node3.Consumer(node2.Gossip.pipe))
	#
	# env.process(node3.Generator())
	# env.process(node1.Consumer(node3.Gossip.pipe))
	# env.process(node2.Consumer(node3.Gossip.pipe))


	env.run(until=7)

run()