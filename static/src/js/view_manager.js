odoo.define('tree_view_extend', function (require) {
"use strict";

var ViewManager = require('web.ViewManager')
var Model = require('web.Model')

ViewManager.include({
   
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
	start: function() {
        var self = this;
        var default_view = this.get_default_view();
        var default_options = this.flags[default_view] && this.flags[default_view].options;

        this._super();
        
        if (self.action){
        	var button = $('#export_to_excel').length;
        	if (button == 0 && self.action.context.hasOwnProperty("show_button") == true){
        		$(".oe-control-panel").after("<div id='export_to_excel'><button  class='oe_highlight' type='button' style='width:120px;height:30px'>Export to Excel</button></div>")
        	}
        	if (button>0 && !self.action.context.hasOwnProperty("show_button")){
        		$('#export_to_excel').remove()
        	}
        	$("#export_to_excel").click(function() {
                self.button_clicked();
            });
        }
    },
   
    button_clicked: function() {
    	var self = this
    	new Model("account.tax.report")
        .call("open_print_report_wizard",[this.action.id])
        .then(function (result) {
        	self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'tax.excel.report',
                view_id: result,
                views: [[false, 'form']],
                target: 'new'
            });
        	
        	 if (self.action){
             	var button = $('#export_to_excel').length;
             	if (button == 0 && self.action.context.hasOwnProperty("show_button") == true){
             		$(".oe-control-panel").after("<div id='export_to_excel'><button  class='oe_highlight' type='button'>Export to Excel</button></div>")
             	}
             	if (button>0 && !self.action.context.hasOwnProperty("show_button")){
             		$('#export_to_excel').remove()
             	}
             	$("#export_to_excel").click(function() {
                     self.button_clicked();
                 });
             }
        	
        });

   },
 
});

});
