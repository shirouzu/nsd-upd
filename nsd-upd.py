#!/usr/bin/python3
# DNS record updater for NSD by H.Shirouzu 2019/09/02

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

def main(name, addr, zone):
	if addr == "src":
		addr = os.environ["SSH_CONNECTION"].split()[0]

	if addr.find(":") >= 0:
		rec = b'AAAA'
		socket.inet_pton(socket.AF_INET6, addr)
	else:
		rec = b'A'
		socket.inet_pton(socket.AF_INET, addr)

	addr = addr.encode("utf8")
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
	dyn_re = re.compile(rb'(\n%s[ \t]+[ \t0-9]*IN[ \t]+%s[ \t]+)([0-9a-f.:]+)([^\n]*\n)' % (re.escape(name), rec), re.I)
	m = dyn_re.search(d)
	if not m:
		raise Exception("host not found")

	old_addr = m.groups()[1]
	if old_addr == addr:
		raise Exception("not modified")

	d = dyn_re.sub(rb'\g<1>%s\g<3>' % addr, d, 1)

	open(zone, "wb").write(d)
	if RELOAD_CMD:
		os.system(RELOAD_CMD)
	print((b"done(%s) %s -> %s" % (serial, old_addr, addr)).decode("utf8"))

if __name__ == "__main__":
	try:
		if len(sys.argv) < 4:
			raise Exception("usage: nsd-upd.py hostname (ipaddr|'src') zone_file")
		main(sys.argv[1], sys.argv[2], sys.argv[3])
		sys.exit(0)

	except Exception as e:
		print(e)
		sys.exit(-1)

