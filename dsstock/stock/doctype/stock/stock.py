# -*- coding: utf-8 -*-
# Copyright (c) 2018, digitalsputnik and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document

class Stock(Document):
	def getItemCount(self,itemCode):
		return frappe.get_doc("Bin","["+itemCode+"] / "+self.name).qty


#get qty avaiable per list of items
#TODO estimated qty
@frappe.whitelist()
def itemsAvailabilty(itemListJSON,stock):
	itemList = json.loads(itemListJSON)
	returnList = []

	for item in itemList:
		#handle empty item name
		if item["item"]=="":
			returnList.append([0,0])
			continue

		itemCode = item["item"].split(" ")[0]
		itemName = ""+itemCode+" / "+stock
		# check if bin exists (if not set value to 0)
		if frappe.db.exists("Bin",itemName):
			itemBin = frappe.get_doc("Bin",""+itemCode+" / "+stock)
			returnList.append([itemBin.qty,0])
		# if bin exitst get actual qty at hand
		else:
			returnList.append([0,0])

	return returnList
