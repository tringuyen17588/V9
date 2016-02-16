# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import models, fields, api
from openerp.exceptions import Warning
import tempfile
from ..report.tax_gst_detailed_report_journal_wise import tax_gst_detailed_report_journal_wise
import xlwt
from ..format_common_excel import font_style
import os
import logging

_logger = logging.getLogger(__name__)


class detailed_gst_report_journal_lines(models.Model):
    _name = 'detailed.gst.report.journal.lines'

    @api.multi
    def print_excel_report(self, data):
        datas = data
        workbook = xlwt.Workbook(style_compression=2)
        out_filename = tempfile.mktemp(suffix=".xls", prefix="drishti.tmp.")
        company = self.env['res.company'].browse(data['form']['company_id'][0])
        if company.currency_id:
            currency = company.currency_id.symbol
        else:
            currency = False
        if datas['form'].get('account_report_id'):
            used_context = datas['form']['used_context']
            data = {'account_report_id': [datas['form']['account_report_id'][0]],
                    'used_context': dict(used_context,
                                         lang=self.env.context.get('lang', 'en_US')
                                         )}
            tax_report_obj = self.env['report.ia_au_gst_reporting.tax_gst_detailed_report_journal_wise'].with_context(used_context)
            res = tax_gst_detailed_report_journal_wise.get_tax_lines(tax_report_obj, datas['form'])
            workbook = xlwt.Workbook()
            text_in_bold = font_style(bold=1, border=1)
            text_with_border = font_style(border=1)
            amount_bold = font_style(position='right', bold=1, border=1)
            amount_normal = font_style(position='right', border=1)
            main_header = font_style(position='center', bold=1,
                                     border=1, color='grey')
            table_header = font_style(position='center', bold=1, border=1,
                                      color='grey')
            table_header_left = font_style(position='left', bold=1, border=1,
                                      color='grey')
            text_in_bold_and_large = font_style(position='left', bold=1,
                                                font_height=200, border=1)
            sheet = workbook.add_sheet('GST Report', cell_overwrite_ok=True)
            report_obj = self.env['account.tax.report'].browse(datas['form']['account_report_id'][0])
            date_from = datas['form']['used_context']['date_from']
            date_to = datas['form']['used_context']['date_to']
            sheet.write_merge(1, 2, 3, 7,
                              report_obj.name, main_header)
            sheet.write_merge(4, 4, 1, 2, 'Date From', table_header)
            sheet.write_merge(4, 4, 3, 4, date_from if date_from else '', text_with_border)
            sheet.write_merge(4, 4, 6, 7, 'Date To', table_header)
            sheet.write_merge(4, 4, 8, 9, date_to if date_to else '', text_with_border)

            row = 8
            sale_lines = res.get('Sale')
            purchase_lines = res.get('Purchase')
