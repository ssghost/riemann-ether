from Cryptodome.Hash import keccak
import warnings

from typing import Callable, cast
from ether.ether_types import EthSig

# suppress load warning
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from eth_keys import datatypes as eth_ecdsa


def keccak256(msg: bytes) -> bytes:
    '''
    Does solidity's dumb keccak

    Args:
        msg (bytes): the message to hash
    Returns:
        (bytes): the keccak256 digest
    '''
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(msg)
    return keccak_hash.digest()


def pow_mod(x: int, y: int, z: int) -> int:
    '''
    int, int, int (or float)
    returns (x^y)mod z
    '''
    number = 1
    while y:
        if y & 1:
            number = number * x % z
        y >>= 1
        x = x * x % z
    return number


def uncompress_pubkey(pubkey: bytes) -> bytes:
    '''
    takes a compressed pubkey, returns the uncompressed pubkey (64 bytes)
    '''
    p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
    parity = pubkey[0] - 2
    x = int.from_bytes(pubkey[1:], 'big')
    a = (pow_mod(x, 3, p) + 7) % p
    y = pow_mod(a, (p + 1) // 4, p)
    if y % 2 != parity:
        y = -y % p
    return (x.to_bytes(32, 'big')) + (y.to_bytes(32, 'big'))


def compress_pubkey(pubkey: bytes) -> bytes:
    '''Take a an uncompressed pubkey, return the compressed representation'''
    pub = pubkey[1:] if len(pubkey) == 65 else pubkey
    parity = (pub[-1] & 1) + 2
    compressed = bytes([parity]) + pub[:32]
    return compressed


def priv_to_pub(privkey: bytes) -> bytes:
    '''Return the pubkey that corresponds to a private key'''
    priv = eth_ecdsa.PrivateKey(privkey)
    pub = eth_ecdsa.PublicKey.from_private(private_key=priv)
    return cast(bytes, pub.to_bytes())


def pub_to_addr(pubkey: bytes) -> str:
    '''Eth addr is last 20 bytes of keccak256 of pubkey'''
    return f'0x{keccak256(pubkey)[-20:].hex()}'


def priv_to_addr(privkey: bytes) -> str:
    '''Make address from privkey'''
    return pub_to_addr(priv_to_pub(privkey))


def recover_pubkey(signature: EthSig, digest: bytes) -> bytes:
    '''Recovers the public key from a signature and message digest'''
    # bullshit in the underlying eth library
    # needs to be 0 if v is odd, 1 if v is even
    normalized_v = (signature[0] + 1) % 2
    normalized_sig = (normalized_v, signature[1], signature[2])

    sig = eth_ecdsa.Signature(vrs=normalized_sig)
    pub = sig.recover_public_key_from_msg_hash(digest)
    return cast(bytes, pub.to_bytes())


def recover_address(signature: EthSig, digest: bytes) -> str:
    return pub_to_addr(recover_pubkey(signature, digest))


def _der_minimal_int(number: int) -> bytes:
    if number < 0:
        raise ValueError('Negative number in signature')
    return number.to_bytes((number.bit_length() + 7) // 8, 'big')


def sig_to_der(signature: EthSig) -> bytes:
    '''
    0x30|b1|0x02|b2|r|0x02|b3|s
    b1 = Length of remaining data
    b2 = Length of r
    b3 = Length of s
    '''
    r = _der_minimal_int(signature[1])
    s = _der_minimal_int(signature[2])

    enc_r = bytes([0x02, len(r)]) + r
    enc_s = bytes([0x02, len(s)]) + s

    der = bytes([0x30, len(enc_r) + len(enc_s)]) + enc_r + enc_s
    return der


def sign_hash(digest: bytes, privkey: bytes) -> EthSig:
    '''Sign a digest'''
    priv = eth_ecdsa.PrivateKey(privkey)
    sig = priv.sign_msg_hash(digest)
    return cast(EthSig, sig.vrs)


def sign(
        message: bytes,
        privkey: bytes,
        algo: Callable[[bytes], bytes] = keccak256) -> EthSig:
    '''
    Gets a signature on a message digest of a message
    '''
    return sign_hash(algo(message), privkey)


def sign_message(
        message: bytes,
        privkey: bytes,
        algo: Callable[[bytes], bytes] = keccak256) -> EthSig:
    '''Sign a message using the ethereum signed message format'''
    prefixed = b''.join([b'\x19Ethereum Signed Message:\n', message])
    return sign(prefixed, privkey)
