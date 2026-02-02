import monitor
import sqlite3
import db
import datetime

def main():
	_db = db.Database()
	_db.init_db()

	# _db.save_process('dfsfsdfsdf')
	_db.save_process_log(1, datetime.datetime.now())

	id1 = _db.get_process_id_by_title('sadasd')
	print(id1)
	id2 = _db.get_process_id_by_title('dfsfsdfsdf')
	print(id2)

	count = _db.get_log_count_by_time(datetime.datetime.strptime('2026-02-02 18:01:18', '%Y-%m-%d %H:%M:%S'))
	print(count)

	m = monitor.Monitor()
	print(m.gpu_mem_th)
	print(m.usage_limit)
	print(m.time_limits)
	pass

if __name__ == '__main__':
	main()