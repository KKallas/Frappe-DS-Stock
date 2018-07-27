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

		#function to traverse items
		def updateBins(doc, todo):
			'''
			Traverses through items list adds (todo=add) or removes projected qty (todo=clean)
			'''
			#check if either of the stocks is virtual
		 	fromVirtual = frappe.get_doc("Stock", doc.stock_from).virtualstock
			toVirtual = frappe.get_doc("Stock", doc.stock_to).virtualstock

			#scan through all items in the subtable
			for item in doc.items:
				#get the item deffiniton doc
				itemDoc = frappe.get_doc("Item",item.item)
				#from
				if not fromVirtual:
					binName = "["+itemDoc.code+"] / "+doc.stock_from
					#make sure bin exists
					if frappe.db.exists("Bin", binName):
						binDoc = frappe.get_doc("Bin",binName)
						if todo == "clean":
							binDoc.forecastDelete(self)
						else:
							binDoc.forecastUpdate(item,doc,1)

					else:
						#make bin if one does not exist
						binDoc = frappe.get_doc({"doctype":"Bin","stock":doc.stock_from,"item":item.item})
						binDoc.insert()
						#when cleaning out old entries there and the bind does not exist, it is enough to create one
						if todo == "clean":
							pass
						else:
							binDoc.forecastUpdate(item,doc,1)


				#to
				if not toVirtual:
					binName = "["+itemDoc.code+"] / "+doc.stock_to
					#make sure bin exists
					if frappe.db.exists("Bin", binName):
						binDoc = frappe.get_doc("Bin",binName)
						if todo == "clean":
							binDoc.forecastDelete(self)
						else:
							binDoc.forecastUpdate(item,doc,0)

					else:
						#make bin if one does not exist
						binDoc = frappe.get_doc({"doctype":"Bin","stock":doc.stock_to,"item":item.item})
						binDoc.insert()
						#when cleaning out old entries there and the bind does not exist, it is enough to create one
						if todo == "clean":
							pass
						else:
							binDoc.forecastUpdate(item,doc,0)

		#remove old esitamted entries
		if frappe.db.exists("Transfer Order",self.name):
			updateBins(self.get_doc_before_save(),"clean")

		#add lines
		updateBins(self,"add")

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
