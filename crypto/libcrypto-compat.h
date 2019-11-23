/*
 * Copyright 2016 The OpenSSL Project Authors. All Rights Reserved.
 *
 * Licensed under the OpenSSL license (the "License").  You may not use
 * this file except in compliance with the License.  You can obtain a copy
 * in the file LICENSE in the source distribution or at
 * https://www.openssl.org/source/license.html
 */

#ifndef LIBCRYPTO_COMPAT_H
#define LIBCRYPTO_COMPAT_H

#include <openssl/opensslv.h> /* For OPENSSL_VERSION_NUMBER */

#if OPENSSL_VERSION_NUMBER < 0x10100000L

#include <openssl/asn1.h>
#include <openssl/bio.h>
#include <openssl/dh.h>
#include <openssl/dsa.h>
#include <openssl/ecdsa.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/rsa.h>

#include "crypto/crypto_export.h"

#ifdef __cplusplus
extern "C"
{
#endif

CRYPTO_EXPORT const unsigned char* ASN1_STRING_get0_data(const ASN1_STRING* x);

CRYPTO_EXPORT void BIO_set_data(BIO* a, void* ptr);
CRYPTO_EXPORT void* BIO_get_data(BIO* a);
CRYPTO_EXPORT void BIO_set_init(BIO* a, int init);
CRYPTO_EXPORT int BIO_get_init(BIO* a);
CRYPTO_EXPORT void BIO_set_shutdown(BIO* a, int shut);

CRYPTO_EXPORT int RSA_set0_key(RSA *r, BIGNUM *n, BIGNUM *e, BIGNUM *d);
CRYPTO_EXPORT int RSA_set0_factors(RSA *r, BIGNUM *p, BIGNUM *q);
CRYPTO_EXPORT int RSA_set0_crt_params(RSA *r, BIGNUM *dmp1, BIGNUM *dmq1, BIGNUM *iqmp);
CRYPTO_EXPORT void RSA_get0_key(const RSA *r, const BIGNUM **n, const BIGNUM **e, const BIGNUM **d);
CRYPTO_EXPORT void RSA_get0_factors(const RSA *r, const BIGNUM **p, const BIGNUM **q);
CRYPTO_EXPORT void RSA_get0_crt_params(const RSA *r, const BIGNUM **dmp1, const BIGNUM **dmq1, const BIGNUM **iqmp);

CRYPTO_EXPORT void DSA_get0_pqg(const DSA *d, const BIGNUM **p, const BIGNUM **q, const BIGNUM **g);
CRYPTO_EXPORT int DSA_set0_pqg(DSA *d, BIGNUM *p, BIGNUM *q, BIGNUM *g);
CRYPTO_EXPORT void DSA_get0_key(const DSA *d, const BIGNUM **pub_key, const BIGNUM **priv_key);
CRYPTO_EXPORT int DSA_set0_key(DSA *d, BIGNUM *pub_key, BIGNUM *priv_key);

CRYPTO_EXPORT void DSA_SIG_get0(const DSA_SIG *sig, const BIGNUM **pr, const BIGNUM **ps);
CRYPTO_EXPORT int DSA_SIG_set0(DSA_SIG *sig, BIGNUM *r, BIGNUM *s);

CRYPTO_EXPORT void ECDSA_SIG_get0(const ECDSA_SIG *sig, const BIGNUM **pr, const BIGNUM **ps);
CRYPTO_EXPORT int ECDSA_SIG_set0(ECDSA_SIG *sig, BIGNUM *r, BIGNUM *s);

CRYPTO_EXPORT void DH_get0_pqg(const DH *dh, const BIGNUM **p, const BIGNUM **q, const BIGNUM **g);
CRYPTO_EXPORT int DH_set0_pqg(DH *dh, BIGNUM *p, BIGNUM *q, BIGNUM *g);
CRYPTO_EXPORT void DH_get0_key(const DH *dh, const BIGNUM **pub_key, const BIGNUM **priv_key);
CRYPTO_EXPORT int DH_set0_key(DH *dh, BIGNUM *pub_key, BIGNUM *priv_key);
CRYPTO_EXPORT int DH_set_length(DH *dh, long length);

CRYPTO_EXPORT const unsigned char *EVP_CIPHER_CTX_iv(const EVP_CIPHER_CTX *ctx);
CRYPTO_EXPORT unsigned char *EVP_CIPHER_CTX_iv_noconst(EVP_CIPHER_CTX *ctx);
CRYPTO_EXPORT EVP_MD_CTX *EVP_MD_CTX_new(void);
CRYPTO_EXPORT void EVP_MD_CTX_free(EVP_MD_CTX *ctx);
#define EVP_CIPHER_impl_ctx_size(e) (e)->ctx_size
#define EVP_CIPHER_CTX_get_cipher_data(ctx) (ctx)->cipher_data

CRYPTO_EXPORT HMAC_CTX *HMAC_CTX_new(void);
CRYPTO_EXPORT void HMAC_CTX_free(HMAC_CTX *ctx);

#define TLS_client_method() TLSv1_2_client_method()

CRYPTO_EXPORT RSA_METHOD *RSA_meth_dup(const RSA_METHOD *meth);
CRYPTO_EXPORT int RSA_meth_set1_name(RSA_METHOD *meth, const char *name);
#define RSA_meth_get_finish(meth) (meth)->finish
CRYPTO_EXPORT int RSA_meth_set_priv_enc(RSA_METHOD *meth, int (*priv_enc) (int flen, const unsigned char *from, unsigned char *to, RSA *rsa, int padding));
CRYPTO_EXPORT int RSA_meth_set_priv_dec(RSA_METHOD *meth, int (*priv_dec) (int flen, const unsigned char *from, unsigned char *to, RSA *rsa, int padding));
CRYPTO_EXPORT int RSA_meth_set_finish(RSA_METHOD *meth, int (*finish) (RSA *rsa));
CRYPTO_EXPORT void RSA_meth_free(RSA_METHOD *meth);

CRYPTO_EXPORT int RSA_bits(const RSA *r);

CRYPTO_EXPORT RSA *EVP_PKEY_get0_RSA(EVP_PKEY *pkey);

#ifdef __cplusplus
} // extern "C"
#endif


#endif /* OPENSSL_VERSION_NUMBER */

#endif /* LIBCRYPTO_COMPAT_H */
