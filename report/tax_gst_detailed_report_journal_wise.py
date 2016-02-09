# -*- coding: utf-8 -*-

import time
from openerp import api, fields, models
from openerp.exceptions import Warning


class tax_gst_detailed_report_journal_wise(models.AbstractModel):
    _name = 'report.ia_au_gst_reporting.tax_gst_detailed_report_journal_wise'

    def get_tax_lines(self, data):
        domain = []
        res = {'Purchase': [], 'Sale': []}
        report_obj = self.env['account.tax.report'].browse(
                                                data['account_report_id'][0])
        report_tax_ids = report_obj.tax_ids.ids
        account_tax_env = self.env['account.tax']
        account_invoice_env = self.env['account.invoice']
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

        tax_ids = []
        if customer_invoices and vendor_invoices:
            tax_ids = sale_taxes.ids + purchase_taxes.ids
        if not customer_invoices and vendor_invoices:
            tax_ids = purchase_taxes.ids
        if not vendor_invoices and customer_invoices:
            tax_ids = sale_taxes.ids
        dates = [data['date_from'], data['date_to']]
        if tax_ids and data.get('journal_wise'):
            if False in dates:
                query = "Select AIL.price_subtotal as price_subtotal, "\
                        " AIL.product_id as product_id, "\
                        "AIL.price_unit as price_unit,"\
                        "AIL.invoice_id as invoice_id,"\
                        " AILT.tax_id as tax_id,"\
                        " AI.journal_id as journal_id"\
                        " from account_invoice_line as AIL,"\
                        "account_invoice_line_tax as AILT, "\
                        "account_invoice as AI where "\
                        "AIL.id=AILT.invoice_line_id and AI.id=AIL.invoice_id"\
                        " and AI.state in ('open', 'paid')"\
                        " and AILT.tax_id in %s"
                params = (tuple(tax_ids),)
            else:
                query = "Select AIL.price_subtotal as price_subtotal,"\
                        " AIL.product_id as product_id, "\
                        "AIL.price_unit as price_unit,"\
                        "AIL.invoice_id as invoice_id,"\
                        " AILT.tax_id as tax_id,"\
                        " AI.journal_id as journal_id"\
                        " from account_invoice_line as AIL,"\
                        "account_invoice_line_tax as AILT, "\
                        "account_invoice as AI where "\
                        "AIL.id=AILT.invoice_line_id and AI.id=AIL.invoice_id"\
                        " and AI.state in ('open', 'paid')"\
                        " and AILT.tax_id in %s"\
                        " and AI.date_invoice>=%s and AI.date_invoice<=%s"
                params = (tuple(tax_ids),) + tuple(dates)
            self.env.cr.execute(query, params)
            invoiced_tax_lines = self._cr.dictfetchall()
            group_invoice = {}
            for rec in invoiced_tax_lines:
                if rec.get('journal_id') in group_invoice.keys():
                    existing_rec = group_invoice.get(rec.get('journal_id'))
                    if rec.get('tax_id') in existing_rec.keys():
                        existing_tax_rec = existing_rec.get(rec.get('tax_id'))
                        if rec.get('invoice_id') in existing_tax_rec.keys():
                            existing_inv_rec = existing_tax_rec.get(
                                                        rec.get('invoice_id'))
                            existing_inv_rec.append({'price_subtotal':
                                                     rec.get('price_subtotal'),
                                                     'price_unit':
                                                     rec.get('price_unit'),
                                                     'product_id':
                                                     rec.get('product_id')})
                            existing_tax_rec.update({rec.get('invoice_id'):
                                                     existing_inv_rec})
                        else:
                            existing_tax_rec.update({rec.get('invoice_id'):
                                                     [{'price_subtotal':
                                                   rec.get('price_subtotal'),
                                                       'price_unit':
                                                   rec.get('price_unit'),
                                                    'product_id':
                                                    rec.get('product_id')}]
                                                     })
#                         tax_rec_to_append = {'price_unit': rec.get('price_unit'),
#                                          'price_subtotal': rec.get('price_subtotal'),
#                                          'invoice_id': rec.get('invoice_id')}
#                         existing_tax_rec.append(tax_rec_to_append)
#                         existing_rec.update({rec.get('tax_id'): existing_tax_rec})
                    else:
                        existing_rec.update({rec.get('tax_id'):
                                             {rec.get('invoice_id'):
                                              [{'price_subtotal':
                                                rec.get('price_subtotal'),
                                               'price_unit':
                                               rec.get('price_unit'),
                                               'product_id':
                                               rec.get('product_id')}]
                                              }
                                             })
