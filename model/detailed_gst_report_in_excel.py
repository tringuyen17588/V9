# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import models, fields, api
from openerp.exceptions import Warning
import tempfile
from ..report.tax_gst_report_detailed import tax_gst_report_detailed
import xlwt
from ..format_common_excel import font_style
import os
import logging

_logger = logging.getLogger(__name__)


class detailed_gst_report_excel(models.Model):
    _name = 'detailed.gst.report.excel'

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
            tax_report_obj = self.env['report.ia_au_gst_reporting.tax_gst_report_detailed'].with_context(used_context)
            res = tax_gst_report_detailed.get_tax_lines(tax_report_obj, datas['form'])
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
                              report_obj.name,
                              main_header)
            sheet.write_merge(4, 4, 1, 2, 'Date From', table_header)
            sheet.write_merge(4, 4, 3, 4, date_from if date_from else '', text_with_border)
            sheet.write_merge(4, 4, 6, 7, 'Date To', table_header)
            sheet.write_merge(4, 4, 8, 9, date_to if date_to else '', text_with_border)

            row = 8
            sale_lines = res.get('Sale')
            purchase_lines = res.get('Purchase')
#             for key in res.keys():
            total_tax_amount_purchase = 0.0
            total_tax_amount_sale = 0.0
            if sale_lines:
                total_tax_amount_sale = 0.0
                total_price_subtotal_sale = 0.0
                sheet.write_merge(row, row + 1, 0, 13, 'Sales', text_in_bold_and_large)
                row += 2
                sheet.write_merge(row, row + 1, 2, 4, 'Tax Code', table_header)
                sheet.write_merge(row, row + 1, 5, 7,
                                  'Tax Code Description', table_header)
                sheet.write_merge(row, row + 1, 8, 10,
                                  'Original Amount\n(Sales Excluding Tax)', table_header)
                sheet.write_merge(row, row + 1, 11, 13,
                                  'Paid Amount\n(Tax Amount)', table_header)
                row += 2
                for rec in sale_lines:
                    sheet.write_merge(row, row + 1, 2, 4, rec.get('tax_code'), text_with_border)
                    sheet.write_merge(row, row + 1, 5, 7,
                                      rec.get('tax_description'), text_with_border)
                    sheet.write_merge(row, row + 1, 8, 10,
                                      rec.get('amount_untaxed'), amount_normal)
                    total_price_subtotal_sale += rec.get('amount_untaxed')
                    sheet.write_merge(row, row + 1, 11, 13,
                                      rec.get('taxed_amount'), amount_normal)
                    total_tax_amount_sale += rec.get('taxed_amount')
                    row += 2
                sheet.write_merge(row, row + 1, 2, 7, 'Total', text_in_bold)
                sheet.write_merge(row, row + 1, 8, 10, total_price_subtotal_sale, amount_bold)
                sheet.write_merge(row, row + 1, 11, 13, total_tax_amount_sale, amount_bold)
                row += 3
            if purchase_lines:
                total_tax_amount_purchase = 0.0
                total_price_subtotal_purchase = 0.0
                sheet.write_merge(row, row + 1, 0, 13, 'Purchase', text_in_bold_and_large)
                row += 2
                sheet.write_merge(row, row + 1, 2, 4, 'Tax Code', table_header)
                sheet.write_merge(row, row + 1, 5, 7,
                                  'Tax Code Description', table_header)
                sheet.write_merge(row, row + 1, 8, 10,
                                  'Original Amount\n(Purchase Excluding Tax)', table_header)
                sheet.write_merge(row, row + 1, 11, 13,
                                  'Paid Amount\n(Tax Amount)', table_header)
                row += 2
                for rec in purchase_lines:
                    sheet.write_merge(row, row + 1, 2, 4, rec.get('tax_code'), text_with_border)
                    sheet.write_merge(row, row + 1, 5, 7,
                                      rec.get('tax_description'), text_with_border)
                    sheet.write_merge(row, row + 1, 8, 10,
                                      rec.get('amount_untaxed'), amount_normal)
                    total_price_subtotal_purchase += rec.get('amount_untaxed')
                    sheet.write_merge(row, row + 1, 11, 13,
                                      rec.get('taxed_amount'), amount_normal)
                    total_tax_amount_purchase += rec.get('taxed_amount')
                    row += 2
                sheet.write_merge(row, row + 1, 2, 7, 'Total', text_in_bold)
                sheet.write_merge(row, row + 1, 8, 10, total_price_subtotal_purchase, amount_bold)
                sheet.write_merge(row, row + 1, 11, 13, total_tax_amount_purchase, amount_bold)
                row += 3
            sheet.write_merge(row, row + 1, 0, 10,
                              'Total Tax Owed (Sales Tax - Purchase Tax):',
                              text_in_bold)
            sheet.write_merge(row, row + 1, 11, 13, total_tax_amount_sale - total_tax_amount_purchase,
                              amount_bold)

            workbook.save(out_filename)
            excel_file = open(out_filename, 'rb')
            excel = excel_file.read()
            excel_file.close()

            try:
                os.unlink(out_filename)
            except (OSError, IOError), exc:
                _logger.error('Cannot remove file %s: %s', (out_filename, exc))
            return (excel, 'xls')
