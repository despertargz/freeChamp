__author__ = 'S70rmCrow'
import os, hashlib

def securePw(salt, pw):
    hash = hashlib.sha512()
    hash.update(salt + pw)
    return hash.hexdigest()