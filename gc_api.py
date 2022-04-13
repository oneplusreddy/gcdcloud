from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from os import system,popen,walk
from os.path import join,isfile,exists
from apiclient import errors
from oauth2client.client import OAuth2WebServerFlow
from google.oauth2.credentials import Credentials
import json
from apiclient.http import MediaIoBaseDownload
import functools

class drive_node:
    def __init__(self,id=None,creds=None,info=None,spaces='drive',chunksize=32*1024*1024):
        self.spaces=spaces
        self.chunksize=chunksize
        if(creds is not None):
            self.creds=creds
        else:
            self.creds=self.get_cred()
        if(id is not None):
            self.id=id
        else:
            self.id=self.get_root_id()
        #print('init '+self.id)
        if(info is not None):
            self.info=dict(info)
        else:
            self.info=self.get_info()
        #self.child=self.get_child()
        pass
    
    def get_info(self):
        DRIVE = discovery.build('drive', 'v3', credentials=self.creds)
        request=DRIVE.files().get(fileId=self.id,fields='*')
        return request.execute()
    
    #lazy initilization to speed up construction
    @property
    @functools.lru_cache()
    def child(self):
        child_list=list()
        if(self.info['mimeType']=='application/vnd.google-apps.folder'):
            DRIVE = discovery.build('drive', 'v3', credentials=self.creds)
            request=DRIVE.files().list(spaces=self.spaces,orderBy='name_natural',pageSize=1000,fields='*',q=('\''+self.id+'\' in parents '+"and 'me' in owners"))
            while request is not None:
                files = request.execute()
                for f in files['files']:
                    child_list.append(drive_node(creds=self.creds,id=f['id'],info=f,spaces=self.spaces))
                request=DRIVE.files().list_next(previous_request=request,previous_response=files)
        else:
            pass
        for i in range(len(child_list)):
            for j in range(i+1,len(child_list)):
                if(child_list[i].info['mimeType']!='application/vnd.google-apps.folder' and child_list[j].info['mimeType']=='application/vnd.google-apps.folder'):
                    child_list[i],child_list[j]=child_list[j],child_list[i]
        return child_list
    
    def get_root_id(self):
        DRIVE = discovery.build('drive', 'v3', credentials=self.creds)
        request=DRIVE.files().list(spaces=self.spaces,q="'me' in owners",pageSize=2,fields='*')
        r=request.execute()['files'][0]
        while('parents' in r):
            r=DRIVE.files().get(fileId=r['parents'][0],fields='*').execute()
        return r['id']
    
    #these two method should be removed for release ver,
    #that is only to easily test the method correctness
    def download(self):
        DRIVE = discovery.build('drive', 'v3', credentials=self.creds)
        request=DRIVE.files().get_media(fileId=self.info['id'])
        fh=open(self.info['name'],'wb')
        downloader = MediaIoBaseDownload(fh, request,chunksize=self.chunksize)
        done = False
        while(done is False):
            status, done = downloader.next_chunk()
            #print("Download %d%%." % int(status.progress() * 100))
        fh.close()

    def ls(self):#list_child
        print('\n'.join([str(i)+':'+x.info['name'] for i,x in zip(range(len(self.child)),self.child)]))
    
    def get_child_index_by_name(self,name):
        for i,d_name in enumerate([x.info['name'] for x in self.child]):
            if(name==d_name):
                return i
        return -1
