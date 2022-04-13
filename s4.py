from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient import errors
from oauth2client.client import OAuth2WebServerFlow
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from os import system,popen,walk
from os.path import join,isfile,exists
import requests
import time
import math
from math import pi,sqrt,sin,cos,atan2
from urllib import parse
from apiclient.http import MediaIoBaseDownload
import hashlib
from gc_api import *
import io
import cgi
import pcloud_api
import pickle
import base64

def update_uprofile():
    with open('global_uprofile_dict.json','w',encoding='utf-8') as f:
        f.write(json.dumps(global_uprofile_dict))
    pcloud_api.uploadfile(**pcloud_config,name='global_uprofile_dict.json',folderid=os.environ.get('PCLOUD_FOLDERID','None'),file_path='global_uprofile_dict.json')

def send_200_basic(target_class,s):
    target_class.send_response(200, 'ok')
    target_class.send_header('Content-Type', 'text/html; charset=UTF-8')
    target_class.end_headers()
    target_class.wfile.write(bytes(s,'utf-8'))
    target_class.connection.close()

class PostHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, 'ok')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        return
        
    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Login required\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        return
        
    def do_GET(self):
        global client_id
        global client_secret
        global scope
        global global_uprofile_dict
        global flow_dict
        global global_dn_dict
        global pcloud_config
        print(self.path)
        raw_path=self.path
        self.path=parse.unquote(self.path)
        if(self.path.find('?fbclid=')!=-1):
            self.path=self.path[:self.path.find('?fbclid=')]
            self.send_response(303)
            self.send_header('Location', parse.quote(self.path))
            self.end_headers()
            self.connection.close()
            return
        print(self.path)
        try:
            if(self.path=='/favicon.ico'):
                self.send_response(200, 'ok')
                self.send_header('Content-Type', 'image/x-icon')
                self.end_headers()
                self.wfile.write(open('favicon.ico','rb').read())
                self.connection.close()
                return
            elif(self.path=='/'):
                self.send_response(200, 'ok')
                self.send_header('Content-Type', 'text/html; charset=UTF-8')
                self.end_headers()
                with open('index.html','rb') as f:
                    self.wfile.write(f.read())
                self.connection.close()
            elif(self.path=='/auth'):
                self.send_response(200, 'ok')
                self.send_header('Content-Type', 'text/html; charset=UTF-8')
                self.end_headers()
                with open('auth.html','rb') as f:
                    self.wfile.write(f.read())
                self.connection.close()
            elif(self.path[:len('/auth_return')]=='/auth_return'):
                query = parse.urlparse(raw_path).query
                j=dict([qc.split("=") for qc in query.split("&")])
                code=j['code']
                uid=j['state'].split('-')[0]
                ident=j['state'].split('-')[1]
                pathid=j['state'].split('-')[2]
                list_protect=j['state'].split('-')[3]
                access_protect=j['state'].split('-')[4]
                flow=flow_dict[uid]
                credentials = flow.step2_exchange(code)
                flow_dict.pop(uid)
                global_uprofile_dict[uid]=dict()
                global_uprofile_dict[uid]['ident']=parse.unquote(ident)
                global_uprofile_dict[uid]['pathid']=pathid
                global_uprofile_dict[uid]['cred']={'refresh_token':credentials.refresh_token,
                        'token_uri':"https://accounts.google.com/o/oauth2/token",
                        'client_id':client_id,
                        'client_secret':client_secret}
                global_uprofile_dict[uid]['list_protect']=(True if list_protect=='True' else False)
                #list protect is disabled, because it makes the invalid token reset buggy
                global_uprofile_dict[uid]['access_protect']=(True if access_protect=='True' else False)
                update_uprofile()
                self.send_response(303)
                self.send_header('Location', '/drive/'+uid)
                self.end_headers()
                pass
            elif(self.path[:len('/drive/')]=='/drive/'):
                uid,*path_d=[x for x in self.path[len('/drive/'):].split('/') if len(x)>0]
                if(any([len(x)==0 for x in self.path[1:].split('/')])):
                    self.send_response(303)
                    self.send_header('Location', '/'+'/'.join([x for x in raw_path[1:].split('/') if len(x)>0]))
                    self.end_headers()
                    self.connection.close()
                    return
                if(uid not in global_uprofile_dict):
                    print('uid not in profile dict')
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/html; charset=UTF-8')
                    self.end_headers()
                    self.connection.shutdown(1)
                    return
                if(uid not in global_dn_dict):
                    try:
                        global_dn_dict[uid]=drive_node(id=global_uprofile_dict[uid]['pathid'],creds=Credentials(None,**global_uprofile_dict[uid]['cred']))
                    except RefreshError as e:
                        global_uprofile_dict.pop(uid)
                        try:
                            global_dn_dict.pop(uid)
                        except:
                            pass
                        update_uprofile()
                        send_200_basic(target_class=self,s='token expired')
                        return
                target_node=global_dn_dict[uid]
                for p in path_d:
                    idx=target_node.get_child_index_by_name(p)
                    if(idx<0):
                        self.send_response(404)
                        self.send_header('Content-Type', 'text/html; charset=UTF-8')
                        self.end_headers()
                        self.connection.shutdown(1)
                        return
                    target_node=target_node.child[idx]
                target_type=''
                do_access=True
                if(target_node.info['mimeType']=='application/vnd.google-apps.folder'):
                    target_type='folder'
                    if(global_uprofile_dict[uid]['list_protect']):
                        do_access=False
                        if(self.headers.get('Authorization','') == 'Basic '+global_uprofile_dict[uid]['ident']):
                            do_access=True
                        else:
                            self.do_AUTHHEAD()
                            self.wfile.write(bytes(self.headers.get('Authorization',''),'utf-8'))
                            self.wfile.write(bytes('authentication fail','utf-8'))
                            return
                else:
                    target_type='file'
                    if(global_uprofile_dict[uid]['access_protect']):
                        do_access=False
                        if(self.headers.get('Authorization','') == 'Basic '+global_uprofile_dict[uid]['ident']):
                            do_access=True
                        else:
                            self.do_AUTHHEAD()
                            self.wfile.write(bytes(self.headers.get('Authorization',''),'utf-8'))
                            self.wfile.write(bytes('authentication fail','utf-8'))
                            return
