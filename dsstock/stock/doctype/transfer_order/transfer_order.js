// Copyright (c) 2018, digitalsputnik and contributors
// For license information, please see license.txt

//TODO, if button is submit hide it, if save display - then clean up refresh
//TODO, line calculactions
//TODO, after line calculations are done do unit totals

//1. rea-summa jagatud tykkideks
//2. tykki hinna valuuta konvert
//3. lisa kulu konvert
//4. lisa kulu jagatud toodetele


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
		//cur_frm.enable_save();
		return(0);
	}

	//update the stock_to or stock_from query filter to exlude the other
	if(cur_frm.doc.stock_to==undefined) {
		cur_frm.set_query("stock_from",function(){return {filters: []}});
	}
	else{
		cur_frm.set_query("stock_from",function(){return {"filters": {"name":['!=',cur_frm.doc.stock_to]}}});
	}
	//if from is empty
	if(cur_frm.doc.stock_from==undefined) {
		cur_frm.set_query("stock_to",function(){return {filters: []}});
	}
	else{
		cur_frm.set_query("stock_to",function(){return {"filters": {"name":['!=',cur_frm.doc.stock_from]}}});
	}

	//get the avaiablity qty list and mark into doc
	frappe.call({"method":"dsstock.stock.doctype.stock.stock.itemsAvailabilty",
								"args":{"itemListJSON":itemsListJSON, "stock":cur_frm.doc.stock_from},
								"callback":function(r){
									//write the avaiable and predicted values in to local doc instance
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
										//cur_frm.disable_save();
									} else {
										//cur_frm.enable_save();
									}
								}});

}

//lock is used to avoid looping as line total should be calculated if individual price is entered
//and individual price should calculated if entire line cost is entered
var calLock = "";

var recalculateItems = function(cdt,cdn) {
	//set per item price and line price
	var line_qty = frappe.model.get_value(cdt,cdn,"qty");
	var line_item = frappe.model.get_value(cdt,cdn,"item_price");
	var line_total = frappe.model.get_value(cdt,cdn,"total_price");
	//item priority
	if (calLock=="item") {
		frappe.model.set_value(cdt,cdn,"total_price",line_item*line_qty);
	}
	//line priority
	else {
		frappe.model.set_value(cdt,cdn,"item_price",line_total/line_qty);
	}

	//add shared cost to EUR price
	var valWithoutShared = 0
	for(var line in cur_frm.doc.items) {
		valWithoutShared+=(cur_frm.doc.items[line].item_price*cur_frm.doc.conversion*cur_frm.doc.items[line].qty);
	}
	//curr_line/sum*divided_costs per every line
	for(var line in cur_frm.doc.items) {
		//calculate all lines total without added costs
		var lineVal = cur_frm.doc.items[line].item_price*cur_frm.doc.conversion*cur_frm.doc.items[line].qty;
		//curr_line/sum*divided_costs per every line
		var shared = lineVal/valWithoutShared*cur_frm.doc.shared_total;
		frappe.model.set_value("Transfer Order Item",cur_frm.doc.items[line].name,"item_eur",cur_frm.doc.items[line].item_price*cur_frm.doc.conversion+(shared/cur_frm.doc.items[line].qty));
	}
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
	},
	conversion: function(frm,cdt,cdn) {
		//recalculate all lines if conversion rate is changed
		for(var line in cur_frm.doc.items) {
			calLock = "item";
			recalculateItems("Transfer Order Item",cur_frm.doc.items[line].name);
			calLock = "";
		}
	},
	shared_total: function(frm,cdt,cdn) {
		//recalculate all lines if conversion rate is changed
		for(var line in cur_frm.doc.items) {
			calLock = "item";
			recalculateItems("Transfer Order Item",cur_frm.doc.items[line].name);
			calLock = "";
		}
	},
	before_submit: function() {
		frappe.valdiated = false;
		frappe.throw("Test");
	}
});


frappe.ui.form.on('Transfer Order Item', {
	item: function(frm,cdt,cdn) {
		updateAvailabilty();
		//TODO get item price
		frappe.model.set_value(cdt,cdn,"item_price",0);
	},
	total_price: function(frm,cdt,cdn) {
		if(calLock=="") {
			calLock = "total";
			recalculateItems(cdt,cdn);
			calLock = "";
		}
	},
	qty: function(frm,cdt,cdn) {
		updateAvailabilty();
		recalculateItems(cdt,cdn);
	},
	item_price: function(frm,cdt,cdn) {
		if(calLock=="") {
			calLock = "item";
			recalculateItems(cdt,cdn);
			calLock = "";
		}
	},
	before_items_remove(frm,cdt,cdn) {
		updateAvailabilty();
		//var deleted_row = frappe.get_doc(cdt, cdn);
		//console.log(deleted_row);
	}
});

//Shared costs into EUR and calculate total
var recalculateShared = function(cdt,cdn) {
	var price = frappe.model.get_value(cdt,cdn,"price");
	var conversion = frappe.model.get_value(cdt,cdn,"conversion");

	frappe.model.set_value(cdt,cdn,"eur",price*conversion);

	//calculate total
	var sharedTotal = 0;
	for(var item in cur_frm.doc.shared) {
		sharedTotal = sharedTotal + cur_frm.doc.shared[item].eur;
	}
	cur_frm.set_value("shared_total",sharedTotal);
}

frappe.ui.form.on('Transfer Order Shared Cost', {
	price: function(frm,cdt,cdn) {
		recalculateShared(cdt,cdn);
	},
	conversion: function(frm,cdt,cdn) {
		recalculateShared(cdt,cdn);
	},
	shared_remove: function(frm,cdt,cdn) {
		recalculateShared(cdt,cdn);
	}
});
