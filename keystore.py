#!/user/bin/python

'''
   Copyright (c) 2016 Rory Hool
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
   
       http://www.apache.org/licenses/LICENSE-2.0
   
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import os

from simplekv.fs import FilesystemStore

directory = 'keystore'

def make_directory():
    if not os.path.exists(directory):
        os.makedirs(directory)

def contains(key):
    make_directory()
    store = FilesystemStore(directory)
    return store.__contains__(key)

def get(key):
    make_directory()
    store = FilesystemStore(directory)
    if contains(key):
        return store.get(key)

    return None

def put(key, value):
    make_directory()
    store = FilesystemStore(directory)
    store.put(key, str(value))

def delete(key):
    make_directory()
    store = FilesystemStore(directory)
    store.delete(key)
