#include <stdio.h>
#include <string.h>
#include <sodium.h>

char* to_hex( char hex[], uint8_t bin[], size_t length )
{
    int i=0;
    uint8_t *p0 = (uint8_t *)bin;
    char *p1 = hex;


    for( i = 0; i < length; i++ ) {
        snprintf( p1, 3, "%02x", *p0 );
        p0 += 1;
        p1 += 2;
    }
    //printf("");
    return hex;
}

uint8_t* hex_str_to_uint8(const char* string) {
   if (string == NULL)
        return NULL;

    size_t slength = strlen(string);
    if ((slength % 2) != 0) // must be even
        return NULL;

    size_t dlength = slength / 2;

    uint8_t* data = (uint8_t*)malloc(dlength);

    memset(data, 0, dlength);

    size_t index = 0;
    while (index < slength) {
        char c = string[index];
        int value = 0;
        if (c >= '0' && c <= '9')
            value = (c - '0');
        else if (c >= 'A' && c <= 'F')
            value = (10 + (c - 'A'));
        else if (c >= 'a' && c <= 'f')
            value = (10 + (c - 'a'));
        else
            return NULL;

        data[(index / 2)] += value << (((index + 1) % 2) * 4);

        index++;
    }

    return data;
}



//finished with generateing secret key
char* new_sk(){
    
    uint8_t public_key[crypto_sign_PUBLICKEYBYTES];
    uint8_t secret_key[crypto_sign_SECRETKEYBYTES];

    static char shexbuf[2*crypto_sign_SECRETKEYBYTES+1];
    crypto_vrf_keypair(public_key, secret_key);
    char* result;
    result = to_hex(shexbuf, secret_key, crypto_sign_SECRETKEYBYTES);
    
    return shexbuf;

}
//finsihed with getting public key using secret key
char* sk_to_pk(unsigned char *sk){
    char* raw;
    raw = hex_str_to_uint8(sk);
    uint8_t public_key[crypto_vrf_PUBLICKEYBYTES];
    crypto_vrf_sk_to_pk(public_key, raw);
    static char pkbuf[2*crypto_vrf_PUBLICKEYBYTES+1];
    char* result;
    result =to_hex(pkbuf, public_key,  crypto_vrf_PUBLICKEYBYTES);
    free(raw);
    return pkbuf;
}

char* s_to_p(unsigned char *raw){

    uint8_t public_key[crypto_vrf_PUBLICKEYBYTES];
    crypto_vrf_sk_to_pk(public_key, raw);
    static char pkbuf[2*crypto_vrf_PUBLICKEYBYTES+1];
    char* result;
    result = to_hex(pkbuf, public_key,  crypto_vrf_PUBLICKEYBYTES);
    free(raw);

    return pkbuf;
}

char* vrf_proof(const unsigned char *sk, const unsigned char *msg){
    unsigned long long msgle;
    msgle = strlen(msg);
    char* rawsk;
   //rawsk = hex_str_to_uint8(sk);
    rawsk = hex_str_to_uint8(sk);
//    unsigned char *testmsg = "0x9d";
//    unsigned long long testmsgle;
//    testmsgle = strlen(testmsg);
    unsigned char* proof[crypto_vrf_PROOFBYTES];
//    unsigned char* testproof[crypto_vrf_PROOFBYTES];
    crypto_vrf_prove(proof, rawsk, msg, msgle);

//    crypto_vrf_prove(testproof, rawsk, testmsg, testmsgle);
    char proofbuf[2*crypto_vrf_PROOFBYTES+1];
    
    to_hex(proofbuf, proof, crypto_vrf_PROOFBYTES);
    
    free(rawsk);
    return proofbuf;
}

char* vrf_proof_to_hash(unsigned char* proof){
    char*rawproof;
    rawproof = hex_str_to_uint8(proof);

    char*output[crypto_vrf_OUTPUTBYTES];
    
    static char* hexoutput[2*crypto_vrf_OUTPUTBYTES+1];
    int i = crypto_vrf_ietfdraft03_proof_to_hash(output, rawproof);


    char* result;
    result = to_hex(hexoutput, output, crypto_vrf_OUTPUTBYTES);
	
	free(rawproof);
    return hexoutput;

}

int verify_proof(unsigned char *output, const unsigned char *pk,
                 const unsigned char *proof, const unsigned char *m){
    unsigned long long msglen;
    msglen = strlen(m);

    char* rawoutput;
    char* rawpk;
    char* rawproof;

    rawoutput = hex_str_to_uint8(output);
    rawpk = hex_str_to_uint8(pk);
    rawproof = hex_str_to_uint8(proof);


    return 0;
}

