#!/usr/bin/python
# For license information, look at LICENSE file in this folder

#This file creates a catalog.bin file which contains
#information about the nest units and events supported
#by the custom microcode.
#
#Catalog.bin creation is coupled with custom microcde.
#Any changes in the custom microcode units or events
#should reflect here.
#
#In the op-build, when creating pnor, this script is executed
#to create a catalog.bin file and then same is added with ECC
#and flashed to a new partition called "Catalog"

import sys, getopt
import struct
import binascii
import ctypes
from array import array

##Global varibales
group_list = []
event_list = []
outfile_dir = ""


##Catalog structures are formed based on the information here,
#
#  https://raw.githubusercontent.com/jmesmon/catalog-24x7/master/hv-24x7-catalog.h
#
class Events:
	def __init__(self, domain, start, length, offset,flag, index, g_cnt, string):
		self.domain = domain
		self.start = start
		self.length = length
		self.offset = offset
		self.flag = flag
		self.index = index
		self.g_cnt = g_cnt
		self.string = string
		self.str_len = len(string)

		self.s_format = "B s H H H I H H H " + str(self.str_len) + "s"
		self.s_var = struct.Struct("> " + self.s_format)
		self.s_val = (self.domain, " ", self.start, self.length,\
				 self.offset, self.flag, self.index, \
					self.g_cnt, self.str_len, self.string)
		self.s_cty = ctypes.create_string_buffer(self.s_var.size)
		self.s_var.pack_into(self.s_cty, 0, *self.s_val)

		self.l_format = "> H 2s "+ self.s_format
		self.l_var = struct.Struct(self.l_format)
		self.l_val = (self.l_var.size, "  ", self.domain, " ",\
				self.start, self.length, self.offset, \
				self.flag, self.index, self.g_cnt, \
				self.str_len, self.string)
		self.l_cty = ctypes.create_string_buffer(self.l_var.size)
		self.l_var.pack_into(self.l_cty, 0,  *self.l_val)
		#print 'Unpacked:', self.l_var.unpack_from(self.l_cty, 0)
		#print 'Raw:', binascii.hexlify(self.l_cty.raw)
		event_list.append(self.l_cty.raw)

class Groups:
	def __init__(self, flag, domain, start, length, index, ecnt, gname, earr):
		self.flag = flag
		self.domain = domain
		self.start = start
		self.length = length
		self.index = index
		self.ecnt = ecnt
		self.earr = earr
		self.grp_name = gname
		self.grp_name_len = len(gname)

		self.s_format = "I B s H H B B H H H H H H H H H H H H H H H H H " + str(self.grp_name_len) + "s"
		self.s_var = struct.Struct("> " + self.s_format)
		self.s_val = (self.flag, self.domain, " ",self.start, self.length,\
				self.index, self.ecnt, self.earr[0], self.earr[1],\
				self.earr[2], self.earr[3], self.earr[4], self.earr[5],\
				self.earr[6], self.earr[7], self.earr[8], self.earr[9],\
				self.earr[10], self.earr[11], self.earr[12], self.earr[13],\
				self.earr[14], self.earr[15], self.grp_name_len, self.grp_name)
		self.s_cty = ctypes.create_string_buffer(self.s_var.size)
		self.s_var.pack_into(self.s_cty, 0, *self.s_val)
		#print 'Unpacked:', self.s_var.unpack_from(self.s_cty, 0)

		self.l_format = "> H 2s "+ self.s_format
		self.l_var = struct.Struct(self.l_format)
		self.l_val = (self.l_var.size, "  ", self.flag, self.domain,\
				" ", self.start, self.length, self.index,\
				self.ecnt, self.earr[0], self.earr[1], self.earr[2],\
				self.earr[3], self.earr[4], self.earr[5], self.earr[6],\
				self.earr[7], self.earr[8], self.earr[9], self.earr[10],\
				self.earr[11], self.earr[12], self.earr[13], self.earr[14],\
				self.earr[15], self.grp_name_len, self.grp_name)
		self.l_cty = ctypes.create_string_buffer(self.l_var.size)
		self.l_var.pack_into(self.l_cty, 0,  *self.l_val)
		#print 'Unpacked:', self.l_var.unpack_from(self.l_cty, 0)
		#print 'Raw:', binascii.hexlify(self.l_cty.raw)
		group_list.append(self.l_cty.raw)

