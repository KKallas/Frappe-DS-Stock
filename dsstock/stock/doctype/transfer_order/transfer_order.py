# -*- coding: utf-8 -*-
# Copyright (c) 2018, digitalsputnik and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TransferOrder(Document):
	def on_update(self):
		'''
		Save Stock Transaction:

		1. Consolidate all items (if there is more than one copy)

		2. If the document has been saved before remove all projections

		3. Insert Bin items for etimated transactions
		3.1 create Bin if necessary

		'''
		#consolidate all lines (1 occurence per item)
		for item in self.items:
			toConsolidate = []
			itemName = item.item
			for subItem in self.items:
				if subItem.item == item.item:
					toConsolidate.append(subItem)
			#if there is more than one line consolidate the sums
			if len(toConsolidate)>1:
				#get unit sum
				sum = 0
				for subItem in toConsolidate:
					sum += subItem.qty
				#put sum to 1st accurance
				toConsolidate[0].qty = sum
				toConsolidate[0].save()
				#delete other lines
				toRemove = toConsolidate[1:]
				for subItem in toRemove:
					self.remove(subItem)
				self.update_children()

		#remove old esitamted entries
		if not frappe.db.exists("Transfer Order",self.name):
			oldDoc = self.get_doc_before_save()
			#check if either of the stocks is virtual
			oldFromVirtual = frappe.get_doc("Stock", oldDoc.stock_from).virtualstock
			oldToVirtual = frappe.get_doc("Stock", oldDoc.stock_to).virtualstock

			for item in oldDoc.items:
				oldItemDoc = frappe.get_doc("Item",item.item)
				#from
				if not oldFromVirtual:
					binDoc = frappe.get_doc("Bin","["+oldItemDoc.code+"] / "+oldDoc.stock_from)
					binDoc.forecastDelete(self)
				#to
				if not oldToVirtual:
					binDoc = frappe.get_doc("Bin","["+oldItemDoc.code+"] / "+oldDoc.stock_to)
					binDoc.forecastDelete(self)

		#add new estimated entries
		#check if either of the stocks is virtual
		fromVirtual = frappe.get_doc("Stock", self.stock_from).virtualstock
		toVirtual = frappe.get_doc("Stock", self.stock_to).virtualstock

		for item in self.items:
			itemDoc = frappe.get_doc("Item",item.item)

			if not fromVirtual:
				#check if the bin exitst, if not create one
				if frappe.db.exists("Bin","["+itemDoc.code+"] / "+self.stock_from):
					#update bin line item
					binDoc = frappe.get_doc("Bin","["+itemDoc.code+"] / "+self.stock_from)
					binDoc.forecastUpdate(item,self,1)
				#create Bin
				else:
					doc = frappe.get_doc({"doctype":"Bin","stock":self.stock_from,"item":item.item})
					doc.insert()
					doc.forecastUpdate(item,self,1)
			#to
			if not toVirtual:
				#check if the bin exitst, if not create one
				if frappe.db.exists("Bin","["+itemDoc.code+"] / "+self.stock_to):
					#update bin line item
					binDoc = frappe.get_doc("Bin","["+itemDoc.code+"] / "+self.stock_to)
					binDoc.forecastUpdate(item,self,0)
				#create Bin
				else:
					doc = frappe.get_doc({"doctype":"Bin","stock":self.stock_to,"item":item.item})
					doc.insert()
					doc.forecastUpdate(item,self,0)


	def on_submit(self):
		'''
		Submit transaction


		'''
		#check if either of the stocks is virtual
		fromVirtual = frappe.get_doc("Stock", self.stock_from).virtualstock
		toVirtual = frappe.get_doc("Stock", self.stock_to).virtualstock

		for item in self.items:
			itemDoc = frappe.get_doc("Item",item.item)
		#from
			if not fromVirtual:
				binDoc = frappe.get_doc("Bin","["+itemDoc.code+"] / "+self.stock_from)
				binDoc.forecastCommit(item,self,1)
		#to
			if not toVirtual:
				binDoc = frappe.get_doc("Bin","["+itemDoc.code+"] / "+self.stock_to)
				binDoc.forecastCommit(item,self,0)
