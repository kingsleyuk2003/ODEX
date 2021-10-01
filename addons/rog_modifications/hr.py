# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

import time
from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError
from openerp.exceptions import except_orm
from datetime import datetime
import calendar
from datetime import date
from dateutil import relativedelta
from openerp import exceptions
from openerp.tools import float_is_zero, float_compare,float_round, DEFAULT_SERVER_DATETIME_FORMAT




class HRHolidays(models.Model):
    _inherit = 'hr.holidays'



    @api.model
    def run_check_leave_allocation_hr_holidays(self):
        emp_obj = self.env['hr.employee']
        employees = emp_obj.search([])

        # today =  datetime.today()
        # day = today.day
        # month = today.month
        #
        # if day == 1 and month == 4 :
        grade_dict = {}
        for emp in employees:
            emp_grade = emp.grade_id
            annual_leave = emp_grade.annual_leave
            sick_leave = emp_grade.sick_leave
            casual_leave = emp_grade.casual_leave
            maternity_leave = emp_grade.maternity_leave
            paternity_leave = emp_grade.paternity_leave
            compensatory_off_co = emp_grade.compensatory_off_co
            leave_without_pay = emp_grade.leave_without_pay
            special_leave = emp_grade.special_leave
            education_leave = emp_grade.education_leave
            grade_dict = {'annual_leave': annual_leave, 'sick_leave':sick_leave, 'casual_leave':casual_leave, 'maternity_leave':maternity_leave, 'paternity_leave':paternity_leave , 'compensatory_off_co':compensatory_off_co, 'leave_without_pay' : leave_without_pay, 'special_leave':special_leave, 'education_leave':education_leave }

            holiday_status_obj = self.env['hr.holidays.status']
            res = False
            holidays_statuses = holiday_status_obj.search([])
            for holiday_status in holidays_statuses :
                if not holiday_status.grade_type :
                    raise UserError('Please Contact the Admin to link the Grade Type Columns to the Leave Types')

                self.env.cr.execute("select sum(number_of_days) from hr_holidays where state = 'validate' and employee_id = %s and holiday_status_id = %s" % (emp.id, holiday_status.id))
                dictAll = self.env.cr.dictfetchall()

                days_balance = dictAll[0]['sum']

                is_allow_accumulation = holiday_status.is_allow_accumulation

                num_days = grade_dict[holiday_status.grade_type]

                if holiday_status.grade_type == 'paternity_leave' and emp.gender != 'male':
                    num_days = 0
                if holiday_status.grade_type == 'maternity_leave' and emp.gender != 'female':
                    num_days = 0
                elif emp.gender != 'male':
                    emp.is_maternity_initially_leave_granted = True


                if num_days != 0:
                    if is_allow_accumulation and days_balance >= 120:
                        if (days_balance - 120) :
                            vals = {
                                'employee_id': emp.id,
                                'name': 'Auto System Leave Deduction for the 120days',
                                'holiday_type': 'employee',
                                'number_of_days_temp': (days_balance - 120),
                                'holiday_status_id': holiday_status.id,
                                'type': 'remove',
                            }
                            res = self.create(vals)
                            res.write({'state': 'validate'})
                    elif is_allow_accumulation and not days_balance :
                        if num_days:
                            vals  =  {
                                'employee_id': emp.id,
                                'name': 'Auto System Leave Allocation',
                                'holiday_type': 'employee',
                                'number_of_days_temp': num_days,
                                'holiday_status_id': holiday_status.id,
                                'type': 'add'}
                            res = self.create(vals)
                            res.write({'state': 'validate'})
                    elif is_allow_accumulation and days_balance :
                        if num_days :
                            vals  =  {
                                'employee_id': emp.id,
                                'name': 'Auto System Leave Allocation',
                                'holiday_type': 'employee',
                                'number_of_days_temp': num_days,
                                'holiday_status_id': holiday_status.id,
                                'type': 'add'}
                            res = self.create(vals)
                            res.write({'state': 'validate'})
                    elif days_balance:
                        if days_balance :
                            vals = {
                                'employee_id': emp.id,
                                'name': 'Auto System Leave Deduction',
                                'holiday_type': 'employee',
                                'number_of_days_temp': days_balance,
                                'holiday_status_id': holiday_status.id,
                                'type': 'remove',
                                }
                            res = self.create(vals)
                            res.write({'state': 'validate'})
                        if num_days:
                            vals = {
                                'employee_id': emp.id,
                                'name': 'Auto System Leave Allocation',
                                'holiday_type': 'employee',
                                'number_of_days_temp': num_days,
                                'holiday_status_id': holiday_status.id,
                                'type': 'add'}
                            res = self.create(vals)
                            res.write({'state': 'validate'})
                    elif num_days :
                        vals = {
                                'employee_id': emp.id,
                                'name': 'Auto System Leave Allocation',
                                'holiday_type': 'employee',
                                'number_of_days_temp': num_days,
                                'holiday_status_id': holiday_status.id,
                                'type': 'add'}
                        res = self.create(vals)
                        res.write({'state': 'validate'})


            if res:
                # Send Email
                user_ids = []
                group_obj = self.env.ref('rog_modifications.group_receive_hr_leave_allocation_email_notification')
                for user in group_obj.users:
                    user_ids.append(user.partner_id.id)

                if user_ids:
                    res.message_post('System has Generated a Leave Allocation/Deduction request' ,
                                     subject='A new Leave Allocation request has been generated ',
                                     partner_ids=[user_ids],
                                     subtype='mail.mt_comment')

        return True

    @api.model
    def run_check_leave_allocation_new_employee_hr_holidays(self):
        emp_obj = self.env['hr.employee']
        employees = emp_obj.search([('is_employee_initially_leave_granted', '=', False)])

        grade_dict = {}
        res = False
        for emp in employees:
            emp_grade = emp.grade_id
            annual_leave = emp_grade.annual_leave
            sick_leave = emp_grade.sick_leave
            casual_leave = emp_grade.casual_leave
            maternity_leave = emp_grade.maternity_leave
            paternity_leave = emp_grade.paternity_leave
            compensatory_off_co = emp_grade.compensatory_off_co
            leave_without_pay = emp_grade.leave_without_pay
            special_leave = emp_grade.special_leave
            education_leave = emp_grade.education_leave
            grade_dict = {'annual_leave': annual_leave, 'sick_leave': sick_leave, 'casual_leave': casual_leave,
                          'maternity_leave': maternity_leave, 'paternity_leave': paternity_leave,
                          'compensatory_off_co': compensatory_off_co, 'leave_without_pay': leave_without_pay,
                          'special_leave': special_leave, 'education_leave': education_leave}

            if not emp.is_employee_initially_leave_granted:

                    holiday_status_obj = self.env['hr.holidays.status']
                    res = False
                    holidays_statuses = holiday_status_obj.search([])
                    for holiday_status in holidays_statuses:
                        if not holiday_status.grade_type:
                            raise UserError('Please Contact the Admin to link the Grade Type Columns to the Leave Types')

                        num_days = grade_dict[holiday_status.grade_type]
                        if not emp.is_employee_initially_leave_granted :
                            self.run_check_leave_allocation_hr_holidays()
                            emp.is_employee_initially_leave_granted = True

        return True

    @api.model
    def run_check_leave_allocation_maternity_90days_hr_holidays(self):
        emp_obj = self.env['hr.employee']
        employees = emp_obj.search([('is_employee_initially_leave_granted', '=', True),('gender', '=', 'female')])

        # today =  datetime.today()
        # day = today.day
        # month = today.month
        #
        # if day == 1 and month == 4 :
        grade_dict = {}
        res = False
        for emp in employees:
            emp_grade = emp.grade_id
            annual_leave = emp_grade.annual_leave
            sick_leave = emp_grade.sick_leave
            casual_leave = emp_grade.casual_leave
            maternity_leave = emp_grade.maternity_leave
            paternity_leave = emp_grade.paternity_leave
            compensatory_off_co = emp_grade.compensatory_off_co
            leave_without_pay = emp_grade.leave_without_pay
            special_leave = emp_grade.special_leave
            education_leave = emp_grade.education_leave
            grade_dict = {'annual_leave': annual_leave, 'sick_leave': sick_leave, 'casual_leave': casual_leave,
                          'maternity_leave': maternity_leave, 'paternity_leave': paternity_leave,
                          'compensatory_off_co': compensatory_off_co, 'leave_without_pay': leave_without_pay,
                          'special_leave': special_leave, 'education_leave': education_leave}

            if not emp.is_maternity_initially_leave_granted:

                    holiday_status_obj = self.env['hr.holidays.status']
                    res = False
                    holidays_statuses = holiday_status_obj.search([])
                    for holiday_status in holidays_statuses:
                        if not holiday_status.grade_type:
                            raise UserError('Please Contact the Admin to link the Grade Type Columns to the Leave Types')

                        num_days = grade_dict[holiday_status.grade_type]
                        if holiday_status.grade_type == 'maternity_leave' and not emp.is_maternity_initially_leave_granted :
                            emp_date = emp.employment_date
                            if emp_date:
                                today = datetime.today()
                                date_diff = today - datetime.strptime(emp_date,'%Y-%m-%d')
                                days_worked = date_diff.days
                                if days_worked >= 90:
                                    num_days = grade_dict[holiday_status.grade_type]
                                    vals = {
                                        'employee_id': emp.id,
                                        'name': 'Auto System Maternity Leave Allocation',
                                        'holiday_type': 'employee',
                                        'number_of_days_temp': num_days,
                                        'holiday_status_id': holiday_status.id,
                                        'type': 'add'}
                                    res = self.create(vals)
                                    res.write({'state': 'validate'})
                                    emp.is_maternity_initially_leave_granted = True
        if res:
            # Send Email
            user_ids = []
            group_obj = self.env.ref('rog_modifications.group_receive_hr_leave_allocation_email_notification')
            for user in group_obj.users:
                user_ids.append(user.partner_id.id)

            if user_ids:
                res.message_post('System has Generated a Maternity Leave Allocation request',
                                 subject='A new Leave Allocation request has been generated ',
                                 partner_ids=[user_ids],
                                 subtype='mail.mt_comment')

        return True



    @api.multi
    def action_view_rule_adjustments(self):
        rule_adjustment_ids = self.mapped('rule_adjustment_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('rog_modifications.action_rule_adjustment_form')
        list_view_id = imd.xmlid_to_res_id('view_rule_adjustment_tree')
        form_view_id = imd.xmlid_to_res_id('view_rule_adjustment_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(rule_adjustment_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % rule_adjustment_ids.ids
        elif len(rule_adjustment_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = rule_adjustment_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.multi
    def action_disapprove(self,msg):
        res = super(HRHolidays,self).action_disapprove(msg)
        self.rule_adjustment_ids.unlink()
        return res

    @api.multi
    def action_validate(self):
        res = super(HRHolidays,self).action_validate()
        if self.type == 'add':
            return res

        is_lwp = self.holiday_status_id.is_lwp
        date_from = self.date_from
        date_to = self.date_to


        date_from = datetime.strptime(date_from,"%Y-%m-%d %H:%M:%S")
        month_from = date_from.month
        date_to = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S")
        month_to = date_to.month

        if month_to  > month_from + 1 :
            raise UserError(_('Please reduce the leave days to overlap maximum of two consecutive months'))

        if is_lwp and month_from == month_to:
            self.env['rule.adjustment'].create(
                {'employee_id': self.employee_id.id,
                 'rule_type': 'lwp',
                 'date_from': self.date_from,
                 'date_to': self.date_to,
                 'lrq_id' :self.id,
                 'state' : 'confirm',
                 })
        elif is_lwp:
            last_day = calendar.monthrange(date_from.year, date_from.month)[1]
            self.env['rule.adjustment'].create(
                {'employee_id': self.employee_id.id,
                 'rule_type': 'lwp',
                 'date_from': self.date_from,
                 'date_to': date(date_from.year,date_from.month,last_day),
                 'lrq_id': self.id,
                 'state': 'confirm',
                 })
            self.env['rule.adjustment'].create(
                {'employee_id': self.employee_id.id,
                 'rule_type': 'lwp',
                 'date_from': date(date_to.year,date_to.month,1),
                 'date_to':  self.date_to,
                 'lrq_id': self.id,
                 'state': 'confirm',
                 })



        return res


    @api.multi
    def action_approve(self):
        approver = self.pending_approver
        res = super(HRHolidays,self).action_approve()
        #send email notifications
        employee_id = self.employee_id
        overall_head_id = employee_id.overall_head_id
        reliever_id = employee_id.reliever_id
        hr_id = employee_id.hr_id
        date_from = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
        date_to = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
        user_names = ''
        if overall_head_id:
            user_names += overall_head_id.name + ", "
            msg = _(
                'The leave Request for %s, which starts from %s and ends on %s, has been finally approved by %s for %s day(s).') % (
                      employee_id.name, date_from, date_to, approver.name, self.number_of_days_temp)
            self.message_post(msg, subject=msg, partner_ids=[overall_head_id.id])

        if reliever_id :
            user_names += reliever_id.name + ", "
            msg = _(
                'This is to inform you that your colleague (%s) has taken a leave, which starts on %s and ends on %s, and has been finally approved by %s for %s day(s), and you (%s) have been assigned to relieve him of his duties during this period') % (
                      employee_id.name, date_from, date_to, approver.name, self.number_of_days_temp,reliever_id.name)
            self.message_post(msg, subject=msg, partner_ids=[reliever_id.id])

        if hr_id:
            user_names += hr_id.name + ", "
            msg = _(
                'The leave Request for %s, which starts from %s and ends on %s, has been finally approved by %s for %s day(s).') % (
                      employee_id.name, date_from, date_to, approver.name, self.number_of_days_temp)
            self.message_post(msg, subject=msg, partner_ids=[hr_id.id])

        self.env.user.notify_info('%s Will Be Notified by Email for leave Request' % (user_names))

        return res


    def _get_count_ra(self):
        self.update({
            'ra_count': len(set(self.rule_adjustment_ids))
        })

    rule_adjustment_ids = fields.One2many('rule.adjustment', 'lrq_id', string='Rule Adjustments')
    ra_count = fields.Integer(string='# of TCL', compute='_get_count_ra', readonly=True)




class HRHolidaysStatus(models.Model):
    _inherit = "hr.holidays.status"

    is_lwp = fields.Boolean(string='Is Leave Without Pay')
    is_allow_accumulation = fields.Boolean(string='Is Alllow Accumulation')
    grade_type = fields.Selection([('annual_leave', 'Annual Leave-AL (Days)'), ('sick_leave', 'Sick Leave-SL (Days)'),('casual_leave', 'Casual Leave-CL (Days)'), ('maternity_leave', 'Maternity Leave-ML (Days)'),('paternity_leave', 'Paternity Leave-PL (Days)'),('compensatory_off_co', 'Compensatory Off-CO'),('leave_without_pay', 'Leave without Pay-LWP (Days)'),('special_leave', 'Special Leave on Death of Spouse-SLDS (Days)'),('education_leave', 'Education Leave EL (Days)')], string='Grade Type')



class RuleAdjustment(models.Model):
    _name = 'rule.adjustment'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'name desc'


    def get_default_working_days(self,date_from,date_to):
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        date_diff = (date_to - date_from).days

        special_days =  self.env['hr.holidays'].get_special_days(date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                       date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                       self.env.user.company_id)
        return date_diff - len(special_days)

    def get_working_days(self,thedate):
        date_obj =  datetime.strptime(thedate, '%Y-%m-%d')

        # reference: https://stackoverflow.com/a/49506217
        # cal = calendar.Calendar()
        # working_days = len([x for x in calami.itermonthdays2(date_obj.year, date_obj.month) if x[0] != 0 and x[1] < 5])

        month_days = self.get_month_days(thedate)

        hr_holiday_obj = self.env['hr.holidays']
        last_day = calendar.monthrange(date_obj.year,date_obj.month)[1]
        date_from = date(date_obj.year,date_obj.month,1)
        date_to = date(date_obj.year,date_obj.month,last_day)
        #removes saturday and sunday and public holidays. So it is preferrable than the reference source above, because it can also deduct public holidays
        special_days = hr_holiday_obj.get_special_days(date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT),date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT),self.env.user.company_id)

        return month_days - len(special_days)


    def get_month_days(self,thedate):
        date_obj = datetime.strptime(thedate, '%Y-%m-%d')
        month_days = calendar.monthrange(date_obj.year,date_obj.month)
        return month_days[1]

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Sorry, you cannot delete a confirmed rule adjustment.'))
        return super(RuleAdjustment, self).unlink()

    @api.multi
    def action_draft(self):
        recs = self.filtered(lambda s: s.state in ['cancel'])
        recs.write({'state': 'draft'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})


    @api.multi
    def action_confirm(self):
        if self.date_from and self.date_to and  self.no_of_days <= 0  :
            raise UserError(_('You cant have zero or lesser number of default days'))

        user_ids = []
        user_names = ''
        group_serv_obj = self.env.ref('rog_modifications.group_receive_email_confirm_rog_rule_adjustment')
        for suser in group_serv_obj.users:
            user_names += suser.name + ", "
            user_ids.append(suser.partner_id.id)

        if user_ids:
            msg = _('A Rule Adjustment (%s) for Rule type (%s), has been confirmed by %s') % (
                    self.name, self.rule_type, self.env.user.name)
            self.message_post( msg,subject=msg, partner_ids=user_ids)

        self.env.user.notify_info('%s Will Be Notified by Email for Rule Adjustment' % (user_names))

        confirmed_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return self.write({'state': 'confirm', 'confirmed_by': self.env.user.id,
                           'confirmed_date': confirmed_date})

    @api.multi
    def action_approve(self):
        user_ids = []
        user_names = ''
        group_serv_obj = self.env.ref('rog_modifications.group_receive_email_approve_rog_rule_adjustment')
        for suser in group_serv_obj.users:
            user_names += suser.name + ", "
            user_ids.append(suser.partner_id.id)

        if user_ids:
            msg = _('A Rule Adjustment (%s) for Rule type (%s), has been approved by %s') % (
                self.name, self.rule_type, self.env.user.name)
            self.message_post(msg, subject=msg, partner_ids=user_ids)

        self.env.user.notify_info('%s Will Be Notified by Email for Rule Adjustment' % (user_names))

        approved_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return self.write({'state': 'approve', 'approved_by': self.env.user.id,
                           'approved_date': approved_date})


    def check_overlapping_rule(self,date_from,date_to,employee_id,rule_type):
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        # date_to_obj = datetime.strptime(date_from, '%Y-%m-%d')
        month_rule = date_from_obj.month

        self.env.cr.execute("select id from rule_adjustment where date_part('month',date_from) = %s and employee_id = %s and rule_type = '%s'" % (month_rule,employee_id.id,rule_type))
        dictAll = self.env.cr.dictfetchall()

        ids = [d['id'] for d in dictAll]
        ids.remove(self.id)
        ra_objs = self.browse(ids)

        for ra_obj in ra_objs:
            # ra_date_from =  datetime.strptime(ra_obj.date_from, '%Y-%m-%d')
            # ra_date_to = datetime.strptime(ra_obj.date_to, '%Y-%m-%d')
            if (date_from <=  ra_obj.date_from  and date_to >= ra_obj.date_from) or  (date_from <=  ra_obj.date_to and date_to >= ra_obj.date_to):
                raise UserError(_('Date Overlapping Rule Adjustment with other previous rule adjustments'))

        return

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('rule_rog_id_code') or 'New'
        res = super(RuleAdjustment, self).create(vals)
        date_to = datetime.strptime(res.date_to, '%Y-%m-%d')
        date_from = datetime.strptime(res.date_from, '%Y-%m-%d')
        date_diff = (date_to - date_from).days
        if date_to.month != date_from.month:
            raise UserError(_('The Date from and Date To fields must be in the same month'))
        if date_diff < 0:
            raise UserError(_(
                'Number of Days cannot be lesser than zero. Please check if the date to field is before the data from field'))

        #check overlapping days
        res.check_overlapping_rule(res.date_from,res.date_to,res.employee_id,res.rule_type)

        #disallow refund rules creation without parent id
        if (res.rule_type == 'absent_refund' or res.rule_type == 'lieo_refund' or  res.rule_type == 'lwpr_refund') and not res.ra_id :
            raise UserError(_('Sorry, you are not allowed to create this type of refund. Please perform this action on the specific refund adjustment'))
        return res

    @api.depends('date_from','date_to')
    def _compute_duration(self):
        for rec in self :
            if rec.date_from and rec.date_to :
                rec.no_of_days =  self.get_default_working_days(rec.date_from,rec.date_to) + 1
                rec.month_days = self.get_month_days(rec.date_from)
                rec.month_wdays = self.get_working_days(rec.date_from)


    @api.depends('rule_type','no_of_days','net_initial_salary','month_wdays','month_days')
    def compute_calculation(self):
        rule_type = self.rule_type
        month_wdays = self.month_wdays
        no_of_days = self.no_of_days
        month_days = self.month_days

        if rule_type in ['absent','lieo','absent_refund','lieo_refund','lwpr_refund'] and month_wdays and no_of_days :
            self.amount = (no_of_days * self.net_initial_salary) / self.month_wdays
        elif rule_type in ['lwp','lwpr_refund'] and month_days and no_of_days :
            self.amount = (no_of_days * self.net_initial_salary) / month_days
        else:
            self.amount = self.other_amount

    @api.multi
    def write(self, vals):
        other_amt = vals.get('other_amount',0)
        res = super(RuleAdjustment,self).write(vals)
        if other_amt:
            self.amount = other_amt
        date_to = datetime.strptime(self.date_to, '%Y-%m-%d')
        date_from = datetime.strptime(self.date_from, '%Y-%m-%d')
        date_diff = (date_to - date_from).days
        if date_to.month != date_from.month:
            raise UserError(_('The Date from and Date To fields must be in the same month'))
        if date_diff < 0:
            raise UserError(_(
                'Number of Days cannot be equal or lesser than zero. Please check if the date to field is before the data from field'))
        # check overlapping days
        self.check_overlapping_rule(self.date_from, self.date_to,self.employee_id,self.rule_type)

        # disallow refund rules creation without parent id
        if (self.rule_type == 'absent_refund' or self.rule_type == 'lieo_refund' or self.rule_type == 'lwpr_refund') and not self.ra_id:
            raise UserError(_(
                'Sorry, you are not allowed to create this type of refund. Please perform this action on the specific refund adjustment'))

        return res

    @api.multi
    def btn_view_refund_par(self):
        ra_id = self.mapped('ra_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('rog_modifications.action_rule_adjustment_form')
        list_view_id = imd.xmlid_to_res_id('rog_modifications.view_rule_adjustment_tree')
        form_view_id = imd.xmlid_to_res_id('rog_modifications.view_rule_adjustment_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(ra_id) > 1:
            result['domain'] = "[('id','in',%s)]" % ra_id.id
        elif len(ra_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = ra_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def btn_view_refund_ra(self):
        refund_rule_ids = self.mapped('refund_rule_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('rog_modifications.action_rule_adjustment_form')
        list_view_id = imd.xmlid_to_res_id('rog_modifications.view_rule_adjustment_tree')
        form_view_id = imd.xmlid_to_res_id('rog_modifications.view_rule_adjustment_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(refund_rule_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % refund_rule_ids.ids
        elif len(refund_rule_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = refund_rule_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.depends('refund_rule_ids')
    def _compute_refund_rule_count(self):
        for rec in self:
            rec.refund_rule_count = len(rec.refund_rule_ids)

    @api.depends('ra_id')
    def _compute_parent_rule_count(self):
        for rec in self:
            rec.parent_rule_count = len(rec.ra_id)

    name = fields.Char(string='Name')
    employee_id = fields.Many2one('hr.employee',string='Employee')
    no_of_days  = fields.Float(string='Default Number of Days',compute='_compute_duration',store=True)
    month_days = fields.Float(string='No. of days in the month',compute='_compute_duration',store=True)
    month_wdays = fields.Float(string='No. of working days in the month (excluding public holidays)', compute='_compute_duration', store=True)
    amount = fields.Float(string='Amount',compute=compute_calculation,store=True)
    other_amount = fields.Float(string='Other Amount')
    net_initial_salary = fields.Float(string='Net Salary',related='employee_id.net_initial_salary',store=True)
    description = fields.Text(string='Note')
    department_id = fields.Many2one('hr.department',string='Department',related='employee_id.department_id',store=True)
    confirmed_by = fields.Many2one('res.users', string="Confirmed By")
    approved_by = fields.Many2one('res.users', string="Approved By")
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    confirmed_date = fields.Date(string="Confirmed Date")
    approved_date = fields.Date(string="Approved Date")
    rule_type = fields.Selection(
        [('absent', 'Absentism'), ('lieo', 'Late In / Early Out'), ('lwp', 'Leave Without Pay'),('absent_refund', 'Absentism Refund'),  ('lieo_refund', 'Late In / Early Out Refund'), ('lwpr_refund', 'Leave Without Pay Refund'),('other_refund', 'Other Refund'),('reward', 'Reward')],
        string='Rule Type', track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'),('approve', 'Approved'), ('cancel', 'Cancel')],
        default='draft', track_visibility='onchange')
    lrq_id = fields.Many2one('hr.holidays',string='Leave Request')
    is_refunded = fields.Boolean(string='Is Refunded')
    is_refund = fields.Boolean(string='Is Refund')
    refund_rule_count = fields.Integer(compute="_compute_refund_rule_count", string='# of Rule Adjustments',
                                          copy=False, default=0)
    refund_rule_ids = fields.One2many('rule.adjustment', 'ra_id', string='Children Rule Adjustment (s)')
    ra_id = fields.Many2one('rule.adjustment', string='Parent Rule Adjustment')
    parent_rule_count = fields.Integer(compute="_compute_parent_rule_count", string='# of Parent Rule Adjustments',
                                       copy=False, default=0)


class HRLoan(models.Model):
    _inherit = 'hr.loan'

    @api.onchange('employee_id')
    def onchange_employee_rog_id(self):
        employee = self.employee_id
        if employee:
            self.update({
                'hr_department_id': employee.hr_department_id,
                'sbu_id': employee.sbu_id,
                'is_ssd_sbu': employee.is_ssd_sbu,
            })

    #reference: addons/ohrms_loan_accounting/models/hr_loan_acc.py:25  Cybrosys Technologies Pvt. Ltd.
    @api.multi
    def action_double_approve(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True

        """This create account move for request in case of double approval.
            """
        if not self.emp_account_id or not self.treasury_account_id or not self.journal_id:
            raise except_orm('Warning', "You must enter employee account, Treasury account and journal to approve ")
        if not self.loan_lines:
            raise except_orm('Warning', 'You must compute Loan Request before Approved')
        timenow = time.strftime('%Y-%m-%d')
        for loan in self:
            amount = loan.loan_amount
            loan_name = loan.employee_id.name
            reference = loan.name
            journal_id = loan.journal_id.id
            debit_account_id = loan.emp_account_id.id
            credit_account_id = loan.treasury_account_id.id
            if not loan.employee_id.user_id :
                raise UserError(_('Please contact the HR manager or Admin to link the employee to a user'))

            partner_id = loan.employee_id.user_id.partner_id
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'loan_id': loan.id,
                'partner_id': partner_id.id
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'loan_id': loan.id,
                'partner_id': partner_id.id
            }
            vals = {
                'name': 'Loan For' + ' ' + loan_name,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'partner_id': partner_id.id,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].with_context(ctx).create(vals)
            self.move_id = move
            move.post()
        self.write({'state': 'approve'})
        return True

    @api.model
    def _get_employee(self):
        return self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', default=_get_employee)

class SalaryAdvanceROG(models.Model):
    _inherit = 'salary.advance'

    @api.onchange('employee_id')
    def onchange_employee_rog_id(self):
        employee = self.employee_id
        if employee:
            self.update({
                'hr_department_id': employee.hr_department_id,
                'sbu_id': employee.sbu_id,
                'is_ssd_sbu': employee.is_ssd_sbu,
            })

    #reference: addons/rog_modifications/hr.py:583  Cybrosys Technologies Pvt. Ltd.
    @api.one
    def submit_to_manager(self):
        self.check_advance_constraint()
        self.state = 'submit'


    # reference: addons/ohrms_salary_advance/models/salary_advance.py:77  Cybrosys Technologies Pvt. Ltd.
    @api.one
    def approve_request(self):
        self.check_advance_constraint()
        self.state = 'waiting_approval'

    #reference: addons/ohrms_salary_advance/models/salary_advance.py:77  Cybrosys Technologies Pvt. Ltd.
    @api.one
    def check_advance_constraint(self):
        """This Approve the employee salary advance request."""
        emp_obj = self.env['hr.employee']
        address = emp_obj.browse([self.employee_id.id]).address_home_id
        if not address.id:
            raise except_orm('Error!', 'Define home address for employee')
        salary_advance_search = self.search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
                                             ('state', '=', 'approve')])
        current_month = datetime.strptime(self.date, '%Y-%m-%d').date().month

        other_month_advance = 0
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(each_advance.date, '%Y-%m-%d').date().month
            if current_month == existing_month:
                other_month_advance += each_advance.advance

        if not self.employee_contract_id:
            raise except_orm('Error!', 'Define a contract for the employee')
        struct_id = self.employee_contract_id.struct_id
        if  not struct_id.advance_date:
            raise except_orm('Error!', 'Advance days is not provided on the salary structure')

        if not self.advance:
            raise except_orm('Warning', 'Please Enter the Salary Advance amount')

        max_perc = 0
        net_initial_salary = self.employee_id.net_initial_salary
        if net_initial_salary > 100000 :
            max_perc = 30
        else:
            max_perc = 50

        adv = self.advance
        amt = (max_perc * self.employee_id.net_initial_salary) / 100

        total_month_adv = other_month_advance + adv
        if total_month_adv > amt and not self.exceed_condition:
            raise except_orm('Error!', 'You have exceeded your Advance for the month. You can only take maximum of %s. Please reduce the amount' % (amt))


        payslip_obj = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id),
                                                     ('state', '=', 'done'), ('date_from', '<=', self.date),
                                                     ('date_to', '>=', self.date)])
        if payslip_obj:
            raise except_orm('Warning', "This month salary already calculated")

        for slip in self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)]):
            slip_moth = datetime.strptime(slip.date_from, '%Y-%m-%d').date().month
            if current_month == slip_moth + 1:
                slip_day = datetime.strptime(slip.date_from, '%Y-%m-%d').date().day
                current_day = datetime.strptime(self.date, '%Y-%m-%d').date().day
                if current_day - slip_day < struct_id.advance_date:
                    raise exceptions.Warning(
                        _('Request can be done after "%s" Days From previous month salary') % struct_id.advance_date)


