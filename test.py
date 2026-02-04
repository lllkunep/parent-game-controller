import psutil
from db import Database

def main():
	db = Database('gpucontrol.db')
	print(db.get_keywords())
	pass

if __name__ == '__main__':
	main()