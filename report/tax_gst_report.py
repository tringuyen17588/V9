# -*- coding: utf-8 -*-

import time
from openerp import api, fields, models
from openerp.exceptions import Warning


class report_tax_gst(models.AbstractModel):
    _name = 'report.ia_au_gst_reporting.report_tax_gst'

    def _compute_account_balance(self, tax_codes):
        """ compute the tax amount for the provided tax codes
        """
        fields = ['tax_amount', 'invoiced_amount']
        context = self._context
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
                    "invoiced_amount, account_invoice_line_tax.tax_id from account_invoice_line, account_invoice_line_tax where id in"\
                    " (select invoice_line_id from account_invoice_line_tax where"\
                    " tax_id IN %s) and account_invoice_line.id=account_invoice_line_tax.invoice_line_id"\
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
            self.env.cr.execute(invoice_line_query, param)
            for rw in self.env.cr.dictfetchall():
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
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
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

    def _compute_report_balance(self, reports):
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
                res[report.id]['tax_code'] = self._compute_account_balance(tax_codes)
                for value in res[report.id]['tax_code'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum of the tax codes
                res[report.id]['tax_code'] = self._compute_account_balance(report.tax_ids)                
                for value in res[report.id]['tax_code'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        report_obj = self.env['account.tax.report'].browse(key)
                        res[report.id][field] += value[field] * report_obj.sign
        return res

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.tax.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        for report in child_reports:
            vals = {
                'name': report.name,
                'tax_amount': res[report.id]['tax_amount'],
                'invoiced_amount': res[report.id]['invoiced_amount'],
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False, #used to underline the financial report balances
            }

            lines.append(vals)
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the tax report, so it's not needed here.
                continue

            if res[report.id].get('tax_code'):
                for tax_id, value in res[report.id]['tax_code'].items():
                    #if there are tax codes to display, we add them to the lines with a level equals to their level in
                    flag = False
                    tax = self.env['account.tax'].browse(tax_id)
                    vals = {
                        'name': tax.name,
                        'tax_amount': value['tax_amount'] or 0.0,
                        'invoiced_amount': value['invoiced_amount'] or 0.0,
                        'type': 'tax',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'tax_type': tax.type_tax_use,
                    }
                    if not tax.company_id.currency_id.is_zero(vals['tax_amount']) or not tax.company_id.currency_id.is_zero(vals['invoiced_amount']):
                            flag = True
                    if flag:
                        lines.append(vals)
        return lines

    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        tax_lines = self.get_account_lines(data.get('form'))
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Date': fields.date.today(),
            'get_tax_lines': tax_lines,
        }
        return self.env['report'].render('ia_au_gst_reporting.report_tax_gst', docargs)