#../addons/ohrms_salary_advance/models/salary_advance.py:120  Cybrosys Technologies Pvt. Ltd.
    @api.one
    def approve_request_acc_dept(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True

        # salary_advance_search = self.search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
        #                                      ('state', '=', 'approve')])
        # current_month = datetime.strptime(self.date, '%Y-%m-%d').date().month
        # for each_advance in salary_advance_search:
        #     existing_month = datetime.strptime(each_advance.date, '%Y-%m-%d').date().month
        #     print current_month, existing_month
        #     if current_month == existing_month:
        #         raise except_orm('Error!', 'Advance can be requested once in a month')

        if not self.debit or not self.credit or not self.journal:
            raise except_orm('Warning', "You must enter Debit & Credit account and journal to approve ")
        if not self.advance:
            raise except_orm('Warning', 'You must Enter the Salary Advance amount')

        move_obj = self.env['account.move']
        timenow = time.strftime('%Y-%m-%d')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        for request in self:
            amount = request.advance
            request_name = request.employee_id.name
            reference = request.name
            journal_id = request.journal.id
            if not request.employee_id.user_id :
                raise UserError(_('Please contact the HR manager or Admin to link the employee to a user'))
            partner_id = request.employee_id.user_id.partner_id
            move = {
                'narration': 'Salary Advance Of ' + request_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'partner_id' : partner_id.id,
                'state': 'posted',
            }

            debit_account_id = request.debit.id
            credit_account_id = request.credit.id

            if debit_account_id:
                debit_line = (0, 0, {
                    'name': request_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'currency_id': self.currency_id.id,
                    'partner_id': partner_id.id,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            if credit_account_id:
                credit_line = (0, 0, {
                    'name': request_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'currency_id': self.currency_id.id,
                    'partner_id': partner_id.id,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            move.update({'line_ids': line_ids})
            move_id = move_obj.with_context(ctx).create(move)
            self.move_id = move_id
            self.state = 'approve'
            return True

    #reference: addons/ohrms_salary_advance/models/salary_advance.py:46   Cybrosys Technologies Pvt. Ltd.
    @api.multi
    def onchange_employee_id(self, employee_id):
        if employee_id:
            employee_obj = self.env['hr.employee'].browse(employee_id)
            department_id = employee_obj.department_id.id
            domain = [('employee_id', '=', employee_id)]
            contract_obj = self.env['hr.contract'].search([('employee_id','=',employee_id)])
            if contract_obj :
                return {'value': {'department': department_id,'employee_contract_id':contract_obj[0].id,'hr_department_id': employee_obj.hr_department_id,
                'sbu_id': employee_obj.sbu_id,
                'is_ssd_sbu': employee_obj.is_ssd_sbu,}, }


    @api.model
    def _get_employee(self):
        return self.env['hr.employee'].search([('user_id','=',self.env.user.id)])


    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')

    employee_id = fields.Many2one('hr.employee',default=_get_employee)







class ROGBand(models.Model):
    _name = 'hr.rog.band'
    _order = 'sequence'

    name = fields.Char(string='Band')
    sequence = fields.Integer(string='Sequence')

class ROGLocation(models.Model):
    _name = 'hr.rog.location'

    name = fields.Char(string='Location')

class ROGFunction(models.Model):
    _name = 'hr.rog.function'

    name = fields.Char(string='Function')

class ROGGrade(models.Model):
    _name = 'hr.rog.grade'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Designation/Grade Title')
    grade_code = fields.Char(string='Grade Code')
    annual_leave = fields.Integer(string='Annual Leave-AL (Days)')
    sick_leave = fields.Integer(string='Sick Leave-SL (Days)')
    casual_leave = fields.Integer(string='Casual Leave-CL (Days)')
    maternity_leave = fields.Integer(string='Maternity Leave-ML (Days)')
    paternity_leave = fields.Integer(string='Paternity Leave-PL (Days)')
    compensatory_off_co = fields.Integer(string='Compensatory Off-CO')
    leave_without_pay = fields.Integer(string='Leave without Pay-LWP (Days)')
    special_leave = fields.Integer(string='Special Leave on Death of Spouse-SLDS (Days)')
    education_leave = fields.Integer(string='Education Leave EL (Days)')

class HRApplicant(models.Model):
    _inherit = 'hr.applicant'

    no_of_year_experience = fields.Integer(string='Years of Experience')


class HRContract(models.Model):
    _inherit = 'hr.contract'

    wage = fields.Float(string='Wage', digits=(16, 2), required=False, help="Basic Salary of the employee")

class Children(models.Model):
    _name = 'hr.children.rog'

    name = fields.Char(string="Child's Name")
    dob = fields.Date(string="Child's DOB")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    emp_id = fields.Many2one('hr.employee',string='Employee')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    lga = fields.Char(string='LGA')
    tribe = fields.Char(string='Tribe')
    religion = fields.Char(string='Religion')
    grade_id = fields.Many2one('hr.rog.grade',string='Grade')
    location_id = fields.Many2one('hr.rog.location', string='Location')
    function_id = fields.Many2one('hr.rog.function', string='Function')
    band_id = fields.Many2one('hr.rog.band', string='Band')
    # qualification = fields.Char(string='Qualification')
    subject = fields.Char(string='Subject')
    institution = fields.Char(string='Institution')
    degree_class = fields.Char(string='Class of Degree')
    blood_group = fields.Char(string='Blood Group')
    genotype = fields.Char(string='Geno Type')
    level = fields.Char(string='Level')
    section = fields.Selection([('depot', 'Depot'), ('gmd', 'GMD Secretariat'), ('head','Head Office')], string='Section')


    nok_relationship = fields.Char(string='NOK Relationship')
    nok_address = fields.Char(string='NOK Address')
    state_id = fields.Char(string='State')
    spouse_name = fields.Char(string='Spouse Name')
    spouse_phone_number = fields.Char(string='Spouse Phone Number')
    spouse_address = fields.Char(string='Spouse Address')
    children_ids = fields.One2many('hr.children.rog', 'emp_id', string='Children(s)')
    fuel = fields.Float(string='Fuel Allowance')
    net_initial_salary = fields.Float(string='Initial Net Salary')
    gross_without_fuel = fields.Float(string="Gross Without Fuel")
    mgt_non_mgt = fields.Selection([
        ('mgt', 'MGT'),
        ('non_mgt', 'NonMGT')
    ], string='MGT/NonMGT')
    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'SHARED SERVICE'),
        ('sbu', 'SBU')
    ], string='Category')
    overall_head_id = fields.Many2one('res.partner',string='Overall Head')
    reliever_id = fields.Many2one('res.partner',string='Reliever')
    hr_id = fields.Many2one('res.partner',string='HR')
    is_maternity_initially_leave_granted = fields.Boolean(string='Maternity Leave Initially Granted')
    is_employee_initially_leave_granted = fields.Boolean(string='Is Employee Leave Initially Granted')
    is_voluntary_pension = fields.Boolean(string='Is Voluntary Pension')

class HRPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.onchange('employee_id')
    def onchange_employee_rog_id(self):
        employee = self.employee_id
        self.update({
            'function_id' : employee.function_id,
             'location_id' : employee.location_id,
             'mgt_non_mgt': employee.mgt_non_mgt,
             'band_id' : employee.band_id,
             'grade_id' : employee.grade_id,
             'hr_department_id' : employee.hr_department_id,
             'sbu_id': employee.sbu_id,
             'is_ssd_sbu' : employee.is_ssd_sbu,
        })




    @api.multi
    @api.one
    def compute_sheet(self):
        from_date  = self.date_from
        to_date = self.date_to
        #check if any rule adjustment is still in draft
        self.env.cr.execute("SELECT ID  FROM rule_adjustment as ra \
                           WHERE ra.employee_id = %s AND ra.state in ('draft','confirm') \
                             AND ra.date_from >= %s AND ra.date_to <= %s",
                        (self.employee_id.id, from_date, to_date))
        res_count = self.env.cr.fetchone()
        if res_count and len(res_count) > 0:
            raise UserError(_('Please approve or cancel any draft rule adjustment to proceed'))

        return  super(HRPayslip,self).compute_sheet()

    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
                            (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()
                return res and res[0] or 0.0

            def get_rog_calculation(self, rule_code,from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')

                #No need to check this because it brings the "Wrong python code defined for salary rule " instead of "Please confirm or cancel any draft rule adjustment to proceed" . So we have to do the test, somewhere
                #check if there are draft records
                # self.cr.execute("SELECT *  FROM rule_adjustment as ra \
                #                    WHERE ra.employee_id = %s AND ra.state = 'draft' \
                #                      AND ra.date_from >= %s AND ra.date_to <= %s AND ra.rule_type = %s",
                #                 (self.employee_id, from_date, to_date, rule_code))
                # res_count = self.cr.fetchone() or False
                # if res_count and len(res_count) > 0:
                #     raise UserError(_('Please confirm or cancel any draft rule adjustment to proceed'))

                self.cr.execute("SELECT sum(amount) as sum \
                            FROM rule_adjustment as ra \
                            WHERE ra.employee_id = %s AND ra.state = 'approve' \
                            AND ra.date_from >= %s AND ra.date_to <= %s AND ra.rule_type = %s",
                                (self.employee_id, from_date, to_date,rule_code))
                res = self.cr.fetchone()[0]
                return res or 0.0



        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.pool.get('hr.payslip')
        inputs_obj = self.pool.get('hr.payslip.worked_days')
        obj_rule = self.pool.get('hr.salary.rule')
        payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)
        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line

        categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
        worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
        payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)

        baselocaldict = {'categories': categories_obj, 'rules': rules_obj, 'payslip': payslip_obj, 'worked_days': worked_days_obj, 'inputs': input_obj}
        #get the ids of the structures on the contracts and their parent id as well
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        #get the rules of the structure and thier children
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    #create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    #blacklist this rule and its children
                    blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]

        result = [value for code, value in result_dict.items()]
        return result


    @api.multi
    def process_sheet(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(HRPayslip,self.with_context(ctx)).process_sheet()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')
    grade_id = fields.Many2one('hr.rog.grade', string='Grade')
    location_id = fields.Many2one('hr.rog.location', string='Location')
    function_id = fields.Many2one('hr.rog.function', string='Function')
    band_id = fields.Many2one('hr.rog.band', string='Band')
    mgt_non_mgt = fields.Selection([
        ('mgt', 'MGT'),
        ('non_mgt', 'NonMGT')
    ], string='Category')



class HrExpenseExtend(models.Model):
    _inherit = "hr.expense"

    @api.multi
    def action_move_create(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(HrExpenseExtend,self.with_context(ctx)).action_move_create()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')
    emp_id = fields.Many2one('hr.employee',string='Employee')
    name = fields.Char(string='Expense Title', readonly=True, required=True, states={'draft': [('readonly', False)]})


class HRDepartment(models.Model):
    _inherit = 'hr.department'

    is_show_other_apps = fields.Boolean(string='Show on Other Apps')

class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_leave_allowance = fields.Boolean(string='Is Leave Allowance',help='Helps to identify the leave allowance for payslip generation purposes')
    is_addition = fields.Boolean(string='Is Addition')
    is_deduction = fields.Boolean(string='Is Deduction')

class ResCompanyROG(models.Model):
    _inherit = "res.company"

    employer_code = fields.Char(string='Employer Code')
    header_data_hr = fields.Html(string='HR Payslip Header Data')
    accountant_group_id = fields.Many2one('emp.expense.group', string='Accountant Group')
