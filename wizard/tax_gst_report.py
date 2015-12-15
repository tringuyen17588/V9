# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import models, fields, api
import datetime
from calendar import monthrange
from isoweek import Week
from dateutil.relativedelta import relativedelta
from openerp.exceptions import Warning


class GstReport(models.TransientModel):
    _name = 'gst.report'
    _description = "GST Report"
    
    period_select = fields.Selection(string='Select Period',
                                     selection=[('tax_quarter_1', 'Tax Quarter 1'),
                                                ('tax_quarter_2', 'Tax Quarter 2'),
                                                ('tax_quarter_3', 'Tax Quarter 3'),
                                                ('tax_quarter_4', 'Tax Quarter 4'),
                                                ('all_dates', 'All Dates'),
                                                ('today', 'Today'),
                                                ('this_week', 'This Week'),
                                                ('this_week_to_date', 'This Week to Date'),
                                                ('this_month', 'This Month'),
                                                ('this_month_to_date', 'This Month to Date'),
                                                ('this_tax_quarter', 'This Tax Quarter'),
                                                ('this_tax_quarter_to_date', 'This Tax Quarter to Date'),
                                                ('this_tax_year_to_date', 'This Tax Year to Date'),
                                                ('yesterday', 'Yesterday'),
                                                ('last_week', 'Last Week'),
                                                ('last_week_to_date', 'Last Week to Date'),
                                                ('last_month', 'Last Month'),
                                                ('last_month_to_date', 'Last Month to Date'),
                                                ('last_tax_quarter', 'Last Tax Quarter'),
                                                ('last_tax_quarter_to_date', 'Last Tax Quarter to Date'),
                                                ('last_tax_year', 'Last Tax Year'),
                                                ('custom', 'Custom')
                                                ],
                                     default='custom')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.users'].browse(self._uid).company_id)
    account_report_id = fields.Many2one('account.tax.report', string='Tax Reports', required=True)

    @api.onchange('period_select')
    def onchange_period_select(self):
        quarter_allocation = {1: [], 2: [], 3: [], 4: []}
        if self.period_select:
            date_today = datetime.date.today()
            current_month = date_today.month
            current_year = date_today.year
            current_week_number = date_today.isocalendar()[1]
            start_date_of_current_month = datetime.date(current_year, current_month, 1)
            last_week_sunday = Week(current_year, current_week_number - 1).sunday()
            last_week_saturday = Week(current_year, current_week_number - 1).saturday()
            current_week_sunday = Week(current_year, current_week_number).sunday()
            current_week_saturday = Week(current_year, current_week_number).saturday()
            next_saturday = Week(current_year, current_week_number + 1).saturday()
            account_config = self.env['account.config.settings'].search([])
            
            if self.period_select == 'all_dates':
                self.date_from = False
                self.date_to = False
            elif self.period_select == 'today':
                self.date_from = date_today
                self.date_to = date_today
            elif self.period_select == 'this_week':
                if date_today < current_week_sunday:
                    self.date_from = last_week_sunday
                    self.date_to = current_week_saturday
                elif date_today == current_week_sunday:
                    self.date_from = current_week_sunday
                    self.date_to = next_saturday
            elif self.period_select == 'this_week_to_date':
                self.date_to = date_today
                if date_today < current_week_sunday:
                    self.date_from = last_week_sunday
                elif date_today == current_week_sunday:
                    self.date_from = date_today
            elif self.period_select == 'this_month':
                self.date_from = start_date_of_current_month
                self.date_to = start_date_of_current_month + relativedelta(months=1) - relativedelta(days=1)
            elif self.period_select == 'this_month_to_date':
                self.date_from = start_date_of_current_month
                self.date_to = date_today
            elif self.period_select == 'yesterday':
                self.date_from = date_today - relativedelta(days=1)
                self.date_to = date_today - relativedelta(days=1)
            elif self.period_select == 'last_week':
                if date_today == current_week_sunday:
                    self.date_from = last_week_sunday
                    self.date_to = current_week_saturday
                else:
                    self.date_from = last_week_sunday - relativedelta(days=7)
                    self.date_to = last_week_saturday
            elif self.period_select == 'last_week_to_date':
                if date_today == current_week_sunday:
                    self.date_from = last_week_sunday
                    self.date_to = date_today
                else:
                    self.date_from = last_week_sunday - relativedelta(days=7)
                    self.date_to = date_today
            elif self.period_select == 'last_month':
                self.date_from = start_date_of_current_month - relativedelta(months=1)
                self.date_to = start_date_of_current_month - relativedelta(days=1)
            elif self.period_select == 'last_month_to_date':
                self.date_from = start_date_of_current_month - relativedelta(months=1)
                self.date_to = date_today
            elif self.period_select == 'custom':
                self.date_from = False
                self.date_to = False
            elif account_config:
                last_month_of_year = account_config.fiscalyear_last_month
                days_of_last_month = monthrange(current_year, last_month_of_year)[1]
                last_day_of_year = account_config.fiscalyear_last_day
                last_day_date = datetime.date(current_year, last_month_of_year, last_day_of_year)
                first_day_date = last_day_date - relativedelta(months=12) + relativedelta(days=1)
                first_month_of_year = first_day_date.month
                first_day_of_year = first_day_date.day
