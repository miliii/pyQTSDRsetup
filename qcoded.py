import base64
from Crypto.Cipher import AES
import os
import binascii


class AESUtil:

    __BLOCK_SIZE_16 = BLOCK_SIZE_16 = AES.block_size

    @staticmethod
    def encryt(str, key, iv):
        cipher = AES.new(key, AES.MODE_ECB,iv)
        x = AESUtil.__BLOCK_SIZE_16 - (len(str) % AESUtil.__BLOCK_SIZE_16)
        if x != 0:
            str = str + chr(x)*x
        msg = cipher.encrypt(str)
        # msg = base64.urlsafe_b64encode(msg).replace('=', '')
        msg = base64.b64encode(msg)
        return msg

    @staticmethod
    def decrypt(enStr, key, iv):
        cipher = AES.new(key, AES.MODE_ECB)
        # enStr += (len(enStr) % 4)*"="
        # decryptByts = base64.urlsafe_b64decode(enStr)
        decryptByts = base64.b64decode(enStr)
        msg = cipher.decrypt(decryptByts)
        paddingLen = ord(msg[len(msg)-1])
        return msg[0:-paddingLen]



def deQCode(key ,text):
    msg = base64.b64decode(text)
    cipher = AES.new(key,AES.MODE_ECB)
    rt = cipher.decrypt(msg)
    rt = rt.split(b'"')
    rt = rt[1].decode("utf8")
    return rt

if __name__ == "__main__":




    txt = "ZGcydnBXaEJnZWZRZjlNZ1dVN01QSjZwZjMrUGZpcStIZTBEeXBRYmEzY2o0VUhzNVFYN1dPUXlJL00rb3AwUGZ2aQ=="
    msg = base64.b64decode(txt)
    bmsg = bytearray(msg)
    bmsg.pop(len(bmsg)-1)
    bmsg.pop(17)
    bmsg.pop(8)
    print(bmsg)
    #decryptByts = base64.b64decode(bmsg)
    key = b"A1001..........."
    res = deQCode(key,bmsg)

    print(res)