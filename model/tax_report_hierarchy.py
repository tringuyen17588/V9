# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, models, fields

# ---------------------------------------------------------
# Account Financial Report
# ---------------------------------------------------------


class account_tax_report(models.Model):
    _name = "account.tax.report"
    _description = "Tax Report"

    @api.multi
    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        '''Returns a dictionary with key=the ID of a record and value = the level of this  
           record in the tree structure.'''
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level

#     def _get_children_by_order(self):
#         '''returns a recordset of all the children computed recursively, and sorted by sequence. Ready for the printing'''
#         res = self
#         children = self.search([('parent_id', 'in', self.ids)], order='sequence ASC')
#         if children:
#             res += children._get_children_by_order()
#         return res

    def _get_children_by_order(self):
        '''returns a recordset of all the children computed recursively, and sorted by sequence. Ready for the printing'''
        res = self
        children = self.search([('parent_id', 'in', self.ids)], order='sequence ASC')
        for child in children:
            res += child._get_children_by_order()
        return res

    name = fields.Char('Report Name', required=True, translate=True)
    parent_id = fields.Many2one('account.tax.report', 'Parent')
    children_ids = fields.One2many('account.tax.report', 'parent_id', 'Account Report')
    sequence = fields.Integer('Sequence')
    level = fields.Integer(compute='_get_level', string='Level', store=True)
    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Tax Group'),
        ('account_type', 'Tax Code'),
        ('account_report', 'Report Value'),
        ('detailed_report', 'Detailed Report')
        ], 'Type', default='sum')
    tag_ids = fields.Many2many('account.account.tag', 'account_tax_report_tag', 'report_id', 'tag_id', 'Tax Groups')
    account_report_id = fields.Many2one('account.tax.report', 'Report Value')
    tax_ids = fields.Many2many('account.tax', 'account_tax_report_tax_code', 'report_id', 'tax_id', 'Tax Codes')
    sign = fields.Selection([(-1, 'Reverse balance sign'), (1, 'Preserve balance sign')], 'Sign on Reports', required=True, default=1,
                            help='For accounts that are typically more debited than credited and that you would like to print as negative amounts in your reports, you should reverse the sign of the balance; e.g.: Expense account. The same applies for accounts that are typically more credited than debited and that you would like to print as positive amounts in your reports; e.g.: Income account.')
    display_detail = fields.Selection([
        ('no_detail', 'No detail'),
        ('detail_flat', 'Display children flat'),
        ('detail_with_hierarchy', 'Display children with hierarchy')
        ], 'Display details', default='detail_flat')
    style_overwrite = fields.Selection([
        (0, 'Automatic formatting'),
        (1, 'Main Title 1 (bold, underlined)'),
        (2, 'Title 2 (bold)'),
        (3, 'Title 3 (bold, smaller)'),
        (4, 'Normal Text'),
        (5, 'Italic Text (smaller)'),
        (6, 'Smallest Text'),
        ], 'Financial Report Style', default=0,
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    

class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'

    name = fields.Char(required=True)
    applicability = fields.Selection([('accounts', 'Accounts'), ('taxes', 'Taxes')], required=True, default='accounts')
    color = fields.Integer('Color Index')
    tax_ids = fields.Many2many('account.tax', 'account_tax_account_tag', string='Tax Codes')  
    
class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'
    
    @api.model
    def _query_get(self, domain=None):
        context = dict(self._context or {})
        domain = domain and safe_eval(domain) or []

        date_field = 'date'
        if context.get('date_to'):
            domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
            domain += [(date_field, '>=', context['date_from'])]

        state = context.get('state')
        if state and state.lower() != 'all':
            domain += [('move_id.state', '=', state)]

        if context.get('company_id'):
            domain += [('company_id', '=', context['company_id'])]

        if 'company_ids' in context:
            domain += [('company_id', 'in', context['company_ids'])]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
            query = self._where_calc(domain)
            tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params
