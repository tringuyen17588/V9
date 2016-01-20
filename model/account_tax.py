# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import models, api


class account_tax(models.Model):
    _inherit = 'account.tax'

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        if self._context.get('report_id'):
            report_id = self._context['report_id']
            report_obj = self.env['account.tax.report'].browse(report_id)
            result = False
            if not report_obj.children_ids:
                self._cr.execute("SELECT tax_id from "
                                 "account_tax_report_tax_code "
                                 "where report_id=" + str(report_id))
                result = self._cr.fetchall()
            if report_obj.children_ids:
                #    get all child reports 
                children = report_obj._get_children_by_order()
                self._cr.execute("SELECT tax_id from "
                                 "account_tax_report_tax_code "
                                 "where report_id in " + str(tuple(children.ids)))
                result = self._cr.fetchall()
            if result:
                ids = [rec[0] for rec in result]
                self._ids = ids
            if not result:
                self._ids = []
        return super(account_tax, self).read(fields=fields,
                                             load=load)
