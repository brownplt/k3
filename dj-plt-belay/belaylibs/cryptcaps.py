from Crypto.Cipher import AES
import base64
import os

class Crypt(object):
  BLOCKSIZE = 32
  
  def __init__(self, secret=os.urandom(BLOCKSIZE)):
    if len(secret) != self.BLOCKSIZE:
      raise Exception("Secret should be %s long, was %s" % \
              (self.BLOCKSIZE, len(secret)))
    self.secret = secret

  def prepare(self, data):
    encrypter = AES.new(self.secret, AES.MODE_CFB)
    return base64.b64encode(encrypter.encrypt(data))

  def unprepare(self, data):
    decrypter = AES.new(self.secret, AES.MODE_CFB)
    return decrypter.decrypt(base64.b64decode(data))