class Page0:
	def __init__(self, ver, date_str):
		self.magic = 0x32347837
		self.ver = ver
		self.date_str = date_str
		self.schema_offset = 0
		self.schema_len = 0
		self.schema_ecnt = 0
		self.event_offset = 1
		self.event_len = 0
		self.event_ecnt = 0
		self.group_offset = 0
		self.group_len = 0
		self.group_ecnt = 0
		self.form_offset = 0
		self.form_len = 0
		self.form_ecnt = 0
		self.es_32 = "                                "
		self.es_8 = "        "
		self.total_events_size = 0
		self.total_group_size = 0
		self.total_grp_events_pages = 1
		self.catalog_len = 0
		self.event_fill = 0
		self.group_fill = 0
		self.page0_fill = 0

		for i in event_list:
			self.total_events_size += len(i)

		self.event_ecnt = len(event_list)
		self.event_len = self.total_events_size/4096
		if (self.total_events_size % 4096):
			self.event_len += 1

		self.event_fill = 4096 - (self.total_events_size % 4096)

		self.group_offset = (self.event_offset + self.event_len)

		for i in group_list:
			self.total_group_size += len(i)

		self.group_ecnt = len(group_list)
		self.group_len = self.total_events_size/4096
		if (self.total_group_size % 4096):
			self.group_len += 1

		self.group_fill = 4096 - (self.total_group_size % 4096)

		#Current this catalog does not support other groups like
		# schema, formula ..
		#In future if needed added it here.
		self.total_grp_events_pages += self.group_len + self.event_len
		self.catalog_len = self.total_grp_events_pages

		self.s_format = "I I Q s s s s s s s s s s s s s s s s 32s H H H\
					2s H H H 2s H H H 2s H H H 2s"
		self.s_var = struct.Struct("> " + self.s_format)
		self.s_val = (self.magic, self.catalog_len, self.ver, self.date_str[0],\
				self.date_str[1], self.date_str[2], self.date_str[3],\
				self.date_str[4], self.date_str[5], self.date_str[6],\
				self.date_str[7], self.date_str[8], self.date_str[9],\
				self.date_str[10], self.date_str[11], self.date_str[12],\
				self.date_str[13], self.date_str[14], self.date_str[15],\
				"                                ",\
				self.schema_offset, self.schema_len, self.schema_ecnt, "  ",\
				self.event_offset, self.event_len, self.event_ecnt, "  ",\
				self.group_offset, self.group_len, self.group_ecnt, "  ",\
				self.form_offset, self.form_len, self.form_ecnt, "  ")

		self.s_cty = ctypes.create_string_buffer(self.s_var.size)
		self.s_var.pack_into(self.s_cty, 0, *self.s_val)
		self.page0_fill = 4096 - len(self.s_cty.raw)

		#print 'Unpacked:', self.s_var.unpack_from(self.s_cty, 0)
		#print 'Raw:', binascii.hexlify(self.s_cty.raw)

		#Lets write to the files.
		#Order of page here is
		# Page 0 -- Page0 structure
		# Page 1 to M -- Events
		# Page M+1 to N --Groups
		fobj = open(outfile_dir+"/catalog.bin", "wb+")
		fobj.write(self.s_cty.raw)
		fobj.write('\0' * self.page0_fill)

		#Page 2, write the events
		for i in event_list:
			fobj.write(i)
		fobj.write('\0' * self.event_fill)

		#Write the groups
		for i in group_list:
			fobj.write(i)
		fobj.write('\0' * self.group_fill)

		#fill the rest with \0
		fobj.write('\0' * ((1024 * 256) - fobj.tell()))

try:
	opts, args = getopt.getopt(sys.argv[1:],"d:")
except getopt.GetoptError:
	sys.exit(2)
for opt, arg in opts:
	if opt == '-d':
		outfile_dir = arg


##This catalog is filled with events support in this file
## https://github.com/maddy-kerneldev/occ/blob/cust_occ_mem_bw/src/occ/proc/nest_microcode.h

##Event Section
#
##List of mcs read events
Events(domain=1,start=0,length=0,offset=0x18,flag = 0,index=0,g_cnt=1,string = "mcs0_read")
Events(domain=1,start=0,length=0,offset=0x20,flag = 0,index=0,g_cnt=1,string = "mcs1_read")
Events(domain=1,start=0,length=0,offset=0x28,flag = 0,index=0,g_cnt=1,string = "mcs2_read")
Events(domain=1,start=0,length=0,offset=0x30,flag = 0,index=0,g_cnt=1,string = "mcs3_read")

##List of mcs write events
Events(domain=1,start=0,length=0,offset=0x38,flag = 0,index=0,g_cnt=1,string = "mcs0_write")
Events(domain=1,start=0,length=0,offset=0x40,flag = 0,index=0,g_cnt=1,string = "mcs1_write")
Events(domain=1,start=0,length=0,offset=0x48,flag = 0,index=0,g_cnt=1,string = "mcs2_write")
Events(domain=1,start=0,length=0,offset=0x50,flag = 0,index=0,g_cnt=1,string = "mcs3_write")

##Group Section
##MCS Read group
mcs_read =  array('H', [0,1,2,3,0,0,0,0,0,0,0,0,0,0,0,0])
Groups(flag=0,domain=1, start=0, length=0,index=1,ecnt=4, gname="MCS_Read_BW", earr=mcs_read)
##MCS write group
mcs_write = array('H', [4,5,6,7,0,0,0,0,0,0,0,0,0,0,0,0])
Groups(flag=0,domain=1, start=0, length=0,index=1,ecnt=4, gname="MCS_Write_BW", earr=mcs_write)

Page0(1, "2016020918450000")
