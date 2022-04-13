import json
import requests
import hashlib

#this method is implemented with read api, instead of downloadfile api
def download(folderid,name,username,password,file_path,max_len=65535):
    session_upload=requests.Session()
    res=session_upload.get(url='https://api.pcloud.com/getdigest')
    auth=json.loads(res.text)
    digest=auth['digest']
    passworddigest=hashlib.sha1((password+hashlib.sha1(username.encode('utf-8')).hexdigest()+digest).encode('utf-8')).hexdigest()

    res=session_upload.post(url='https://api.pcloud.com/file_open?getauth=1',
        data={'flags':0x40,'folderid':folderid,'name':name,
        'username':username,'digest':digest,'passworddigest':passworddigest})

    fmeta=json.loads(res.text)
    fd=fmeta['fd']
    with open(file_path,'wb') as f:
        while(True):
            res=session_upload.post(url='https://api.pcloud.com/file_read?getauth=1',
                data={'fd':fd,'count':max_len,
                'username':username,'digest':digest,'passworddigest':passworddigest})
            #print(res.text)
            f.write(res.content)
            if(len(res.content)<max_len):
                break

def upload(folderid,name,username,password,file_path):
    session_upload=requests.Session()
    res=session_upload.get(url='https://api.pcloud.com/getdigest')
    auth=json.loads(res.text)
    digest=auth['digest']
    passworddigest=hashlib.sha1((password+hashlib.sha1(username.encode('utf-8')).hexdigest()+digest).encode('utf-8')).hexdigest()

    res=session_upload.post(url='https://api.pcloud.com/file_open?getauth=1',
        data={'flags':0x40,'folderid':folderid,'name':name,
        'username':username,'digest':digest,'passworddigest':passworddigest})

    fmeta=json.loads(res.text)
    fd=fmeta['fd']
    with open(file_path,'rb') as f:
        content=f.read()
        res=session_upload.post(url='https://api.pcloud.com/file_write?getauth=1',
            data={'fd':fd,
            'username':username,'digest':digest,'passworddigest':passworddigest},
            files={name:content})
        #print(res.text)

def uploadfile(folderid,name,username,password,file_path):
    session_upload=requests.Session()
    res=session_upload.get(url='https://api.pcloud.com/getdigest')
    auth=json.loads(res.text)
    digest=auth['digest']
    passworddigest=hashlib.sha1((password+hashlib.sha1(username.encode('utf-8')).hexdigest()+digest).encode('utf-8')).hexdigest()

    with open(file_path,'rb') as f:
        res=session_upload.post(url='https://api.pcloud.com/uploadfile?getauth=1',
            data={'folderid':folderid,
            'username':username,'digest':digest,'passworddigest':passworddigest},
            files={name:f.read()})
        #print(res.text)

def read(folderid,name,username,password,max_len=65535):
    session_upload=requests.Session()
    res=session_upload.get(url='https://api.pcloud.com/getdigest')
    auth=json.loads(res.text)
    digest=auth['digest']
    passworddigest=hashlib.sha1((password+hashlib.sha1(username.encode('utf-8')).hexdigest()+digest).encode('utf-8')).hexdigest()

    res=session_upload.post(url='https://api.pcloud.com/file_open?getauth=1',
        data={'flags':0x40,'folderid':folderid,'name':name,
        'username':username,'digest':digest,'passworddigest':passworddigest})

    fmeta=json.loads(res.text)
    fd=fmeta['fd']
    ret=''
    while(True):
        res=session_upload.post(url='https://api.pcloud.com/file_read?getauth=1',
            data={'fd':fd,'count':max_len,
            'username':username,'digest':digest,'passworddigest':passworddigest})
        #print(res.text)
        ret+=res.text
        if(len(res.text)<max_len):
            break
    return ret

def write(folderid,name,username,password,content):
    session_upload=requests.Session()
    res=session_upload.get(url='https://api.pcloud.com/getdigest')
    auth=json.loads(res.text)
    digest=auth['digest']
    passworddigest=hashlib.sha1((password+hashlib.sha1(username.encode('utf-8')).hexdigest()+digest).encode('utf-8')).hexdigest()

    res=session_upload.post(url='https://api.pcloud.com/file_open?getauth=1',
        data={'flags':0x242,'folderid':folderid,'name':name,
        'username':username,'digest':digest,'passworddigest':passworddigest})

    fmeta=json.loads(res.text)
    fd=fmeta['fd']
    res=session_upload.post(url='https://api.pcloud.com/file_write?getauth=1',
        data={'fd':fd,
        'username':username,'digest':digest,'passworddigest':passworddigest},
        files={name:content})
    #print(res.text)
