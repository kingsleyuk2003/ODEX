# -*- coding: utf-8 -*-
# © 2016 Jérôme Guerriat
# © 2016 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
from openerp import api, fields, models, tools


class HRHolidays(models.Model):
    _inherit = 'hr.holidays'

    is_batch = fields.Boolean(default=False)

    # Replace XML onchange with api.onchange for more functionality
    @api.onchange('employee_id')
    def onchange_employee(self):
        return super(HRHolidays, self).onchange_employee(self.employee_id.id)

    @api.onchange('date_from', 'employee_id')
    def date_from_onchange(self):
        if self.type == 'add':
            return
        self.onchange_user_tz('date_from')

    @api.onchange('date_to', 'employee_id')
    def date_to_onchange(self):
        if self.type == 'add':
            return
        self.onchange_user_tz('date_to')

    # Read dates in user timezone
    def onchange_user_tz(self, type_change):
        if not self.date_to or not self.date_from:
            return

        date_from_user_tz = self.change_to_user_tz(self.date_from)
        date_to_user_tz = self.change_to_user_tz(self.date_to)
        # call original odoo function with correct timezone
        if type_change == 'date_from':
            result = self.onchange_date_from(date_to_user_tz, date_from_user_tz)
        else:
            result = self.onchange_date_to(date_to_user_tz, date_from_user_tz)
        self.compute_days(result, date_from_user_tz, date_to_user_tz)

    def change_to_user_tz(self, date):
        """
        Take date and return it in the user timezone
        :param date:
        :return:
        """
        if not date:
            return False
        date_object = datetime.strptime(date,
                                        tools.DEFAULT_SERVER_DATETIME_FORMAT)
        date_user_tz = fields.Datetime.context_timestamp(self.sudo(self._uid),
                                                         date_object)
        date_user_tz_string = date_user_tz.strftime('%Y-%m-%d %H:%M:%S')
        return date_user_tz_string

    # Get date range with exact dates
    def daterange(self, date_from, date_to):
        DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        date_from = datetime.strptime(date_from, DATETIME_FORMAT)
        date_to = datetime.strptime(date_to, DATETIME_FORMAT)
        for n in range(int((date_to - date_from).days) + 1):
            yield date_from + timedelta(n)

    def compute_days(self, result, date_from, date_to):
        number_of_days = result['value']['number_of_days_temp']
        if self.employee_id:
            days_without_special_days = self.deduct_special_days(number_of_days)
            self.number_of_days_temp = days_without_special_days
        else:
            self.number_of_days_temp = number_of_days

    def deduct_special_days(self, number_of_days=0):

        days_to_deduct = 0
        company_id = self.employee_id.company_id
        special_days = self.get_special_days(self.date_from, self.date_to, company_id )

        for date in special_days:
            days_to_deduct += 1

        days_without_special_days = number_of_days - days_to_deduct
        return days_without_special_days

    def get_special_days(self, date_from, date_to, company_id):
        # retrieve public leaves in employee's company
        public_leave_ids = self.env['hr.public_holiday'].search([
            ('company_ids', 'in', company_id.id)]
        )
        deduct_saturday = company_id.deduct_saturday_in_leave
        deduct_sunday = company_id.deduct_sunday_in_leave

        special_days = {}

        # for each date in the selected period, check if a public holiday exists
        # and/or if we should deduct Saturday/Sunday
        for date in self.daterange(date_from, date_to):
            public_leave = public_leave_ids.filtered(
                lambda r: r.date == str(date.date()))
            if public_leave:
                special_days[date.date()] = 'Public Holiday: %s' \
                                                 % public_leave.name
            elif date.weekday() == 5 and deduct_saturday:
                special_days[date.date()] = 'Saturday'
            elif date.weekday() == 6 and deduct_sunday:
                special_days[date.date()] = 'Sunday'

        return special_days
