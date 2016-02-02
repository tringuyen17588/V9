# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import models, fields, api
from ..report.tax_gst_report import report_tax_gst
import xlwt
import cStringIO
import base64
from ..format_common_excel import font_style


class TaxExcelReport(models.TransientModel):
    _name = 'tax.excel.report'

    report_id = fields.Many2one('account.tax.report', string='Report')
    excel_data = fields.Binary(string='Report Data', readonly=True)
    name = fields.Char(string='File Name')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self:
                self.env['res.users'].browse(self._uid).company_id)

    @api.multi
    def print_report(self):
        if self.company_id.currency_id:
            currency = self.company_id.currency_id.symbol
        else:
            currency = False
        if self.report_id:
            first_inv = self.env['account.invoice'].search([],
                                                       order='date_invoice asc',
                                                       limit=1)
            last_inv = self.env['account.invoice'].search([],
                                                      order='date_invoice desc',
                                                      limit=1)
            used_context = {'date_from': first_inv.date_invoice,
                            'date_to': last_inv.date_invoice}
            data = {'account_report_id': [self.report_id.id],
                    'used_context': dict(used_context,
                                         lang=self.env.context.get('lang', 'en_US')
                                         )}
            tax_report_obj = self.env['report.ia_au_gst_reporting.report_tax_gst']
            res = report_tax_gst.get_account_lines(tax_report_obj, data)
            workbook = xlwt.Workbook()
            text_in_bold = font_style(bold=1, border=1)
            text_with_border = font_style(border=1)
            amount_bold = font_style(position='right', bold=1, border=1)
            amount_normal = font_style(position='right', border=1)
            main_header = font_style(position='center', bold=1,
                                     border=1, color='grey')
            table_header = font_style(position='center', bold=1, border=1,
                                      color='grey')
            sheet = workbook.add_sheet('GST Report')
            row_column_list = []
            level = [x.get('level') for x in res]
            max_level = max(level)
            sheet.write_merge(1, 2, max_level - 1, max_level + 2,
                              self.report_id.name, main_header)
            inv_amt_col_start = max_level + 1
            inv_amt_col_stop = max_level + 3
            tax_amt_col_start = max_level + 4
            tax_amt_col_stop = max_level + 6
            sheet.write_merge(4, 5, 0, max_level, 'Name', table_header)
            sheet.write_merge(4, 5, inv_amt_col_start, inv_amt_col_stop,
                              'Invoiced Amount\n(Tax Exclusive)', table_header)
            sheet.write_merge(4, 5, tax_amt_col_start, tax_amt_col_stop,
                              'Taxed Amount', table_header)
            row = 6
            col = 0
            for rec in res:
                if rec.get('level') > 0:
                    col = rec.get('level') - 1
                    taxed_amount = rec.get('tax_amount')
                    taxed_amount = format(taxed_amount, '.2f')
                    invoiced_amount = rec.get('invoiced_amount', 0.0)
                    invoiced_amount = format(round(invoiced_amount, 2), '.2f')
                    if rec.get('level') != max_level:
                        sheet.write_merge(row, row + 1, col, max_level,
                                          rec.get('name'), text_in_bold)

                        sheet.write_merge(row, row + 1, tax_amt_col_start,
                                          tax_amt_col_stop,
                      currency + taxed_amount if currency else taxed_amount,
                                          amount_bold)
                        sheet.write_merge(row, row + 1, inv_amt_col_start,
                                          inv_amt_col_stop,
                      currency + invoiced_amount if currency else invoiced_amount,
                                          amount_bold)
                    else:
                        sheet.write_merge(row, row + 1, col, max_level,
                                          rec.get('name'), text_with_border)

                        sheet.write_merge(row, row + 1, tax_amt_col_start,
                                          tax_amt_col_stop,
                      currency + taxed_amount if currency else taxed_amount,
                                          amount_normal)
                        sheet.write_merge(row, row + 1, inv_amt_col_start,
                                          inv_amt_col_stop,
                  currency + invoiced_amount if currency else invoiced_amount,
                                          amount_normal)
                    row_column_list.append({'row': [row, row + 1],
                                            'col': [col, max_level]})
                    row += 2
            stream = cStringIO.StringIO()
            workbook.save(stream)
            self.write({'name': 'GST Report.xls',
                        'excel_data': base64.encodestring(stream.getvalue())})
            return {'name': 'GST Report',
                    'res_model': 'tax.excel.report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': self.id,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'show_button': True}}
        else:
            return {'name': 'GST Report',
                    'res_model': 'tax.excel.report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'show_button': True}}

