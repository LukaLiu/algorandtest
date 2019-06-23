from ctypes import *
import base64
path='/Users/yuliu/PycharmProjects/algorandtest/crypto_lib/vrf.so'
import binascii
lib=CDLL(path)


#new_sk() working part
func = lib.new_sk
func.restype=POINTER(c_char*128)
newsk=func().contents
buff = bytes()
for x in newsk:


	buff+=x

print('\nfinal buff', buff)

#secret key to publickey
pkfunc = lib.sk_to_pk
pkfunc.restype = POINTER(c_char*64)
pkfunc.argtype = POINTER(c_char*128)

newpk = pkfunc(buff).contents
pkbuff = bytes()
for x in newpk:
	pkbuff+=x

print('public key', pkbuff)

#get proof using sk and msg
#msg have to convert to bytes before passing to c function
ms = '0x9d'
ms = ms.encode()

pffunc = lib.vrf_proof
pffunc.restype = POINTER(c_char*160)
pffunc.argtype =(POINTER(c_char*128),c_byte*len(ms))
newproof = pffunc(buff,ms).contents
proof = bytes()
for x in newproof:
	proof+=x
print("proof in python", proof)


#use proof to get the hash proof bytes 80s, output bytes 64
p2hfunc = lib.vrf_proof_to_hash
p2hfunc.restype = POINTER(c_char*128)
pffunc.argtype = POINTER(c_char*160)
newoutput = p2hfunc(proof).contents
output = bytes()
for x in newoutput:
	output+=x
print("output in python", output)

#verfigy output with pk and proof
# can verify proof by inputting empty output, valid will return 0
verifyout = lib.verify_proof
testout = bytes()*160
verifyout.restype = c_int
verifyout.argtype = (POINTER(c_char*128),POINTER(c_char*64),POINTER(c_char*160),POINTER(c_byte*len(ms)))
flag = verifyout(testout,pkbuff,proof,ms)
print(flag)



