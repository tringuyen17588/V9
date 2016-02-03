# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from openerp.osv import fields, osv
from openerp import api


class account_tax(osv.osv):
    _inherit = 'account.tax'

    def _compute_account_balance(self, cr, uid, ids, tax_codes, context=None):
        """ compute the tax amount for the provided tax codes
        """
        fields = ['tax_amount', 'invoiced_amount']
        context = context
        date_from = context.get('date_from',False)
        date_to = context.get('date_to',False)

        invoice_states = ['open', 'paid']
        dates = [date_from, date_to]
        res = {}
        res_inv = {}
        for tax in tax_codes:
            res[tax.id] = dict((field, 0.0) for field in fields)
        if tax_codes:
            if False in dates:
                invoice_line_query = "SELECT COALESCE(SUM(price_subtotal), 0) as "\
                    "invoiced_amount, account_invoice_line_tax.tax_id from "\
                    "account_invoice_line, account_invoice_line_tax, account_invoice"\
                    " where account_invoice_line.id in"\
                    " (select invoice_line_id from account_invoice_line_tax where"\
                    " tax_id IN %s) and account_invoice_line.id=account_invoice_line_tax.invoice_line_id"\
                    " and account_invoice_line.invoice_id=account_invoice.id "\
                    " GROUP BY account_invoice_line_tax.tax_id"
                param = (tuple(tax_codes._ids),)
            else:
                invoice_line_query = "SELECT COALESCE(SUM(price_subtotal), 0) as "\
                    "invoiced_amount, account_invoice_line_tax.tax_id from "\
                    "account_invoice_line, account_invoice_line_tax, account_invoice"\
                    " where account_invoice_line.id in"\
                    " (select invoice_line_id from account_invoice_line_tax where"\
                    " tax_id IN %s) and account_invoice_line.id=account_invoice_line_tax.invoice_line_id"\
                    " and account_invoice_line.invoice_id=account_invoice.id and"\
                    " account_invoice.date_invoice >= %s and"\
                    " account_invoice.date_invoice <= %s" +\
                    " GROUP BY account_invoice_line_tax.tax_id"
                param = (tuple(tax_codes._ids),) + tuple(dates)
            cr.execute(invoice_line_query, param)
            for rw in cr.dictfetchall():
                res_inv[rw['tax_id']] = rw
            if False in dates:
                request = "SELECT tax_id as id, COALESCE(SUM(amount), 0) as tax_amount FROM " \
                    "account_invoice as account_invoice_tax__invoice_id,account_invoice_tax " \
                    "WHERE tax_id IN %s  AND (account_invoice_tax.invoice_id=account_invoice_tax__invoice_id.id) AND " \
                    "(account_invoice_tax__invoice_id.state in %s) GROUP BY tax_id"
                params = (tuple(tax_codes._ids),) + (tuple(invoice_states),)
            else:
                request = "SELECT tax_id as id, COALESCE(SUM(amount), 0) as tax_amount FROM " \
                    "account_invoice as account_invoice_tax__invoice_id,account_invoice_tax " \
                    "WHERE tax_id IN %s  AND (account_invoice_tax.invoice_id=account_invoice_tax__invoice_id.id) AND " \
                    "(account_invoice_tax__invoice_id.state in %s) AND (account_invoice_tax__invoice_id.date_invoice >= %s) AND "\
                    "(account_invoice_tax__invoice_id.date_invoice <= %s) GROUP BY tax_id"

                params = (tuple(tax_codes._ids),) + (tuple(invoice_states),) + tuple(dates) 
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

    def compute_taxed_amount(self, cr, uid, ids, field_name, arg, context=None):
        '''Returns Taxed Amount for all the codes which are configured
        in this Report or its children'''
        res = {}
        taxed_amount = 0.0
        report_balance = self.browse(cr, uid, ids, context)._compute_account_balance(self.browse(cr, uid, ids, context))
        for report in report_balance.keys():
            taxed_amount = report_balance.get(report).get('tax_amount')
            res.update({report: taxed_amount})
        return res

    def compute_invoiced_amount(self, cr, uid, ids, field_name, arg, context=None):
        '''Returns Taxed Amount for all the codes which are configured
        in this Report or its children'''
        res = {}
        invoiced_amount = 0.0
        report_balance = self.browse(cr, uid, ids, context)._compute_account_balance(self.browse(cr, uid, ids, context))
        for report in report_balance.keys():
            invoiced_amount = report_balance.get(report).get('invoiced_amount')
            res.update({report: invoiced_amount})
        return res

    _columns = {'taxed_amount': fields.function(compute_taxed_amount,
                                                type='float',
                                                string='Taxed Amount'),
               'invoiced_amount': fields.function(compute_invoiced_amount,
                                                  type='float',
                                                  string='Invoiced Amount(Tax Exclusive)') } 