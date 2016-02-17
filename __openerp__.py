# -*- coding: utf-8 -*-
{
    'name': 'Australian GST Reporting',
    'version': '1.0',
    'depends': ['base', 'report', 'account_accountant', 'l10n_au'],
    'author': 'Ioppolo & Associates',
    'description': """
Australian GST Reporting
====================================
Generate Reports based on Tax Codes

    """,
    'website': 'http://ioppolo.com.au/',
    'category': 'Accounting',
    'sequence': 0,
    'demo': [],
    'test': [],
    'data': [#'ia_au_gst_reporting.xml',
             'data/gst_report_data.xml',
             'views/reports.xml',
             'views/tax_details_report_view.xml',
             'views/tax_gst_report_view.xml',
             'wizard/tax_gst_report_view.xml',
             'views/account_invoice_tax_view.xml',
             'wizard/open_tax_balances.xml',
             'views/tax_report_hierarchy_view.xml',
             'views/tax_gst_report_detailed_journal_wise.xml',
             'wizard/tax_excel_report.xml',
             'wizard/open_tax_journal_items.xml'
             ],
    'qweb': [],
    'installable': True,
    'application': True,
}
