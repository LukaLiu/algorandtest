import numpy as np
import os

def gen_delay_map():

	dirpath = os.path.dirname(os.path.abspath(__file__))
	filepath = 'delaydatas/delays.csv'
	folder_path = os.path.join(dirpath, filepath)


	my_data = np.genfromtxt(folder_path, delimiter=',',dtype=bytes)

	delays=dict()
	for x in range(1,29):
		count = 0
		ct = 0
		for delay in my_data[x]:
			if count==0:
				ct = x-1
				count+=1
			else:
				delay = delay.decode('utf-8')[:-2]

				delays.setdefault(ct,[]).append(float(delay))

	return delays

