// Copyright (c) 2018, digitalsputnik and contributors
// For license information, please see license.txt

var updateAvailabilty = function() {
	//get stock list
	var itemsList = cur_frm.doc.items.map((val) => {return{item:val.item,qty:val.qty}});
	var itemsListJSON = JSON.stringify(itemsList);

	//if stock is virtual or
	//if the stock_from is empty clear all errors and set the avaiable and predicted to 0
	if(cur_frm.doc.stock_from==undefined || cur_frm.doc.stock_from_virtual==1) {
		cur_frm.doc.items.forEach(function(item,index){
			cur_frm.doc.items[index].qty_avaiable=0;
			cur_frm.doc.items[index].qty_predicted=0;
			$("div.row-index")[index+1].style.backgroundColor = "white";
		});
		cur_frm.enable_save();
		return(0);
	}

	//get the avaiablity qty list and mark into doc
	frappe.call({"method":"dsstock.stock.doctype.stock.stock.itemsAvailabilty",
								"args":{"itemListJSON":itemsListJSON, "stock":cur_frm.doc.stock_from},
								"callback":function(r){
									//write the avaiable and predicted values in to local doc instance
									//TODO make row avaiablity and write the values there
									r["message"].forEach(function(item,index) {
										cur_frm.doc.items[index].qty_avaiable=item[0];
										cur_frm.doc.items[index].qty_predicted=item[1];
									});

									//chnage the line nr DVI to red color if not enough stock is avaiable
									var badLineCounter = 0;
									cur_frm.doc.items.forEach(function(item,index){
										//find the line nr DIV foc current line
										if(item.qty>item.qty_avaiable) {
											$("div.row-index")[index+1].style.backgroundColor = "red";
											badLineCounter +=1;
										}
										else{
											$("div.row-index")[index+1].style.backgroundColor = "white";
										}
									});

									//if at least one of the lines not avaiable then diable submit button
									if(cur_frm.toolbar.current_status=="Submit" && badLineCounter>0) {
										cur_frm.disable_save();
									} else {
										cur_frm.enable_save();
									}
								}});

}


frappe.ui.form.on('Transfer Order', {
	refresh: function(frm) {
		//create current version
		cur_frm.oldDoc = JSON.parse(JSON.stringify(cur_frm.doc));
		//hide hidden linked inputs
		$("div[data-fieldname='stock_from_virtual']").hide();
		$("div[data-fieldname='stock_to_virtual']").hide();
		//update the stock avaiablity
		updateAvailabilty();
	},
	stock_from: function(frm) {
		updateAvailabilty();
	}
});

frappe.ui.form.on('Transfer Order Item', {
	item: function(frm) {
		updateAvailabilty();
	},
	qty: function(frm) {
		updateAvailabilty();
	},
	before_items_remove(frm,cdt,cdn) {
		var deleted_row = frappe.get_doc(cdt, cdn);
		console.log(deleted_row);
	}
});
