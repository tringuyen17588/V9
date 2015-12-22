# -*- coding: utf-8 -*-

import time
from openerp import api, fields, models
from openerp.exceptions import Warning


class report_tax_gst_code_wise(models.AbstractModel):
    _name = 'report.ia_au_gst_reporting.report_tax_gst_code_wise'
    
    def get_tax_lines(self, data):
        domain = []
        tax_wise_data_list_sale = []
        tax_wise_data_list_purchase = []
        sale_refund_result = {}
        purchase_refund_result = {}
        res = {'Purchase': [], 'Sale': []}
        report_obj = self.env['account.tax.report'].browse(data['account_report_id'][0])
        report_tax_ids = report_obj.tax_ids.ids
        account_tax_env = self.env['account.tax']
        account_invoice_env = self.env['account.invoice']
        account_invoice_tax_env = self.env['account.invoice.tax']
        if report_tax_ids:
            sale_taxes = account_tax_env.search([('company_id', '=', data['company_id'][0]),
                                                 ('type_tax_use', '=', 'sale'),
                                                 ('id', 'in', tuple(report_tax_ids))])
        else:
            sale_taxes = account_tax_env.search([('company_id', '=', data['company_id'][0]),
                                                 ('type_tax_use', '=', 'sale')]
                                                )

        if data['date_from']:
            domain.append(('date_invoice', '>=', data['date_from']))
        if data['date_to']:
            domain.append(('date_invoice', '<=', data['date_to']))
        if data['company_id']:
            domain.append(('company_id', '=', data['company_id'][0]))
        domain.append(('state', 'in', ['open', 'paid']))

        #    Calculation of Sales Tax
        customer_invoice_domain = domain + [('type', '=', 'out_invoice')]
        customer_invoice_refund_domain = domain + [('type', '=', 'out_refund')]
        customer_invoices = account_invoice_env.search(customer_invoice_domain)
        customer_refund_invoices = account_invoice_env.search(customer_invoice_refund_domain)

        #    Calculation of Purchase Tax
        if report_tax_ids:
            purchase_taxes = account_tax_env.search([('company_id', '=', data['company_id'][0]),
                                                     ('type_tax_use', '=', 'purchase'),
                                                     ('id', 'in', tuple(report_tax_ids))])
        else:
            purchase_taxes = account_tax_env.search([('company_id', '=', data['company_id'][0]),
                                                     ('type_tax_use', '=', 'purchase')])
        vendor_invoice_domain = domain + [('type', '=', 'in_invoice')]
        vendor_invoice_refund_domain = domain + [('type', '=', 'in_refund')]
        vendor_invoices = account_invoice_env.search(vendor_invoice_domain)
        vendor_refund_invoices = account_invoice_env.search(vendor_invoice_refund_domain)

        select_clause = 'select account_invoice_tax.tax_id , COALESCE(SUM(account_invoice_tax.amount), 0) as tax_amount,'\
                        ' COALESCE(SUM(account_invoice.amount_untaxed), 0) as invoice_amount '\
                        'from account_invoice_tax, account_invoice'

        if customer_invoices and sale_taxes:
            customer_invoice_ids = customer_invoices.ids
            sale_taxes_ids = sale_taxes.ids
            if len(sale_taxes_ids) == 1:
                tax_where_clause = 'tax_id=' + str(sale_taxes_ids[0])
            else:
                tax_where_clause = 'tax_id in ' + str(tuple(sale_taxes_ids))
            if len(customer_invoice_ids) == 1:
                invoice_where_clause = 'invoice_id=' + str(customer_invoice_ids[0])
            else:
                invoice_where_clause = 'invoice_id in ' + str(tuple(customer_invoice_ids))
            self._cr.execute(select_clause + ' where ' + tax_where_clause + ' and ' +
                             invoice_where_clause +
                             ' and account_invoice_tax.invoice_id=account_invoice.id'
                             ' group by account_invoice_tax.tax_id '
                             )
            sale_result = self._cr.dictfetchall()
            self._cr.execute("select tax_id, invoice_line_id from account_invoice_line_tax where tax_id not in "
                             "(select account_invoice_tax.tax_id from account_invoice_tax,account_tax  "
                             "where account_invoice_tax.tax_id in "+str(tuple(sale_taxes_ids))+")"
                             " and tax_id in "+str(tuple(sale_taxes_ids)))
            tax_code_from_invoice_lines = self._cr.dictfetchall()
            for tax_code in tax_code_from_invoice_lines:
                line = {}
                self._cr.execute("Select COALESCE(sum(price_subtotal),0.0) from account_invoice_line,"
                                 "account_invoice_line_tax where "
                                 "account_invoice_line.id=account_invoice_line_tax.invoice_line_id"
                                 " and account_invoice_line_tax.tax_id="+str(tax_code.get('tax_id')))
                invoice_line_total = self._cr.fetchone()
                tax = self.env['account.tax'].browse(tax_code.get('tax_id'))
                line.update({'amount_untaxed': invoice_line_total[0],
                             'tax_code': tax.name,
                             'tax_description': tax.description,
                             'taxed_amount': 0.0})
                tax_wise_data_list_sale.append(line)
            if customer_refund_invoices:
                customer_refund_invoice_ids = customer_refund_invoices.ids
                if len(customer_refund_invoice_ids) == 1:
                    refund_invoice_where_clause = 'account_invoice_tax.invoice_id=' + str(customer_refund_invoice_ids[0])
                else:
                    refund_invoice_where_clause = 'account_invoice_tax.invoice_id in ' + str(tuple(customer_refund_invoice_ids))
                self._cr.execute(select_clause + ' where ' + tax_where_clause + ' and ' +
                             refund_invoice_where_clause +
                             ' and account_invoice_tax.invoice_id=account_invoice.id'
                             ' group by account_invoice_tax.tax_id ')
                sale_refund_result = self._cr.dictfetchall()
            for record in sale_result:
                tax_wise_data = {}
                tax_obj = account_tax_env.browse(record['tax_id'])
                tax_wise_data['tax_code'] = tax_obj.name
                tax_wise_data['tax_description'] = tax_obj.description
                if sale_refund_result:
                    for data in sale_refund_result:
                        tax_wise_data['amount_untaxed'] = record['invoice_amount'] - data['invoice_amount'] \
                            if data['tax_id'] == record['tax_id'] else record['invoice_amount']
                        tax_wise_data['taxed_amount'] = record['tax_amount'] - data['tax_amount']\
                            if data['tax_id'] == record['tax_id'] else record['tax_amount']
                else:
                    tax_wise_data['amount_untaxed'] = record['invoice_amount']
                    tax_wise_data['taxed_amount'] = record['tax_amount']
                tax_wise_data_list_sale.append(tax_wise_data)
            res.update({'Sale': tax_wise_data_list_sale})

        if vendor_invoices and purchase_taxes:
            vendor_invoice_ids = vendor_invoices.ids
            purchase_taxes_ids = purchase_taxes.ids
            if len(purchase_taxes_ids) == 1:
                tax_where_clause = 'tax_id=' + str(purchase_taxes_ids[0])
            else:
                tax_where_clause = 'tax_id in ' + str(tuple(purchase_taxes_ids))
            if len(vendor_invoice_ids) == 1:
                invoice_where_clause = ' account_invoice_tax.invoice_id=' + str(vendor_invoice_ids[0])
            else:
                invoice_where_clause = ' account_invoice_tax.invoice_id in ' + str(tuple(vendor_invoice_ids))
            self._cr.execute(select_clause + ' where ' + tax_where_clause + ' and ' +
                             invoice_where_clause +
                             ' and account_invoice_tax.invoice_id=account_invoice.id'
                             ' group by account_invoice_tax.tax_id '
                             )
            purchase_result = self._cr.dictfetchall()
            self._cr.execute("select tax_id, invoice_line_id from account_invoice_line_tax where tax_id not in "
                             "(select account_invoice_tax.tax_id from account_invoice_tax,account_tax  "
                             "where account_invoice_tax.tax_id in "+str(tuple(purchase_taxes_ids))+")"
                             " and tax_id in "+str(tuple(purchase_taxes_ids)))
            tax_code_from_invoice_lines = self._cr.dictfetchall()
            for tax_code in tax_code_from_invoice_lines:
                line = {}
                self._cr.execute("Select COALESCE(sum(price_subtotal),0.0) from account_invoice_line,"
                                 "account_invoice_line_tax where "
                                 "account_invoice_line.id=account_invoice_line_tax.invoice_line_id"
                                 " and account_invoice_line_tax.tax_id="+str(tax_code.get('tax_id')))
                invoice_line_total = self._cr.fetchone()
                tax = self.env['account.tax'].browse(tax_code.get('tax_id'))
                line.update({'amount_untaxed': invoice_line_total[0],
                             'tax_code': tax.name,
                             'tax_description': tax.description,
                             'taxed_amount': 0.0})
                tax_wise_data_list_purchase.append(line)
            if vendor_refund_invoices:
                vendor_refund_invoice_ids = vendor_refund_invoices.ids
                if len(customer_refund_invoice_ids) == 1:
                    refund_vendor_invoice_where_clause = 'account_invoice_tax.invoice_id=' + str(vendor_refund_invoice_ids[0])
                else:
                    refund_vendor_invoice_where_clause = 'account_invoice_tax.invoice_id in ' + str(tuple(vendor_refund_invoice_ids))
                self._cr.execute(select_clause + ' where ' + tax_where_clause + ' and ' +
                             refund_vendor_invoice_where_clause +
                             ' and account_invoice_tax.invoice_id=account_invoice.id'
                             ' group by account_invoice_tax.tax_id ')
                purchase_refund_result = self._cr.dictfetchall()
            for record in purchase_result:
                tax_wise_data = {}
                tax_obj = account_tax_env.browse(record['tax_id'])
                tax_wise_data['tax_code'] = tax_obj.name
                tax_wise_data['tax_description'] = tax_obj.description
                if purchase_refund_result:
                    for data in purchase_refund_result:
                        tax_wise_data['amount_untaxed'] = record['invoice_amount'] - data['invoice_amount']\
                            if data['tax_id'] == record['tax_id'] else record['invoice_amount']
                        tax_wise_data['taxed_amount'] = record['tax_amount'] - data['tax_amount']\
                            if data['tax_id'] == record['tax_id'] else record['tax_amount']
                else:
                    tax_wise_data['amount_untaxed'] = record.get('invoice_amount', 0.0)
                    tax_wise_data['taxed_amount'] = record.get('tax_amount', 0.0)
                tax_wise_data_list_purchase.append(tax_wise_data)
            res.update({'Purchase': tax_wise_data_list_purchase})
        if not res.get('Sale') and not res.get('Purchase'):
            raise Warning("No Data found for both Sales Tax And Purchase Tax!")
        return res

    @api.multi
    def render_html(self, data):
        sale_totals = {}
        purchase_totals = {}
        sale_untaxed_total = 0.0
        sale_tax_total = 0.0
        purchase_untaxed_total = 0.0
        purchase_tax_total = 0.0
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        tax_lines = self.get_tax_lines(data.get('form'))
        sale_tax_lines = tax_lines['Sale']
        purchase_tax_lines = tax_lines['Purchase']
        for val in sale_tax_lines:
            sale_untaxed_total += val.get('amount_untaxed', 0.0)
            sale_tax_total += val.get('taxed_amount', 0.0)
        sale_totals['sale_untaxed_total'] = sale_untaxed_total
        sale_totals['sale_tax_total'] = sale_tax_total

        for rec in purchase_tax_lines:
            purchase_untaxed_total += rec.get('amount_untaxed', 0.0)
            purchase_tax_total += rec.get('taxed_amount', 0.0)
        purchase_totals['purchase_untaxed_total'] = purchase_untaxed_total
        purchase_totals['purchase_tax_total'] = purchase_tax_total
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Date': fields.date.today(),
            'sale_tax_lines': sale_tax_lines,
            'purchase_tax_lines': purchase_tax_lines,
            'sale_totals': sale_totals,
            'purchase_totals': purchase_totals
        }
        return self.env['report'].render('ia_au_gst_reporting.report_tax_gst_code_wise', docargs)
