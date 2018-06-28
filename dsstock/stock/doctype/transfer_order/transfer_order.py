# -*- coding: utf-8 -*-
# Copyright (c) 2018, digitalsputnik and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TransferOrder(Document):
	def on_update(self):
		pass
		#check from stock, if the stock is not virtual check if the bin exists, if not create it
		#self.from
		#self.to
		#TODO ij JS if not virtual check if enough stock is avaiable and make the record
		#add future move with link tomyself

		#repeat with to stock

	def on_submit(self):
		frappe.throw("not submited")
		#bin must exists
		#find from bin and remove predicted line, flatten qty at hand
		#repeat with stock
