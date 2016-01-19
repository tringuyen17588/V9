odoo.define('tree_view_extend', function (require) {
"use strict";

var ControlPanelMixin = require('web.ControlPanelMixin');
var core = require('web.core');
var data = require('web.data');
var framework = require('web.framework');
var DataModel = require('web.DataModel');
var pyeval = require('web.pyeval');
var SearchView = require('web.SearchView');
var Widget = require('web.Widget');
var ViewManager = require('web.ViewManager')
var Model = require('web.Model')

var QWeb = core.qweb;
var _t = core._t;
ViewManager.include({
   
    /**
     * @returns {jQuery.Deferred} initial view loading promise
     */
	start: function() {
        var self = this;
        var default_view = this.get_default_view();
        var default_options = this.flags[default_view] && this.flags[default_view].options;

        this._super();
        var views_ids = {};
        _.each(this.views, function (view) {
            views_ids[view.type] = view.view_id;
            
            view.options = _.extend({
                action : self.action,
                action_views_ids : views_ids,
            }, self.flags, self.flags[view.type], view.options);
            view.$container = self.$(".oe-view-manager-view-" + view.type);
            
        });
        if (self.action){
        	 console.log("this.action:::::::::::",this.action.context)
        	 var button = $('#export_to_excel').length;
             if (button == 0 && this.action.context.hasOwnProperty("show_button") == true){
             	$(".oe-control-panel").after("<div id='export_to_excel'><button  class='oe_highlight' type='button'>Export to Excel</button></div>")
             }
             if (this.action.context.hasOwnProperty("show_button") == false){
            	 $('#export_to_excel').remove()
             }
             $("#export_to_excel").click(function() {
                 self.button_clicked();
             });
        }
       
//        else{
//        	if(button > 0){
//        		console.log("LLLLLLLLLLLLL")
//        		$('#test_button').remove()
//        	}
//        }

        this.control_elements = {};
        if (this.flags.search_view) {
            this.search_view_loaded = this.setup_search_view();
        }
        if (this.flags.views_switcher) {
            this.render_switch_buttons();
        }

        // Switch to the default_view to load it
        var main_view_loaded = this.switch_mode(default_view, null, default_options);

        return $.when(main_view_loaded, this.search_view_loaded);
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
                if (button == 0 && (self.action.xml_id == "ia_au_gst_reporting.action_tax_report_tree_hierarchy" || self.action.res_model == 'tax.excel.report')){
                	$(".oe-control-panel").after("<div id='export_to_excel'><button  class='oe_highlight' type='button'>Export to Excel</button></div>")
                }
//                if (self.action.xml_id != "ia_au_gst_reporting.action_tax_report_tree_hierarchy" && self.action.xml_id != "ia_au_gst_reporting.action_account_tax_line_open"){
//                	$('#export_to_excel').remove()
//                }
                $("#export_to_excel").click(function() {
                    self.button_clicked();
                });
           }
        	
        });
//   	 var model = new instance.web.Model("oepetstore.message_of_the_day");
//        model.call("my_method", {context: new instance.web.CompoundContext()}).then(function(result) {
//        console.log(result["hello"])
//            // will show "Hello world" to the user
//        });
   },
   
 
});

});