#                         existing_rec.update({rec.get('tax_id'):
#                                              [{'price_unit': rec.get('price_unit'),
#                                               'price_subtotal': rec.get('price_subtotal'),
#                                               'invoice_id': rec.get('invoice_id')}
#                                               ]})
                    group_invoice.update({rec.get('journal_id'): existing_rec})
                else:
                    group_invoice.update({rec.get('journal_id'):
                                          {rec.get('tax_id'):
                                           {rec.get('invoice_id'):
                                            [{'price_unit':
                                              rec.get('price_unit'),
                                              'price_subtotal':
                                              rec.get('price_subtotal'),
                                              'product_id':
                                              rec.get('product_id')}
                                             ]}
                                           }
                                          })
            for journal in group_invoice.keys():
                journal_line = {}
                tax_line_list = []
                journal_obj = self.env['account.journal'].browse(journal)
                journal_record = group_invoice.get(journal)
                journal_wise_price_subtotal = 0.0
                journal_wise_tax_amount = 0.0
                for tax in journal_record.keys():
                    tax_line = {}
                    invoice_line_details = []
                    tax_obj = self.env['account.tax'].browse(tax)
                    tax_record = journal_record.get(tax)
                    price_unit = 0.0
                    price_subtotal = 0.0
                    sum_amount = 0.0
                    for l in tax_record.keys():
                        invoice_record = tax_record.get(l)
                        invoice_price_unit = 0.0
#                         invoice_description = ''
                        invoice_rec = {}
                        invoice_obj = self.env['account.invoice'].browse(l)
                        self._cr.execute("SELECT COALESCE(amount, 0.0)"
                              " from account_invoice_tax where invoice_id=" +
                              str(l) + " and tax_id=" + str(tax))
                        tax_amount = self._cr.fetchone()
                        if tax_amount:
                            amount = tax_amount[0]
                        else:
                            amount = 0.0
                        for inv_rec in invoice_record:
                            invoice_rec = {}
                            product_obj = self.env['product.product'].browse(
                                                  inv_rec.get('product_id'))
                            if tax_obj.amount_type == 'percent' and not tax_obj.price_include:
                                tax_amount = (inv_rec.get('price_subtotal') * tax_obj.amount) / 100
                            elif tax_obj.price_include:
                                tax_amount = inv_rec.get('price_unit') - inv_rec.get('price_subtotal')
                            invoice_rec.update({'invoice_number': invoice_obj.number,
                                                'price_subtotal': inv_rec.get('price_subtotal'),
                                                'tax_amount': tax_amount,
                                                'invoice_description': product_obj.name})
                            invoice_line_details.append(invoice_rec)
#                             if invoice_record.index(inv_rec) != len(invoice_record) -1:
#                                 product_name = product_obj.name + ', '
#                             else:
#                                 product_name = product_obj.name
#                             invoice_description += product_name
                            invoice_price_unit += inv_rec.get('price_unit')
                            price_unit += inv_rec.get('price_unit')
                            price_subtotal += inv_rec.get('price_subtotal')

                        sum_amount += amount
#                         invoice_rec.update({'invoice_number':
#                                             invoice_obj.number,
#                                             'price_subtotal':
#                                             price_subtotal,
#                                             'tax_amount': amount,
#                                             'invoice_description':
#                                             invoice_description})
#                         invoice_line_details.append(invoice_rec)
                    t_dic = {'price_subtotal': price_subtotal,
                             'tax_amount': sum_amount,
                             'name': tax_obj.name,
                             'description': tax_obj.description,
                             'invoice_details': invoice_line_details}
                    tax_line.update(t_dic)
                    tax_line_list.append(tax_line)
                    journal_wise_price_subtotal += price_subtotal
                    journal_wise_tax_amount += sum_amount
                journal_line.update({'name': journal_obj.name,
                                     'tax_lines': tax_line_list,
                                     'total_amount': journal_wise_price_subtotal,
                                     'total_tax_amount': journal_wise_tax_amount})
                if journal_obj.type == 'sale':
                    sale_list = res.get('Sale')
                    sale_list.append(journal_line)
                    res.update({'Sale': sale_list})
                elif journal_obj.type == 'purchase':
                    purchase_list = res.get('Purchase')
                    purchase_list.append(journal_line)
                    res.update({'Purchase': purchase_list})
        if not res.get('Sale') and not res.get('Purchase'):
            raise Warning("No Data found for both Sales Tax And Purchase Tax!")
        return res

    @api.multi
    def render_html(self, data):
        sale_totals = {}
        purchase_totals = {}
        sale_price_subtotal = 0.0
        sale_tax_total = 0.0
        purchase_untaxed_total = 0.0
        purchase_tax_total = 0.0
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        tax_lines = self.get_tax_lines(data.get('form'))
        sale_tax_lines = tax_lines['Sale']
        purchase_tax_lines = tax_lines['Purchase']
        for val in sale_tax_lines:
            for line in val.get('tax_lines'):
                sale_price_subtotal += line.get('price_subtotal')
                sale_tax_total += line.get('tax_amount')
        sale_totals['sale_untaxed_total'] = sale_price_subtotal
        sale_totals['sale_tax_total'] = sale_tax_total

        for rec in purchase_tax_lines:
            for line in rec.get('tax_lines'):
                purchase_untaxed_total += line.get('price_subtotal')
                purchase_tax_total += line.get('tax_amount')
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
                'ia_au_gst_reporting.tax_gst_detailed_report_journal_wise',
                docargs)