#             for key in res.keys():
            if sale_lines:
                total_tax_amount_sale = 0.0
                sheet.write_merge(row, row + 1, 0, 14, 'Sales', text_in_bold_and_large)
                row += 2
                for rec in sale_lines:
                    sheet.write_merge(row, row + 1, 1, 14, rec['name'], text_in_bold_and_large)
                    row += 2

                    sheet.write_merge(row, row + 1, 2, 4, 'Tax Code', table_header)
                    sheet.write_merge(row, row + 1, 5, 6,
                                      'Tax Code Description \n /Invoice Number', table_header)
                    sheet.write_merge(row, row + 1, 7, 8,
                                      'Invoice Description', table_header)
                    sheet.write_merge(row, row + 1, 9, 10,
                                      'Total Paid Amount\n(Sales Including Tax)', table_header)
                    sheet.write_merge(row, row + 1, 11, 12,
                                      'Original Amount\n(Sales Excluding Tax)', table_header)
                    sheet.write_merge(row, row + 1, 13, 14,
                                      'Paid Amount\n(Tax Amount)', table_header)

                    row += 2
                    for line in rec.get('tax_lines'):
                        sheet.write_merge(row, row + 1, 2, 4, line.get('name'), text_with_border)
                        sheet.write_merge(row, row + 1, 5, 14,
                                         line.get('description'), text_with_border)

                        row += 2
                        for inv_line in line.get('invoice_details'):
                            sheet.write_merge(row, row + 1, 5, 6,
                                              inv_line.get('invoice_number'), text_with_border)
                            sheet.write_merge(row, row + 1, 7, 8,
                                              inv_line.get('invoice_description'), text_with_border)
                            sheet.write_merge(row, row + 1, 9, 10,
                                              inv_line.get('original_amount'), amount_normal)
                            sheet.write_merge(row, row + 1, 11, 12,
                                              inv_line.get('price_subtotal'), amount_normal)
                            sheet.write_merge(row, row + 1, 13, 14,
                                              inv_line.get('tax_amount'), amount_normal)
                            total_tax_amount_sale += inv_line.get('tax_amount')
                            row += 2
                        sheet.write_merge(row, row + 1, 2, 8,
                                          line.get('name') + ' - Total', text_in_bold)
                        sheet.write_merge(row, row + 1, 9, 10,
                                          line.get('invoice_original_amount'), amount_bold)
                        sheet.write_merge(row, row + 1, 11, 12,
                                          line.get('price_subtotal'), amount_bold)
                        sheet.write_merge(row, row + 1, 13, 14,
                                          line.get('tax_amount'), amount_bold)
                        tax_lines = rec.get('tax_lines')
                        len_tax_lines = len(tax_lines)
                        if tax_lines.index(line) != len_tax_lines - 1:
                            row += 3
                        else:
                            row += 2
                    sheet.write_merge(row, row + 1, 1, 8, rec.get('name') + ' - Total', 
                                      text_in_bold)
                    sheet.write_merge(row, row + 1, 9, 10, rec.get('journal_original_amount'), 
                                      amount_bold)
                    sheet.write_merge(row, row + 1, 11, 12, rec.get('total_amount'), 
                                      amount_bold)
                    sheet.write_merge(row, row + 1, 13, 14, rec.get('total_tax_amount'), 
                                      amount_bold)
                    row += 2
                sheet.write_merge(row, row + 1, 0, 12, 'Sales Tax - Total',
                                  text_in_bold)
                sheet.write_merge(row, row + 1, 13, 14, total_tax_amount_sale, 
                                  amount_bold)
                row += 3
            if purchase_lines:
                total_tax_amount_purchase = 0.0
                sheet.write_merge(row, row + 1, 0, 14, 'Purchase', text_in_bold_and_large)
                row += 2
                for rec in purchase_lines:
                    sheet.write_merge(row, row + 1, 1, 14, rec['name'], text_in_bold_and_large)
                    row += 2

                    sheet.write_merge(row, row + 1, 2, 4, 'Tax Code', table_header)
                    sheet.write_merge(row, row + 1, 5, 6,
                                      'Tax Code Description \n /Invoice Number', table_header)
                    sheet.write_merge(row, row + 1, 7, 8,
                                      'Invoice Description', table_header)
                    sheet.write_merge(row, row + 1, 9, 10,
                                      'Total Paid Amount\n(Sales Including Tax)', table_header)
                    sheet.write_merge(row, row + 1, 11, 12,
                                      'Original Amount\n(Sales Excluding Tax)', table_header)
                    sheet.write_merge(row, row + 1, 13, 14,
                                      'Paid Amount\n(Tax Amount)', table_header)

                    row += 2
                    for line in rec.get('tax_lines'):
                        sheet.write_merge(row, row + 1, 2, 4, line.get('name'), text_with_border)
                        sheet.write_merge(row, row + 1, 5, 14,
                                         line.get('description'), text_with_border)

                        row += 2
                        for inv_line in line.get('invoice_details'):
                            sheet.write_merge(row, row + 1, 5, 6,
                                              inv_line.get('invoice_number'), text_with_border)
                            sheet.write_merge(row, row + 1, 7, 8,
                                              inv_line.get('invoice_description'), text_with_border)
                            sheet.write_merge(row, row + 1, 9, 10,
                                              inv_line.get('original_amount'), amount_normal)
                            sheet.write_merge(row, row + 1, 11, 12,
                                              inv_line.get('price_subtotal'), amount_normal)
                            sheet.write_merge(row, row + 1, 13, 14,
                                              inv_line.get('tax_amount'), amount_normal)
                            total_tax_amount_purchase += inv_line.get('tax_amount')
                            row += 2
                        sheet.write_merge(row, row + 1, 2, 8,
                                          line.get('name') + ' - Total', text_in_bold)
                        sheet.write_merge(row, row + 1, 9, 10,
                                          line.get('invoice_original_amount'), amount_bold)
                        sheet.write_merge(row, row + 1, 11, 12,
                                          line.get('price_subtotal'), amount_bold)
                        sheet.write_merge(row, row + 1, 13, 14,
                                          line.get('tax_amount'), amount_bold)
                        tax_lines = rec.get('tax_lines')
                        len_tax_lines = len(tax_lines)
                        if tax_lines.index(line) != len_tax_lines - 1:
                            row += 3
                        else:
                            row += 2
                    sheet.write_merge(row, row + 1, 1, 8, rec.get('name') + ' - Total', 
                                      text_in_bold)
                    sheet.write_merge(row, row + 1, 9, 10, rec.get('journal_original_amount'), 
                                      amount_bold)
                    sheet.write_merge(row, row + 1, 11, 12, rec.get('total_amount'), 
                                      amount_bold)
                    sheet.write_merge(row, row + 1, 13, 14, rec.get('total_tax_amount'), 
                                      amount_bold)
                    row += 2
                sheet.write_merge(row, row + 1, 0, 12, 'Purchase Tax - Total',
                                  text_in_bold)
                sheet.write_merge(row, row + 1, 13, 14, total_tax_amount_purchase, 
                                  amount_bold)
                row += 3
            sheet.write_merge(row, row + 1, 0, 12,
                              'Total Tax Owed (Sales Tax - Purchase Tax):',
                              text_in_bold)
            sheet.write_merge(row, row + 1, 13, 14, total_tax_amount_sale - total_tax_amount_purchase,
                              amount_bold)
#             row = 8
#             col = 0
#             
#             sheet.write_merge(row, row, 0, 1,
#                                           rec.get('name'), text_with_border)

                      
#             stream = cStringIO.StringIO()
            workbook.save(out_filename)
            excel_file = open(out_filename, 'rb')
            excel = excel_file.read()
            excel_file.close()

            try:
                os.unlink(out_filename)
            except (OSError, IOError), exc:
                _logger.error('Cannot remove file %s: %s', (out_filename, exc))
            return (excel, 'xls')
