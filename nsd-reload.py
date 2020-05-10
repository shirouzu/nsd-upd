#!/usr/bin/python3
# NSD check and reload by H.Shirouzu 2020/02/26 (update 2020/02/26)

import os

CONF_FILE = "/etc/nsd/nsd.conf"
ZONE_DIR = "/etc/nsd/zones"

def main():
	if os.system("nsd-checkconf %s" % CONF_FILE) != 0:
		raise Exception("conf check error(%s)" % CONF_FILE)

	os.chdir(ZONE_DIR)
	for z in os.listdir("."):
		if os.system("nsd-checkzone %s %s" % (z, z)) != 0:
			raise Exception("zone check error(%s)" % z)

	if os.system("nsd-control reload") != 0:
		raise Exception("reload error")

if __name__ == '__main__':
	try:
		print("nsd-reload start...\n")
		main()
		print("nsd-reload OK")
	except Exception as e:
		print("\n%s" % e)

