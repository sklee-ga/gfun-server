# -*- coding: utf-8 -*-

"""
AES256 Ccrypt

--- de/encrypt as like Unity3D Client Logic
e.g)
aes = new RijndaelManaged();
aes.KeySize = 256;
aes.BlockSize = 128;
aes.Mode = CipherMode.CBC;
aes.Padding = PaddingMode.PKCS7;
aes.IV =System.Text.Encoding.ASCII.GetBytes( seed_key.Substring(0, 16));
aes.Key = System.Text.Encoding.ASCII.GetBytes(seed_key);
"""

from Crypto.Cipher import AES
import base64


class AESCrypt(object):
    def __init__(self):
        self.key = 'TuYAWaWUzaga35n6be7RuprUVubreDhb'
        self.iv = self.key[:16]
        self.BLOCK_SIZE = 128
        self.PADDING = '{'

    def encode(self, text):
        aes = AES.new(self.key, AES.MODE_CBC, self.iv)
        pad = lambda s: s + (self.BLOCK_SIZE - len(s) % self.BLOCK_SIZE) * self.PADDING
        EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
        encoded = EncodeAES(aes, text)
        return encoded

    def encode_g(self, text):
        pad_text = self.pad_PKCS7(text)
        aes = AES.new(self.key, AES.MODE_CBC, self.iv)
        enc = aes.encrypt(pad_text)
        benc = base64.b64encode(enc)
        return benc

    def decode(self, text):
        aes = AES.new(self.key, AES.MODE_CBC, self.iv)
        DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(self.PADDING)
        decoded = DecodeAES(aes, text)
        return decoded

    def decode_g(self, text):
        aes = AES.new(self.key, AES.MODE_CBC, self.iv)
        bdec = base64.b64decode(text)
        dec = aes.decrypt(bdec)
        unpad_text = self.unpad_PKCS7(dec)
        return unpad_text

    @staticmethod
    def unpad_PKCS7(text):
        pattern = text[-1]
        length = ord(pattern)
        padding = pattern * length
        pattern_pos = len(text) - length

        if text[pattern_pos:] == padding:
            return text[:pattern_pos]
        else:
            return text

    @staticmethod
    def pad_PKCS7(text):
        padding = 16 - (len(text) % 16)
        pattern = chr(padding)
        return text + (pattern * padding)
