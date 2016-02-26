# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import models, api
from openerp.exceptions import Warning
import tempfile
import logging
from ..report.tax_gst_report import report_tax_gst
import xlwt
from ..format_common_excel import font_style
import cStringIO


_logger = logging.getLogger(__name__)


class hierarchical_gst_report_excel(models.Model):
    _name = 'hierarchical.gst.report.excel'

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
            tax_report_obj = self.env['report.ia_au_gst_reporting.report_tax_gst'].with_context(used_context)
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
            report_obj = self.env['account.tax.report'].browse(datas['form']['account_report_id'][0])
            date_from = datas['form']['used_context']['date_from']
            date_to = datas['form']['used_context']['date_to']
            sheet.write_merge(1, 2, max_level - 1, max_level + 2,
                              report_obj.name, main_header)
            sheet.write_merge(4, 4, 1, 2, 'Date From', table_header)
            sheet.write_merge(4, 4, 3, 4, date_from if date_from else '', text_with_border)
            sheet.write_merge(4, 4, 6, 7, 'Date To', table_header)
            sheet.write_merge(4, 4, 8, 9, date_to if date_to else '', text_with_border)
            inv_amt_col_start = max_level + 1
            inv_amt_col_stop = max_level + 3
            tax_amt_col_start = max_level + 4
            tax_amt_col_stop = max_level + 6
            sheet.write_merge(6, 7, 0, max_level, 'Name', table_header)
            sheet.write_merge(6, 7, inv_amt_col_start, inv_amt_col_stop,
                              'Invoiced Amount\n(Tax Exclusive)', table_header)
            sheet.write_merge(6, 7, tax_amt_col_start, tax_amt_col_stop,
                              'Taxed Amount', table_header)
            row = 8
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
#             stream = cStringIO.StringIO()
            workbook.save(out_filename)
            excel_file = open(out_filename, 'rb')
            excel = excel_file.read()
            excel_file.close()

#             try:
#                 os.unlink(out_filename)
#             except (OSError, IOError), exc:
#                 _logger.error('Cannot remove file %s: %s', (out_filename, exc))
            return (excel, 'xls')
