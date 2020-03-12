#!/usr/bin/python3
# DNS record updater for NSD by H.Shirouzu 2019/09/02 (update 2020/01/25)

import os
import sys
import re
import socket
import time
import getopt

ADD, MOD, DEL = range(3)

RELOAD_CMD = "/usr/sbin/nsd-control reload"

def get_zonename(d):
	m = re.search(rb"\$ORIGIN[ \t]+([a-z0-9-.]+)\.", d)
	if m:
		zone_name = m.groups()[0]
	else:
		m = re.search(rb"([a-z0-9-.]+)\.[ \t]+.*[ \t]SOA[ \t]+", d)
		if m:
			zone_name = m.groups()[0]

	if zone_name:
		# print(zone_name)
		return zone_name.decode("utf-8")

	raise Exception("zone name can't find")


def new_serial(old_s):
	cur_val = int(old_s)
	new_s = time.strftime("%Y%m%d00").encode("utf8")
	new_val = int(new_s)
	if new_val >= cur_val * 10:
		new_s = b'%d' % (cur_val + 1)
	elif new_val <= cur_val:
		new_s = b'%10d' % (cur_val + 1)
	return new_s

def serial_update(d):
	serial_re = re.compile(rb'(IN[ \t]+SOA[^(]+\([ \t\n]*)([0-9]+)([ \t;])', re.I)
	m = serial_re.search(d)
	if not m:
		raise Exception("serial not found")
	serial = new_serial(m.groups()[1])
	d = serial_re.sub(rb'\g<1>%s\g<3>' % serial, d, 1)
	return d, m.groups()[1], serial

def make_zone(zone_name, zone, d):
	zone_tmp = zone + ".tmp"
	open(zone_tmp, "wb").write(d)
	if os.system("nsd-checkzone %s %s" % (zone_name, zone_tmp)):
		raise Exception("invalid nsd-file(%s)" % zone_tmp)
	os.rename(zone_tmp, zone)

def modify_rec(zone, name="", val=""):
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

	# ゾーン名取得
	d = open(zone, "rb").read()
	zone_name = get_zonename(d)

	# シリアル更新
	d, old_serial, new_serial = serial_update(d)

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
		old_val = old_serial
		val = new_serial

	make_zone(zone_name, zone, d)
	if RELOAD_CMD:
		os.system(RELOAD_CMD)
	print((b"modify done(%s) %s -> %s" % (new_serial, old_val, val)).decode("utf8"))


def add_rec(rec_data, zone):
	# ゾーン名取得
	d = open(zone, "rb").read()
	zone_name = get_zonename(d)

	# シリアル更新
	d, old_serial, new_serial = serial_update(d)

	rec_data = rec_data.encode("utf8")

	d += rec_data + b"\n"

	make_zone(zone_name, zone, d)
	if RELOAD_CMD:
		os.system(RELOAD_CMD)
	print((b"add done(%s)" % new_serial).decode("utf8"))

def del_rec(rec_data, zone):
	# ゾーン名取得
	d = open(zone, "rb").read()
	zone_name = get_zonename(d)
	# シリアル更新
	d, old_serial, new_serial = serial_update(d)

	rec_data = rec_data.encode("utf8")

	sv = d
	if rec_data[-1:] != b'\n':
		rec_data += b'\n'
	d = re.sub(rec_data, b'', d)
	if d == sv:
		print("del not found")
		return

	if len(d) < 100:
		raise Exception("del illegal")

	make_zone(zone_name, zone, d)
	if RELOAD_CMD:
		os.system(RELOAD_CMD)
	print((b"del done(%s)" % new_serial).decode("utf8"))


USAGE = '''\
usage: nsd-upd.py [hostname (ipaddr|'src'|txt=val)] zone_file
       nsd-upd.py --add full-record zone_file
       nsd-upd.py --del regex-pattern zone_file
'''

if __name__ == "__main__":
	try:
		if len(sys.argv) < 2 or not os.access(sys.argv[-1], os.F_OK):
			raise Exception(USAGE)

		if   sys.argv[1] == "--add":
			add_rec(sys.argv[2], sys.argv[3])
		elif sys.argv[1] == "--del":
			del_rec(sys.argv[2], sys.argv[3])
		elif len(sys.argv) == 2:
			modify_rec(sys.argv[-1])
		else:
			modify_rec(sys.argv[-1], sys.argv[1], sys.argv[2])
		sys.exit(0)

	except Exception as e:
		print(e)
		sys.exit(-1)

