#!/usr/bin/python3
# DNS record updater for NSD by H.Shirouzu 2019/09/02 (update 2020/01/25)

import os
import sys
import re
import socket
import time

RELOAD_CMD = "/usr/sbin/nsd-control reload"

def new_serial(old_s):
	cur_val = int(old_s)
	new_s = time.strftime("%Y%m%d00").encode("utf8")
	new_val = int(new_s)
	if new_val >= cur_val * 10:
		new_s = b'%d' % (cur_val + 1)
	elif new_val <= cur_val:
		new_s = b'%10d' % (cur_val + 1)
	return new_s

def main(zone, name="", val=""):
	if val == "src":
		rec = b'A'
		val = os.environ["SSH_CONNECTION"].split()[0]
	elif val.find("txt=") >= 0:
		rec = b'TXT'
		val = val[4:]
	elif val.find(":") >= 0:
		rec = b'AAAA'
		socket.inet_pton(socket.AF_INET6, val) # verify only
	elif name != "":
		rec = b'A'
		socket.inet_pton(socket.AF_INET, val) # verify only

	val = val.encode("utf8")
	name = name.encode("utf8")

	d = open(zone, "rb").read()

	# シリアル更新
	serial_re = re.compile(rb'(IN[ \t]+SOA[^(]+\([ \t\n]*)([0-9]+)([ \t;])', re.I)
	m = serial_re.search(d)
	if not m:
		raise Exception("serial not found")
	serial = new_serial(m.groups()[1])
	d = serial_re.sub(rb'\g<1>%s\g<3>' % serial, d, 1)

	# ターゲット検索
	if name:
		dyn_re = re.compile(rb'(\n%s[ \t]+[ \t0-9]*IN[ \t]+%s[ \t]+)([0-9a-z.:_\-]+)([^\n]*\n)' % (re.escape(name), rec), re.I)
		m = dyn_re.search(d)
		if not m:
			raise Exception("host not found")

		old_val = m.groups()[1]
		if old_val == val:
			raise Exception("not modified")

		d = dyn_re.sub(rb'\g<1>%s\g<3>' % val, d, 1)
	else:
		old_val = m.groups()[1]
		val = serial

	open(zone, "wb").write(d)
	if RELOAD_CMD:
		os.system(RELOAD_CMD)
	print((b"done(%s) %s -> %s" % (serial, old_val, val)).decode("utf8"))

if __name__ == "__main__":
	try:
		if len(sys.argv) < 2 or not os.access(sys.argv[-1], os.F_OK):
			raise Exception("usage: nsd-upd.py [hostname (ipaddr|'src'|txt=val)] zone_file")

		if len(sys.argv) == 2:
			main(sys.argv[-1])
		else:
			main(sys.argv[-1], sys.argv[1], sys.argv[2])
		sys.exit(0)

	except Exception as e:
		print(e)
		sys.exit(-1)

