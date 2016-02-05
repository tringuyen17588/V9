# -*- coding: utf-8 -*-

import time
from openerp import api, fields, models
from openerp.exceptions import Warning


class tax_gst_report_detailed(models.AbstractModel):
    _name = 'report.ia_au_gst_reporting.tax_gst_report_detailed'

    def get_tax_lines(self, data):
        domain = []
        res = {'Purchase': [], 'Sale': []}
        report_obj = self.env['account.tax.report'].browse(data['account_report_id'][0])
        report_tax_ids = report_obj.tax_ids.ids
        account_tax_env = self.env['account.tax']
        account_invoice_env = self.env['account.invoice']
        dates = [data['date_from'], data['date_to']]
        if report_tax_ids:
            sale_taxes = account_tax_env.search([('company_id', '=',
                                                  data['company_id'][0]),
                                                 ('type_tax_use', '=', 'sale'),
                                                 ('id', 'in',
                                                  tuple(report_tax_ids))])
            purchase_taxes = account_tax_env.search([('company_id', '=',
                                                      data['company_id'][0]),
                                                     ('type_tax_use', '=',
                                                      'purchase'),
                                                     ('id', 'in',
                                                      tuple(report_tax_ids))])
        else:
            sale_taxes = account_tax_env.search([('company_id', '=',
                                                  data['company_id'][0]),
                                                 ('type_tax_use', '=', 'sale')]
                                                )
            purchase_taxes = account_tax_env.search([('company_id', '=',
                                                      data['company_id'][0]),
                                                     ('type_tax_use', '=',
                                                      'purchase')])

        if data['date_from']:
            domain.append(('date_invoice', '>=', data['date_from']))
        if data['date_to']:
            domain.append(('date_invoice', '<=', data['date_to']))
        if data['company_id']:
            domain.append(('company_id', '=', data['company_id'][0]))
        domain.append(('state', 'in', ['open', 'paid']))

        #    Calculation of Sales Tax
        customer_invoice_domain = domain + [('type', '=', 'out_invoice')]
        customer_invoices = account_invoice_env.search(customer_invoice_domain)

        vendor_invoice_domain = domain + [('type', '=', 'in_invoice')]
        vendor_invoices = account_invoice_env.search(vendor_invoice_domain)

        select_clause = 'select account_invoice_tax.tax_id , COALESCE(SUM(account_invoice_tax.amount), 0) as tax_amount,'\
                        ' COALESCE(SUM(account_invoice.amount_untaxed), 0) as invoice_amount '\
                        'from account_invoice_tax, account_invoice'

        if False in dates:
            query_tax_line = "select tax_id from "\
                            "account_invoice_line_tax where tax_id not in "\
                            "(select account_invoice_tax.tax_id from "\
                            "account_invoice_tax,account_tax"\
                            " where account_invoice_tax.tax_id in %s)"\
                            " and tax_id in %s group by tax_id"
        else:
            query_tax_line = "select tax_id from "\
                             "account_invoice_line_tax where tax_id not in "\
                             "(select account_invoice_tax.tax_id from "\
                             "account_invoice_tax,account_tax"\
                             " where account_invoice_tax.tax_id in %s )"\
                             " and tax_id in %s group by tax_id"
        tax_ids = []
        invoice_ids = []
        if customer_invoices and vendor_invoices:
            invoice_ids = customer_invoices.ids + vendor_invoices.ids
            tax_ids = sale_taxes.ids + purchase_taxes.ids
        if not customer_invoices and vendor_invoices:
            invoice_ids = vendor_invoices.ids
            tax_ids = purchase_taxes.ids
        if not vendor_invoices and customer_invoices:
            invoice_ids = customer_invoices.ids
            tax_ids = sale_taxes.ids
        if not data.get('journal_wise'):
            if tax_ids:
                tax_where_clause = 'tax_id=' + str(tax_ids[0]) if len(tax_ids) == 1 else 'tax_id in ' + str(tuple(tax_ids))
            if invoice_ids:
                invoice_where_clause = 'invoice_id=' + str(invoice_ids[0]) if len(invoice_ids) == 1 else 'invoice_id in ' + str(tuple(invoice_ids))
            if tax_ids and invoice_ids:
                self._cr.execute(select_clause + ' where ' + tax_where_clause + ' and ' +
                                 invoice_where_clause +
                                 ' and account_invoice_tax.invoice_id=account_invoice.id'
                                 ' group by account_invoice_tax.tax_id '
                                 )
                result = self._cr.dictfetchall()
                if False in dates:
                    self._cr.execute(query_tax_line, (tuple(tax_ids),
                                                      tuple(tax_ids)))
                    tax_code_from_invoice_lines = self._cr.dictfetchall()
                else:
                    self._cr.execute(query_tax_line, (tuple(tax_ids),
                                                      tuple(tax_ids)
                                                      ))
                    tax_code_from_invoice_lines = self._cr.dictfetchall()
                for tax_code in tax_code_from_invoice_lines:
                    line = {}
                    if False in dates:
                        self._cr.execute("Select COALESCE(sum(price_subtotal),0.0) from account_invoice_line,"
                                         "account_invoice_line_tax, account_invoice where "
                                         "account_invoice_line.id=account_invoice_line_tax.invoice_line_id"
                                         " and account_invoice.state in ('open', 'paid') "
                                         "and account_invoice_line.invoice_id=account_invoice.id"
                                         " and account_invoice_line_tax.tax_id=%s", 
                                         tuple(tax_code.get('tax_id')))
                    else:
                        self._cr.execute("Select COALESCE(sum(price_subtotal),0.0) from account_invoice_line,"
                                         "account_invoice_line_tax, account_invoice where "
                                         "account_invoice_line.id=account_invoice_line_tax.invoice_line_id"
                                         " and account_invoice.state in ('open', 'paid') "
                                         " and account_invoice.date_invoice>=%s"
                                         " and account_invoice.date_invoice<=%s"
                                         " and account_invoice_line.invoice_id=account_invoice.id"
                                         " and account_invoice_line_tax.tax_id=%s",
                                         tuple(dates) + tuple([tax_code.get('tax_id')],))
                    invoice_line_total = self._cr.fetchone()
                    tax = self.env['account.tax'].browse(tax_code.get('tax_id'))
                    line.update({'amount_untaxed': invoice_line_total[0],
                                 'tax_code': tax.name,
                                 'tax_description': tax.description,
                                 'taxed_amount': 0.0})
                    if tax.type_tax_use == 'sale':
                        ex_recs = res['Sale']
                        ex_recs.append(line)
                        res.update({'Sale': ex_recs})
                    elif tax.type_tax_use == 'purchase':
                        ex_recs = res['Purchase']
                        ex_recs.append(line)
                        res.update({'Purchase': ex_recs})

                for record in result:
                    tax_wise_data = {}
                    tax_obj = account_tax_env.browse(record['tax_id'])
                    tax_wise_data['tax_code'] = tax_obj.name
                    tax_wise_data['tax_description'] = tax_obj.description

                    tax_wise_data['amount_untaxed'] = record['invoice_amount']
                    tax_wise_data['taxed_amount'] = record['tax_amount']

                    if tax_obj.type_tax_use == 'sale':
                        sale_recs = res['Sale']
                        sale_recs.append(tax_wise_data)
                        res.update({'Sale': sale_recs})
                    elif tax_obj.type_tax_use == 'purchase':
                        purchase_recs = res['Purchase']
                        purchase_recs.append(tax_wise_data)
                        res.update({'Purchase': purchase_recs})
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
        return self.env['report'].render(
                'ia_au_gst_reporting.tax_gst_report_detailed', docargs)
