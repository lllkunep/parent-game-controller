from models import *
from modules.db.db_adapter import DbAdapter

def main():
	pass

if __name__ == '__main__':
	adapter = DbAdapter.init('gpucontrol.db')
	main()
	adapter.close()