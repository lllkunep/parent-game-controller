
def main():
	aaa = {}
	try:
		aaa['a'].append(1)
		print(aaa)
	except KeyError:
		aaa['a'] = []
		aaa['a'].append(1)
	print(aaa)
	pass

if __name__ == '__main__':
	main()