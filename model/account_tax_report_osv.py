# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from openerp.osv import fields, osv
from openerp import api
from ..report.tax_gst_report import report_tax_gst


class account_tax_report(osv.osv):
    _inherit = 'account.tax.report'

    def _compute_account_balance(self, cr, uid, ids, tax_codes, context=None):
        """ compute the tax amount for the provided tax codes
        """
        fields = ['tax_amount', 'invoiced_amount']
        context = context
        date_from = context.get('date_from', False)
        date_to = context.get('date_to', False)
 
        invoice_states = ['open', 'paid']
        res = {}
        res_inv = {}
        for tax in tax_codes:
            res[tax.id] = dict((field, 0.0) for field in fields)
        if tax_codes:
            invoice_line_query = "SELECT COALESCE(SUM(price_subtotal), 0) as "\
                "invoiced_amount, account_invoice_line_tax.tax_id from account_invoice_line, account_invoice_line_tax where id in"\
                " (select invoice_line_id from account_invoice_line_tax where"\
                " tax_id IN %s) and account_invoice_line.id=account_invoice_line_tax.invoice_line_id"\
                " GROUP BY account_invoice_line_tax.tax_id"
            param = (tuple(tax_codes._ids),)
            cr.execute(invoice_line_query, param)
            for rw in cr.dictfetchall():
                res_inv[rw['tax_id']] = rw
            request = "SELECT tax_id as id, COALESCE(SUM(amount), 0) as tax_amount FROM " \
                "account_invoice as account_invoice_tax__invoice_id,account_invoice_tax " \
                "WHERE tax_id IN %s  AND (account_invoice_tax.invoice_id=account_invoice_tax__invoice_id.id) AND " \
                "(account_invoice_tax__invoice_id.state in %s)"\
                " GROUP BY tax_id"
 
            params = (tuple(tax_codes._ids),) + (tuple(invoice_states),)
            cr.execute(request, params)
            for row in cr.dictfetchall():
                res[row['id']] = row
                if res_inv.get(row['id']):
                    invoiced_amount = res_inv.get(row['id']).get('invoiced_amount')
                    res[row['id']].update({'invoiced_amount': invoiced_amount})
            for r_key in res_inv.keys():
                if res.get(r_key):
                    invoiced_amount = res_inv.get(r_key).get('invoiced_amount')
                    if invoiced_amount != 0.0:
                        existing_rec = res[r_key]
                        existing_rec.update({'invoiced_amount': invoiced_amount})
                        res.update({r_key: existing_rec})
        return res

    def _compute_report_balance(self, cr, uid, ids, reports, context=None):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the tax codes linked with the selected tax groups
               'account_type' : it's the sum of the tax codes
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['tax_amount', 'invoiced_amount']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the tax codes linked with the selected tax groups
                tax_ids = []
                for tag in report.tag_ids:
                    for tax in tag.tax_ids:
                        tax_ids.append(tax.id)
                tax_codes = self.env['account.tax'].browse(tax_ids)
                res[report.id]['tax_code'] = self.browse(cr, uid, ids)._compute_account_balance(tax_codes)
                for value in res[report.id]['tax_code'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum of the tax codes
                res[report.id]['tax_code'] = self.browse(cr, uid, ids)._compute_account_balance(report.tax_ids)                
                for value in res[report.id]['tax_code'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self.browse(cr, uid, ids)._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self.browse(cr, uid, ids)._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        report_obj = self.pool['account.tax.report'].browse(cr, uid, key)
                        res[report.id][field] += value[field] * report_obj.sign
        return res

    def compute_taxed_amount(self, cr, uid, ids, field_name, arg, context=None):
        '''Returns Taxed Amount for all the codes which are configured
        in this Report or its children'''
        res = {}
        taxed_amount = 0.0
        report_balance = self.browse(cr, uid, ids)._compute_report_balance(self.browse(cr, uid, ids))
        for report in report_balance.keys():
            taxed_amount = report_balance.get(report).get('tax_amount')
            res.update({report: taxed_amount})
        return res

    def compute_tax_excl_amount(self, cr, uid, ids, field_name, arg, context=None):
        '''Returns Taxed Amount for all the codes which are configured
        in this Report or its children'''
        res = {}
        invoiced_amount = 0.0
        report_balance = self.browse(cr, uid, ids)._compute_report_balance(self.browse(cr, uid, ids))
        for report in report_balance.keys():
            invoiced_amount = report_balance.get(report).get('invoiced_amount')
            res.update({report: invoiced_amount})
        return res

    _columns = {
        'amount_taxed': fields.function(compute_taxed_amount, string='Taxed Amount', type='float'),
        'amount_tax_exclusive': fields.function(compute_tax_excl_amount, string='Invoiced Amount(Tax Excl.)', type='float')
    }