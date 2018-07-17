# -*- coding: utf-8 -*-
# Copyright (c) 2018, digitalsputnik and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from operator import attrgetter

class Bin(Document):
	def autoname(self):
		itemCode = frappe.get_doc("Item",self.item).code
		self.name = "["+itemCode+"] / "+self.stock

	def forecastRecalculate(self):
		#if there are no forcasted lines
		if len(self.forecast_table) == 0:
			self.forecastQTY = 0
			#self.save()
			return

		self.forecast_table.sort(key=attrgetter('qty'), reverse=True)
		self.forecast_table.sort(key=attrgetter('date'))

		#add the lines togheter and update the IDX
		lineSum = self.qty
		newIdx = 0
		for line in self.forecast_table:
			#if it is just created Bin the line does not have defined qty?
			if line.qty:
				lineSum+=line.qty
			newIdx+=1
			line.qty_avaiable = lineSum
			line.idx = newIdx
			line.save()

		#update projected qty
		self.forecast = lineSum

		#update the record
		self.update_children()
		self.db_update()

	def on_update(self):
		self.forecastRecalculate()
		frappe.db.commit()

	def forecastUpdate(self,doc,transfer,dir):
		#deal with from/to stock, if from then we take from that stock
		if dir==1:
			qty = doc.qty*-1
		else:
			qty = doc.qty

		#create new forecast line
		newDoc = self.append("forecast_table",{"date":transfer.date,"qty":qty,"transfer":transfer.name})
		#newDoc.save()
		self.update_children()

		print "DEBUGDEBUGDEBUG"
		print self.name
		for item in self.forecast_table:
			print item.as_dict()

		#update the forecastQTY
		self.forecastRecalculate()

	def forecastDelete(self,doc):
		#delete the previous/dated forecast
		for line in self.forecast_table:
			if line.transfer == doc.name:
				self.remove(line)

		self.update_children()
		self.forecastRecalculate()

	def forecastCommit(self,doc,transfer,dir):
		#find out if the doc allready exits in the table

		oldEntry = None
		for line in self.forecast_table:
			if line.transfer == doc.parent:
				oldEntry = line
				break

		#deal with from/to stock, if from then we take from that stock
		if dir==1:
			qty = doc.qty*-1
		else:
			qty = doc.qty

		#remove forcast line
		self.remove(oldEntry)

		#update qty at hand
		self.qty += qty

		self.forecastRecalculate()
		self.save()
		#frappe.db.commit()