#                 start_date_of_current_month = datetime.date(current_year, current_month, first_day_of_year)
                for quarter in quarter_allocation:
                    month_list = quarter_allocation.get(quarter)
                    for r in range(1, 4):
                        if first_month_of_year > 12:
                            month_list.append({first_day_date.year + 1: first_month_of_year % 12})
                        else:
                            month_list.append({first_day_date.year: first_month_of_year})
                        first_month_of_year += 1
                    quarter_allocation.update({quarter: month_list})
                if quarter_allocation:
                    if self.period_select == 'tax_quarter_1':
                        quarter_start_year = quarter_allocation[1][0].keys()[0]
                        quarter_start_month = quarter_allocation[1][0].get(quarter_start_year)
                        days_in_quarter_start_month = monthrange(quarter_start_year, quarter_start_month)[1]
                        if days_in_quarter_start_month >= first_day_of_year:
                            date_from = datetime.date(quarter_start_year,
                                                      quarter_start_month,
                                                      first_day_of_year)
                        else:
                            date_from = datetime.date(quarter_start_year,
                                                      quarter_start_month,
                                                      days_in_quarter_start_month)
                        self.date_from = date_from
                        self.date_to = date_from + relativedelta(months=3) - relativedelta(days=1)
                    elif self.period_select == 'tax_quarter_2':
                        quarter_start_year = quarter_allocation[2][0].keys()[0]
                        quarter_start_month = quarter_allocation[2][0].get(quarter_start_year)
                        days_in_quarter_start_month = monthrange(quarter_start_year, quarter_start_month)[1]

                        if days_in_quarter_start_month >= first_day_of_year:
                            date_from = datetime.date(quarter_start_year,
                                                      quarter_start_month,
                                                      first_day_of_year)
                        else:
                            date_from = datetime.date(quarter_start_year,
                                                      quarter_start_month,
                                                      days_in_quarter_start_month)
                        self.date_from = date_from
                        self.date_to = date_from + relativedelta(months=3) - relativedelta(days=1)
                    elif self.period_select == 'tax_quarter_3':
                        quarter_start_year = quarter_allocation[3][0].keys()[0]
                        quarter_start_month = quarter_allocation[3][0].get(quarter_start_year)
                        days_in_quarter_start_month = monthrange(quarter_start_year, quarter_start_month)[1]

                        if days_in_quarter_start_month >= first_day_of_year:
                            date_from = datetime.date(quarter_start_year,
                                                       quarter_start_month,
                                                       first_day_of_year)
                        else:
                            date_from = datetime.date(quarter_start_year,
                                                      quarter_start_month,
                                                      days_in_quarter_start_month)
                        self.date_from = date_from
                        self.date_to = date_from + relativedelta(months=3) - relativedelta(days=1)

                    elif self.period_select == 'tax_quarter_4':
                        quarter_start_year = quarter_allocation[4][0].keys()[0]
                        quarter_start_month = quarter_allocation[4][0].get(quarter_start_year)
                        days_in_quarter_start_month = monthrange(quarter_start_year, quarter_start_month)[1]
                        if days_in_quarter_start_month >= first_day_of_year:
                            date_from = datetime.date(quarter_start_year,
                                                       quarter_start_month,
                                                       first_day_of_year)
                        else:
                            date_from = datetime.date(quarter_start_year,
                                                      quarter_start_month,
                                                      days_in_quarter_start_month)
                        self.date_from = date_from
                        self.date_to = date_from + relativedelta(months=3) - relativedelta(days=1)

                    elif self.period_select == 'this_tax_quarter':
                        for q_no, months in quarter_allocation.iteritems():
                            m_list = []
                            for m in months:
                                m_list.append(m.get(m.keys()[0]))
                            if current_month in m_list:
                                self.date_from = datetime.date(months[0].keys()[0], months[0].get(months[0].keys()[0]), first_day_of_year)
                                self.date_to = datetime.date(months[2].keys()[0], months[2].get(months[2].keys()[0]), last_day_of_year)
                    elif self.period_select == 'this_tax_quarter_to_date':
                        for q_no, months in quarter_allocation.iteritems():
                            m_list = []
                            for m in months:
                                m_list.append(m.get(m.keys()[0]))
                            if current_month in m_list:
                                self.date_from = datetime.date(months[0].keys()[0], months[0].get(months[0].keys()[0]), first_day_of_year)
                                self.date_to = date_today
                    elif self.period_select == 'this_tax_year_to_date':
                        self.date_from = first_day_date
                        self.date_to = date_today
                    
                    elif self.period_select == 'last_tax_quarter':
                        for q_no, months in quarter_allocation.iteritems():
                            m_list = []
                            for m in months:
                                m_list.append(m.get(m.keys()[0]))
                            if current_month in m_list:
                                self.date_to = datetime.date(months[2].keys()[0],
                                                             months[2].get(months[2].keys()[0]),
                                                             first_day_of_year) - relativedelta(days=1)
                                self.date_from = datetime.date(months[2].keys()[0],
                                                             months[2].get(months[2].keys()[0]),
                                                             first_day_of_year) - relativedelta(months=3)
                    elif self.period_select == 'last_tax_quarter_to_date':
                        for q_no, months in quarter_allocation.iteritems():
                            m_list = []
                            for m in months:
                                m_list.append(m.get(m.keys()[0]))
                            if current_month in m_list:
                                self.date_to = date_today
                                self.date_from = datetime.date(months[2].keys()[0],
                                                             months[2].get(months[2].keys()[0]),
                                                             first_day_of_year) - relativedelta(months=3)
                    elif self.period_select == 'last_tax_year':
                        self.date_from = first_day_date - relativedelta(months=12)
                        self.date_to = last_day_date - relativedelta(months=12)
                    else:
                        self.date_from = False
                        self.date_to = False
            else:
                raise Warning('Fiscal Year Last Day is not set!')

    def _build_contexts(self, data):
        result = {}
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['company_id'] = data['form']['company_id'] or False
        return result

    @api.multi
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to','company_id','account_tax_id','account_report_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        report_obj = self.env['account.tax.report'].browse(data['form']['account_report_id'][0])
        if report_obj.type == 'detailed_report':
            return self.env['report'].get_action(self, 'ia_au_gst_reporting.report_tax_gst_code_wise', data=data)
        else:
            return self.env['report'].get_action(self, 'ia_au_gst_reporting.report_tax_gst', data=data)