#                #by-pass for root, to invalidate token
#                if(len(path_d)==0 and target_type=='folder'):
#                    do_access=True
                if(not do_access):
                    send_200_basic(target_class=self,s='login required')
                    return
                if(target_type=='folder'):
                    k_dir=['<a href="'+'/drive/'+uid+'/'+'/'.join(path_d[:-1])+'">'+'Parent Directory'+'</a>']+['<a href="'+self.path+'/'+x.info['name']+'">'+x.info['name']+'/</a>' for x in target_node.child if x.info['mimeType']=='application/vnd.google-apps.folder']
                    k_file=['<a href="'+self.path+'/'+x.info['name']+'">'+x.info['name']+'</a>' for x in target_node.child if x.info['mimeType']!='application/vnd.google-apps.folder']
                    s='<h2>'+'/'+'/'.join(path_d)+'</h2><hr><ul>'+('<li>'+'</li><li>'.join(k_dir)+'</li>')+('<hr><li>'+'</li><li>'.join(k_file)+'</li>' if len(k_file)>0 else '')+'</ul>'
                    send_200_basic(target_class=self,s=s)
                    return
                else:
                    DRIVE = discovery.build('drive', 'v3', credentials=target_node.creds)
                    request=DRIVE.files().get_media(fileId=target_node.info['id'])
                    fh=self.wfile#io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request,chunksize=target_node.chunksize)
                    done = False
                    self.send_response(200, 'ok')
                    self.send_header('Content-Type', target_node.info['mimeType'])
                    self.send_header('Content-Length',target_node.info['size'])
                    self.end_headers()
                    while(done is False):
                        status, done = downloader.next_chunk()
#                        byte_len=fh.tell()
#                        fh.seek(0,io.SEEK_SET)
#                        chunk_2=fh.read(byte_len)
#                        self.wfile.write(chunk_2)
#                        fh.seek(0,io.SEEK_SET)
#                        #print("Download %d%%." % int(status.progress() * 100))
                    self.connection.close()
