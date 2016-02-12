odoo.define('tree_view_extend', function (require) {
"use strict";

var ViewManager = require('web.ViewManager')
var Model = require('web.Model')

$.fn.test_function = function(self, action)
{
	if (action){
		var self = self
		new Model("account.tax.report")
	    .call("open_print_report_wizard",[action.id])
	    .then(function (result) {
	    	self.do_action({
	            type: 'ir.actions.act_window',
	            res_model: 'tax.excel.report',
	            view_id: result,
	            views: [[false, 'form']],
	            target: 'new',
	            context:{'default_period_select':action.context.period_select,'default_date_from': action.context.date_from, 'show_button':true, 'default_date_to': action.context.date_to}
	        });
	    	
//	    	 if (action){
//	         	var button = $('#export_to_excel').length;
//	         	if (button == 0 && action.context.hasOwnProperty("show_button") == true){
//	         		$(".oe-control-panel").after("<div id='export_to_excel'><button  class='oe_highlight' type='button'>Export to Excel</button></div>")
//	         	}
//	         	if (!action.context.hasOwnProperty("show_button")){
//	         		$('#export_to_excel').remove()
//	         	}
//	         	
//	         	 $("#export_to_excel").click(function() {
//	         		 var action = action
////	         		 action.context.show_button = true;
//	         		 if(action){
//	         			 $.fn.test_function(action);
//	         		 }
//	        
//	             });
//	         }
	});
	}
	
},

ViewManager.include({
   
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
	start: function() {
		
        var self = this;
        var default_view = this.get_default_view();
        var default_options = this.flags[default_view] && this.flags[default_view].options;
        this._super();
       
//        if (self.action){
//        	var button = $('#export_to_excel').length;
//        	if (button == 0 && self.action.context.hasOwnProperty("show_button") == true){
//        		$(".oe-control-panel").after("<div id='export_to_excel'><button  class='oe_highlight' type='button' style='width:120px;height:30px'>Export to Excel</button></div>")
//        	}
//        	if (!self.action.context.hasOwnProperty("show_button")){
//        		$('#export_to_excel').remove()
//        	}
//        	
//        	 $("#export_to_excel").click(function() {
//        		 var action = self.action;
////        		 self.action.context.show_button = true;
//        		 if (action){
//        			 $.fn.test_function(self, action);
//        		 }
//        		 
//             });
//        }
        
        $('.oe-control-panel').bind("DOMSubtreeModified",function(){
			if($('li.active')[$('li.active').length-1]){
				var inner_text = $('li.active')[$('li.active').length-1].innerText;
				console.log("INNER TEXT::::::::", inner_text)
				if(inner_text.indexOf('Tax Balances') == -1){
					$('#export_to_excel').remove()
				}
				if (inner_text.indexOf('Tax Balances')!= -1){
					var button = $('#export_to_excel').length;
		        	if (button == 0 && self.action.context.hasOwnProperty("show_button") == true){
		        		$(".oe-control-panel").after("<div id='export_to_excel'><button  class='oe_highlight' type='button' style='width:120px;height:30px'>Export to Excel</button></div>")
		        	}
		        	$("#export_to_excel").click(function() {
		        		 var action = self.action;
//		        		 self.action.context.show_button = true;
		        		 if (action){
		        			 $.fn.test_function(self, action);
		        		 }
		        		 
		             });
				}
			}
			  
			});
        
        
    },
   
   
});

});
