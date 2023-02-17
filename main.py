import kivy
from kivymd.toast import toast

ERR= ''
try:
	import os
	import threading
	import requests
	import json
	import time
	from bs4 import BeautifulSoup
except Exception as ex:
	toast(str(ex))

from kivy.lang import Builder

try:
	from kivymd.uix.list import ThreeLineAvatarListItem,ImageLeftWidget
	from kivymd.uix.screen import MDScreen
	from kivymd.app import MDApp
	from kivymd.uix.button import MDFloatingActionButtonSpeedDial
	from kivy.core.clipboard import Clipboard
	from kivy.core.window import Window
except Exception as ex:
	toast(str(ex))

UI= '''
MDBoxLayout:
	orientation: "vertical"

    MDTopAppBar:
        title: "Free Chunk DL"
        
    ScrollView:
    	MDList:
    		id: dllist
    	
    	
    MDFloatingActionButton:
    	icon: "plus"
    	on_press: app.callback()
    	elevation_normal: 8
    	pos_hint: {'center_x':.9,'center_y':.2}
    	margin_bottom: 10
'''

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def printl(text):
	print(text,end='\r')

def get_info(url,key='obisoftdev2023'):
	resp = requests.get(url,json={'key':key})
	return json.loads(resp.text)


def make_session(dl):
	session = requests.Session()
	host = dl['host']
	username = dl['username']
	password = dl['password']
	sid = dl['sid']
	url = host + f'index.php/{sid}/login'
	resp = session.get(url)
	soup = BeautifulSoup(resp.text, "html.parser")
	
	csrfToken = soup.find('input',{'name':'csrfToken'})['value']
	
	payload = {}
	payload['csrfToken'] = csrfToken
	payload['source'] = ''
	payload['username'] = username
	payload['password'] = password
	payload['remember'] = '1'
	
	url += '/signIn'
	resp = session.post(url,data=payload)
	
	if resp.url!=url:
	           return session
	           
	printl('Login faild')
	return None
	
def wait_download(app,url,ichunk=0,index=0,file=None,session=None,time_start=0,time_total=0,speed=0,clock=0):
	app.dls[url].tertiary_text='getting info...'
	dl = get_info(url)
	filename = dl['filename']
	total_size = dl['filesize']
	
	ext = filename.split('.')[-1]
	try:
		icon = get_icon(ext)
		if icon !=  app.imgs[url].source and ichunk==0:
			app.imgs[url].source = icon
	except:pass
	
	if not session:
		session = make_session(dl)
	
	if not file:
		file = open(app.dlpath+'/'+dl['filename'],'wb')
	
	state = dl['state']
	
	chunks = dl['chunks']
	i = ichunk
	chunk_por = index
	while i < len(chunks):
		printl(f'download chunk {i+1}')
		chunkurl = dl['chunks'][i]
		# download chunk per chunk
		if not session:return None,0,0,None
		resp = session.get(chunkurl,stream=True)
		for chunk in resp.iter_content(1024):
			chunk_por += len(chunk)
			tcurrent = time.time() - time_start
			time_total += tcurrent
			time_start = time.time()
			speed+=len(chunk)
			clock_time = (total_size - chunk_por) / (speed)
			
			file.write(chunk)
			#progress
			try:
				app.dls[url].primary_text = filename
			except:pass
			try:
				app.dls[url].text = filename
			except:pass
			try:
				ifmt= sizeof_fmt(chunk_por)
				tfmt= sizeof_fmt(total_size)
				sfmt=sizeof_fmt(speed)
				app.dls[url].tertiary_text = f'{ifmt}/{tfmt} - {sfmt}/s'
			except:pass
			if time_total>=1:
				time_total=0
				speed=0
		i+=1
	
	if state == 'finish':
		try:
			app.dls[url].tertiary_text='download complete! - saved'
		except:pass
		return False,i,chunk_por,file,session,filename,time_start,time_total,speed,clock
	return True,i,chunk_por,file,session,filename,time_start,time_total,speed,clock

def start_dl(app,url):
		try:
			ichunk = 0
			index = 0
			file = None
			session = None
			time_start = time.time()
			time_total = 0
			speed = 0
			clock = time.time()
			while (True):
				wait,ichunk,index,file,session,filename,time_start,time_total,speed,clock = wait_download(app,url,ichunk,index,file,session,time_start,time_total,speed,clock)
				if not wait:
					break
		except Exception as ex:
			app.dls[url].tertiary_text=str(ex)
		pass

def get_icon(ext):
	if os.path.exists(ext+'.png'):
		return ext+'.png'
	if ext == 'mp4' or ext == 'mkv' or ext=='mpg' or ext == '3gp':
		return 'video.png'
	return 'doc.png'

class fchdl(MDApp):
	
	def callback(self):
		try:
			url = Clipboard.paste()
			if 'http' in url and 'chunks' in url:
				if url in self.dls:
					toast('(task exist.)')
					return
				img=ImageLeftWidget(source=get_icon(''))
				item = ThreeLineAvatarListItem(text=url,secondary_text=self.dlpath+'\n')
				item.add_widget(img)
				self.dls[url] = item
				self.imgs[url] = img
				self.root.ids.dllist.add_widget(item)
				threading.Thread(target=start_dl,args=(self,url)).start()
			else:
				toast('Not Url Copy')
		except Exception as ex:
			toast(str(ex))
	
	def load_(self):
		if True:
			    	import android
			    	from android.storage import primary_external_storage_path
			    	from android.permissions import request_permissions, Permission,check_permission
			    	def get_perms(perms):
			    			for perm in perms:
			    				try:
			    					if not check_permission(perm):
			    						return False
			    				except Exception as ex:
			    					#toast(str(ex))
			    					pass
			    			return True
			    	perms = [Permission.WRITE_EXTERNAL_STORAGE,Permission.READ_EXTERNAL_STORAGE,Permission.INTERNET]
			    	while not get_perms(perms):
			    		request_permissions(perms)
			    	self.dlpath = primary_external_storage_path() + '/' + 'Download'
			    	sdcard = ''
			    	try:
			    		sdcard=os.getenv('EXTERNAL_STORAGE')
			    	except:pass
			    	if sdcard!='':
			    		self.dlpath = sdcard+ '/' + 'Download'
			    	if '//' in self.dlpath :
			    		PATH_APP = self.dlpath.replace('//','/')
			    	if not os.path.exists(self.dlpath):
			    			os.mkdir(self.dlpath)
			    			
			    	
	def build(self):
		self.dlpath=''
		self.dls = {}
		self.imgs={}
		self.title = 'Free Chunk DL'
		try:
			self.load_()
		except Exception as ex:
			toast(str(ex))
		self.screen = Builder.load_string(UI)
		return self.screen

if __name__ == '__main__':
	fchdl().run()