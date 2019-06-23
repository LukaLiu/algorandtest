import numpy as np
import os



def generate_block_delays(num_nodes):
	dirpath = os.path.dirname(os.path.abspath(__file__))
	filepath = 'delaydatas/bitcoinblockdelay.csv'
	folder_path = os.path.join(dirpath, filepath)

	btc_data = np.genfromtxt(folder_path, delimiter=',')

	delays = [i for i in range(0, 30000)]
	probs = [btc_data[i][3] for i in delays]
	freq = [btc_data[i][2] for i in delays]

	probs = np.array(probs)
	#freq = np.array(freq)
	probs /= probs.sum()

	samples = np.random.choice(delays, 10000, replace=True, p=probs)

	return samples