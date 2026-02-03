import psutil
import win32serviceutil
import win32service
import win32event

def main():
	config_path = 'C:\\Windows\\System32\\drivers\\etc\\gpucontrol.ini'
	db_path = 'C:\\Windows\\System32\\drivers\\etc\\gpucontrol.db'
	print(config_path)
	print(db_path)
	pass

if __name__ == '__main__':
	main()