#                    fh.close()
                    return
        except RefreshError as e:
            global_uprofile_dict.pop(uid)
            try:
                global_dn_dict.pop(uid)
            except:
                pass
            update_uprofile()
            send_200_basic(target_class=self,s='token expired')
            return
        except:
            print('get error')
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=UTF-8')
            self.end_headers()
            self.connection.shutdown(1)
        return
        
    def do_POST(self):
        global client_id
        global client_secret
        global scope
        global global_uprofile_dict
        global flow_dict
        global pcloud_config
        if(self.path=='/auth'):
            try:
                ctype,pdict=cgi.parse_header(self.headers.get('Content-Type'))
                pdict['boundary']=bytes(pdict['boundary'],'utf-8')
                content_len = int(self.headers.get('Content-length'))
                pdict['CONTENT-LENGTH'] = content_len
                if(ctype=='multipart/form-data'):
                    fields=cgi.parse_multipart(self.rfile, pdict)
                    uid=fields.get('uid')[0]#equals to fields['uid'][0]
                    pathid=fields.get('pathid')[0]
                    secretkey=fields.get('secretkey')[0]
                    protection=fields.get('protect',[])
            except:
                print('Process request error')
                self.wfile.write(bytes('Error','utf-8'))
                self.connection.shutdown(1)
                return
            ident=base64.b64encode(bytes((uid+':'+secretkey),'utf-8')).decode('ascii')
            #ident=hashlib.blake2s(bytes(uid+secretkey,'ascii'),digest_size=8).hexdigest()
            if(uid not in global_uprofile_dict):
                flow = OAuth2WebServerFlow(client_id=client_id,
                                           client_secret=client_secret,
                                           scope=scope,
                                           state=uid+'-'+\
                                            ident+'-'+\
                                            pathid+'-'+\
                                            ('True' if 'list_protect' in protection else 'False')+'-'+\
                                            ('True' if 'access_protect' in protection else 'False'),
                                           redirect_uri=host_url+'/auth_return')
                flow_dict[uid]=flow
                auth_uri = flow.step1_get_authorize_url()
                self.send_response(303)
                self.send_header('Location', auth_uri)
                self.end_headers()
                self.connection.close()
                return
            else:
                if(ident==global_uprofile_dict[uid]['ident']):
                    global_uprofile_dict[uid]['pathid']=pathid
                    global_uprofile_dict[uid]['list_protect']=('list_protect' in protection)
                    global_uprofile_dict[uid]['access_protect']=('access_protect' in protection)
                    update_uprofile()
                    #for both pathid!=global_uprofile_dict[uid]['pathid'] and ==
                    try:
                        global_dn_dict[uid]=drive_node(id=global_uprofile_dict[uid]['pathid'],creds=Credentials(None,**global_uprofile_dict[uid]['cred']))
                        send_200_basic(target_class=self,s='updated')
                        return
                    except RefreshError as e:
                        global_uprofile_dict.pop(uid)
                        try:
                            global_dn_dict.pop(uid)
                        except:
                            pass
                        update_uprofile()
                        send_200_basic(target_class=self,s='token expired')
                        return
                else:
                    send_200_basic(target_class=self,s='secretkey mismatch')
                    return
            send_200_basic(target_class=self,s='nothing changed')
            return
        return
        

def StartServer():
    sever = ThreadingHTTPServer(("",int(os.environ.get('PORT',9999))),PostHandler)
    print('ready')
    sever.serve_forever()

if __name__=='__main__':
    pcloud_config={'username':str(os.environ.get('PCLOUD_UID','None')),'password':str(os.environ.get('PCLOUD_PASSWORD','None'))}
    client_id=str(os.environ.get('GD_CLIENT_ID','None'))
    client_secret=str(os.environ.get('GD_CLIENT_SECRET','None'))
    scope=str(os.environ.get('GD_SCOPE','None'))
    global_uprofile_dict=dict()
    global_dn_dict=dict()
    pcloud_api.download(**pcloud_config,name='global_uprofile_dict.json',folderid=os.environ.get('PCLOUD_FOLDERID','None'),file_path='global_uprofile_dict.json')
    with open('global_uprofile_dict.json','r',encoding='utf-8') as f:
        global_uprofile_dict=json.loads(f.read())
    flow_dict=dict()
    host_url=os.environ.get('host_url','None')
    print('port='+str(os.environ.get('PORT',9999)))
    StartServer()
