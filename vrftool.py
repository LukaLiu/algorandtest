from ctypes import *
import os

projectpath = os.path.dirname(os.path.abspath(__file__))
clib = "crypto_lib/vrf.so"
libpath = os.path.join(projectpath,clib)
lib = CDLL(libpath)


#return secret_key in hex
def new_sk():

	funnewsk = lib.new_sk
	funnewsk.restype = POINTER(c_char * 128)

	newsk = funnewsk().contents
	sk = bytes()

	for x in newsk:
		sk += x

	# free = lib.freemem
	# free.argtype = POINTER(c_char*128)
	# free(newsk)

	return sk

#get ppublic key from secret key
def get_pk(secret_key):

	funpk = lib.sk_to_pk
	funpk.restype=POINTER(c_char*64)
	funpk.argtype = POINTER(c_byte*128)

	newpk = funpk(secret_key).contents
	pk=bytes()

	for x in newpk:
		pk+=x

	return pk


#generate proof for certain msg
def get_proof(secret_key, message):

	#encode msg before passing to c
	message = message.encode()
	msglen = len(message)

	funproof = lib.vrf_proof
	funproof.restype=POINTER(c_char*160)
	funproof.argtype=(POINTER(c_byte*128),c_byte*msglen)

	newproof = funproof(secret_key,message).contents
	proof=bytes()
	for x in newproof:
		proof+=x

	return proof

#get the hash of the proof
def get_hash(proof):

	funhash=lib.vrf_proof_to_hash
	funhash.restype=POINTER(c_char*128)
	funhash.argtype=POINTER(c_byte*160)

	new_hash = funhash(proof).contents
	hash=bytes()

	for x in new_hash:
		hash+=x

	return hash

#verify proof with msg, 0 means vlaid
def verify_proof(proof,public_key, message, hash=None):


	message = message.encode()
	msglen = len(message)
	if not hash:
		temp=bytes()
		hash = temp*160

	funverify = lib.verify_proof
	funverify.restype = c_int
	funverify.argtype = (POINTER(c_char * 128), POINTER(c_char * 64),
	                POINTER(c_char * 160), POINTER(c_byte * msglen))

	return funverify(hash,public_key,proof,message)





