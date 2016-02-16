# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import openerp
from openerp import tools
from openerp.addons.base.ir.ir_actions import ir_actions_report_xml

_logger = logging.getLogger(__name__)


def extend(class_to_extend):
    """
    Decorator to use to extend a existing class with a new method
    Example :
    @extend(Model)
    def new_method(self, *args, **kwargs):
        print 'I am in the new_method', self._name
        return True
    Will add the method new_method to the class Model
    """
    def decorator(func):
#         if hasattr(class_to_extend, func.func_name):
#             raise except_osv(_("Developper Error"),
#                 _("You can extend the class %s with the method %s.",
#                 "Indeed this method already exist use the decorator 'replace' instead"))
        setattr(class_to_extend, func.func_name, func)
        return class_to_extend
    return decorator


@extend(ir_actions_report_xml)
def render_report(self, cr, uid, res_ids, name, data, context=None):
    """
    Look up a report definition and render the report for the provided IDs.
    """
    new_report = self._lookup_report(cr, name)
    if isinstance(new_report, (str, unicode)):  # Qweb report
        # The only case where a QWeb report is rendered with this method occurs when running
        # yml tests originally written for RML reports.
        if openerp.tools.config['test_enable'] and not tools.config['test_report_directory']:
            # Only generate the pdf when a destination folder has been provided.
            return self.pool['report'].get_html(cr, uid, res_ids, new_report, data=data, context=context), 'html'
        elif data.get('form') and isinstance(data['form'], dict) and data['form'].get('is_excel'):
            excel_dict = data['form']['is_excel']
    #         obj_inst = excel_dict.get('obj')
            obj_inst = openerp.pooler.get_pool(cr.dbname).get(excel_dict.get('obj'))
            result = getattr(obj_inst, excel_dict.get('function'))(cr, uid, res_ids, data, context)
            return result
        else:
            return self.pool['report'].get_pdf(cr, uid, res_ids, new_report, data=data, context=context), 'pdf'
    else:
        return new_report.create(cr, uid, res_ids, data, context)