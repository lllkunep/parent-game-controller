import psutil
from db import Database

def main():
	pids = psutil.pids()
	print(pids)
	p = psutil.Process(100)
	print(p.exe())
	pass

if __name__ == '__main__':
	main()