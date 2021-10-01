# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class IncidentReport(models.Model):
    _name = 'incident.report'
    _inherit = ['mail.thread']


    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_qhsse.group_receive_qhsse_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                '%s for (%s), which is being initiated by %s.') % (msg,
                                                                   self.name, self.env.user.name),
                              subject='%s' % (msg),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names, msg))


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('ir_code') or 'New'
        res = super(IncidentReport, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return


    @api.multi
    def button_submit(self):
        self.state = 'submit'
        self.email_dispatch('Submit')
        return


    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    date = fields.Date(string='Date')
    incident = fields.Text(string='Incident')
    alert_by_person = fields.Char(string='Alert by Person')
    alert_method = fields.Char(string='Method of Alert')
    time =  fields.Char(string='Time')
    location = fields.Char(string='Location')
    response_team = fields.Char(string='Response Team')
    description_detail = fields.Text(string='Description / Details')
    action_taken = fields.Text(string='Action Taken')
    material_used = fields.Text(string='Material Used')
    category = fields.Char(string='Category')
    recommendation = fields.Text(string='Recommendations')
    is_investigation = fields.Selection([('yes','Yes'),('no','No')])
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')



class QHSSEMeeting(models.Model):
    _name = 'qhsse.meeting'
    _inherit = ['mail.thread']

    @api.model
    def run_notify_qhsse_meeting(self):
        is_activate_qhsse_reminder = self.env.user.company_id.is_qhsse_reminder
        if is_activate_qhsse_reminder :
            days_offset_reminder = self.env.user.company_id.qhsse_reminder_days
            today = datetime.today()

            object = self.env['qhsse.meeting']
            records = object.search([('date', '<=',  datetime.today().strftime('%d-%m-%Y %H:%M:%S')),('state','=','activated')])
            for rec in records:
                expiry_date = datetime.strptime(rec.date,'%Y-%m-%d')
                start_reminder_date = expiry_date - timedelta(days=+days_offset_reminder)
                if today >=  start_reminder_date :
                    user_ids = []
                    group_obj = self.env.ref('rog_qhsse.group_receive_qhsse_email_notification')
                    for user in group_obj.users:
                        user_ids.append(user.id)
                    rec.message_unsubscribe_users(user_ids=user_ids)
                    rec.message_subscribe_users(user_ids=user_ids)
                    rec.message_post(_('FYI, There is a QHSSE Meeting Reminder for %s.') % (expiry_date.strftime('%d-%m-%Y')),
                                          subject='QHSSE Meeting Reminder' ,
                                          subtype='mail.mt_comment')

                    if today.strftime('%Y-%m-%d') == expiry_date.strftime('%Y-%m-%d'):
                        rec.state = 'deactivated'

        return True


    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_qhsse.group_receive_qhsse_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                '%s for (%s), which is being initiated by %s.') % (msg,
                                                                   self.name, self.env.user.name),
                              subject='%s' % (msg),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names, msg))


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('qhsse_code') or 'New'
        res = super(QHSSEMeeting, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return


    @api.multi
    def button_activate(self):
        self.state = 'activated'
        self.email_dispatch('Activated Reminder')
        return

    @api.multi
    def button_deactivate(self):
        self.state = 'deactivated'
        self.email_dispatch('DeActivated Reminder')
        return


    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    quarters = fields.Selection([('1st','1st'),('2nd','2nd'),('3rd','3rd'),('4th','4th')])
    month = fields.Selection([
        ('jan','January'),('feb','February'),('mar','March'),('apr','April'),('may','May'),('june','June'),('july','July'),('aug','August'),('sept','September'),('oct','October'),('nov','November'),('dec','December')
    ])
    date = fields.Date(string='Meeting Date')
    remark = fields.Text(string='Remarks')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('activated', 'Activated'),
        ('deactivated', 'DeActivated'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


class EmergencyDrill(models.Model):
    _name = 'emergency.drill'
    _inherit = ['mail.thread']

    @api.model
    def run_notify_emergency_drill(self):
        is_activate_emergency_drill_reminder = self.env.user.company_id.is_emergency_drill_reminder
        if is_activate_emergency_drill_reminder :
            days_offset_reminder = self.env.user.company_id.emergency_drill_reminder_days
            today = datetime.today()

            object = self.env['emergency.drill']
            records = object.search([('date', '<=',  datetime.today().strftime('%d-%m-%Y %H:%M:%S')),('state','=','activated')])
            for rec in records:
                expiry_date = datetime.strptime(rec.date,'%Y-%m-%d')
                start_reminder_date = expiry_date - timedelta(days=+days_offset_reminder)
                if today >=  start_reminder_date :
                    user_ids = []
                    group_obj = self.env.ref('rog_qhsse.group_receive_emergency_drill_email_notification')
                    for user in group_obj.users:
                        user_ids.append(user.id)
                    rec.message_unsubscribe_users(user_ids=user_ids)
                    rec.message_subscribe_users(user_ids=user_ids)
                    rec.message_post(_('FYI, There is a Emergency Drill Reminder for %s.') % (expiry_date.strftime('%d-%m-%Y')),
                                          subject='Emergency Drill Reminder' ,
                                          subtype='mail.mt_comment')

                    if today.strftime('%Y-%m-%d') == expiry_date.strftime('%Y-%m-%d'):
                        rec.state = 'deactivated'
        return True


    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_qhsse.group_receive_emergency_drill_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                '%s for (%s), which is being initiated by %s.') % (msg,
                                                                   self.name, self.env.user.name),
                              subject='%s' % (msg),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names, msg))


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('ed_code') or 'New'
        res = super(EmergencyDrill, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return


    @api.multi
    def button_activate(self):
        self.state = 'activated'
        self.email_dispatch('Activated Reminder')
        return

    @api.multi
    def button_deactivate(self):
        self.state = 'deactivated'
        self.email_dispatch('DeActivated Reminder')
        return


    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    year = fields.Char(string='Year')
    quarters = fields.Selection([('1st','1st'),('2nd','2nd'),('3rd','3rd'),('4th','4th')])
    month = fields.Selection([
        ('jan','January'),('feb','February'),('mar','March'),('apr','April'),('may','May'),('june','June'),('july','July'),('aug','August'),('sept','September'),('oct','October'),('nov','November'),('dec','December')
    ])
    date = fields.Date(string='Drill Date')
    remark = fields.Text(string='Remarks')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('activated', 'Activated'),
        ('deactivated', 'DeActivated'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


class SecurityMeeting(models.Model):
    _name = 'security.meeting'
    _inherit = ['mail.thread']

    @api.model
    def run_notify_security_meeting(self):
        is_activate_security_meeting_reminder = self.env.user.company_id.is_security_meeting_reminder
        if is_activate_security_meeting_reminder :
            days_offset_reminder = self.env.user.company_id.security_meeting_reminder_days
            today = datetime.today()

            object = self.env['security.meeting']
            records = object.search([('date', '<=',  datetime.today().strftime('%d-%m-%Y %H:%M:%S')),('state','=','activated')])
            for rec in records:
                expiry_date = datetime.strptime(rec.date,'%Y-%m-%d')
                start_reminder_date = expiry_date - timedelta(days=+days_offset_reminder)
                if today >=  start_reminder_date :
                    user_ids = []
                    group_obj = self.env.ref('rog_qhsse.group_receive_security_meeting_email_notification')
                    for user in group_obj.users:
                        user_ids.append(user.id)
                    rec.message_unsubscribe_users(user_ids=user_ids)
                    rec.message_subscribe_users(user_ids=user_ids)
                    rec.message_post(_('FYI, There is a Security Meeting Reminder for %s.') % (expiry_date.strftime('%d-%m-%Y')),
                                          subject='Security Meeting Reminder' ,
                                          subtype='mail.mt_comment')

                    if today.strftime('%Y-%m-%d') == expiry_date.strftime('%Y-%m-%d'):
                        rec.state = 'deactivated'
        return True


    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_qhsse.group_receive_security_meeting_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                '%s for (%s), which is being initiated by %s.') % (msg,
                                                                   self.name, self.env.user.name),
                              subject='%s' % (msg),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names, msg))


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('sm_code') or 'New'
        res = super(SecurityMeeting, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return


    @api.multi
    def button_activate(self):
        self.state = 'activated'
        self.email_dispatch('Activated Reminder')
        return

    @api.multi
    def button_deactivate(self):
        self.state = 'deactivated'
        self.email_dispatch('DeActivated Reminder')
        return


    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    month = fields.Selection([
        ('jan','January'),('feb','February'),('mar','March'),('apr','April'),('may','May'),('june','June'),('july','July'),('aug','August'),('sept','September'),('oct','October'),('nov','November'),('dec','December')
    ])
    date = fields.Date(string='Meeting Date')
    remark = fields.Text(string='Remarks')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('activated', 'Activated'),
        ('deactivated', 'DeActivated'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')





class Inspection(models.Model):
    _name = 'inspection'
    _inherit = ['mail.thread']

    @api.model
    def run_notify_inspection(self):
        is_activate_inspection_reminder = self.env.user.company_id.is_inspection_reminder
        if is_activate_inspection_reminder :
            days_offset_reminder = self.env.user.company_id.inspection_reminder_days
            today = datetime.today()

            object = self.env['inspection']
            records = object.search([('date', '<=',  datetime.today().strftime('%d-%m-%Y %H:%M:%S')),('state','=','activated')])
            for rec in records:
                expiry_date = datetime.strptime(rec.date,'%Y-%m-%d')
                start_reminder_date = expiry_date - timedelta(days=+days_offset_reminder)
                if today >=  start_reminder_date :
                    user_ids = []
                    group_obj = self.env.ref('rog_qhsse.group_receive_inspection_email_notification')
                    for user in group_obj.users:
                        user_ids.append(user.id)
                    rec.message_unsubscribe_users(user_ids=user_ids)
                    rec.message_subscribe_users(user_ids=user_ids)
                    rec.message_post(_('FYI, There is an Inspection Reminder for %s.') % (expiry_date.strftime('%d-%m-%Y')),
                                          subject='Inspection Reminder' ,
                                          subtype='mail.mt_comment')

                    if today.strftime('%Y-%m-%d') == expiry_date.strftime('%Y-%m-%d'):
                        rec.state = 'deactivated'
        return True


    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_qhsse.group_receive_inspection_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                '%s for (%s), which is being initiated by %s.') % (msg,
                                                                   self.name, self.env.user.name),
                              subject='%s' % (msg),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names, msg))


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('i_code') or 'New'
        res = super(Inspection, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return


    @api.multi
    def button_activate(self):
        self.state = 'activated'
        self.email_dispatch('Activated Reminder')
        return

    @api.multi
    def button_deactivate(self):
        self.state = 'deactivated'
        self.email_dispatch('DeActivated Reminder')
        return


    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    year = fields.Char(string='Year')
    month = fields.Selection([
        ('jan','January'),('feb','February'),('mar','March'),('apr','April'),('may','May'),('june','June'),('july','July'),('aug','August'),('sept','September'),('oct','October'),('nov','November'),('dec','December')
    ])
    date = fields.Date(string='Meeting Date')
    remark = fields.Text(string='Remarks')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('activated', 'Activated'),
        ('deactivated', 'DeActivated'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
#     user_ids = fields.One2many('res.users','inspection_user_id',string='Responsible Persons')
#
#
# class ResUserROG(models.Model):
#     _inherit = 'res.users'
#
#     inspection_user_id = fields.Many2one('inspection',string='Inspection User')



class RegulatoryDocument(models.Model):
    _name = 'regulatory.document'
    _inherit = ['mail.thread']

    @api.model
    def run_notify_regulatory_document(self):
        is_activate_regulatory_document_reminder = self.env.user.company_id.is_regulatory_document_reminder
        if is_activate_regulatory_document_reminder :
            days_offset_reminder = self.env.user.company_id.regulatory_document_reminder_days
            today = datetime.today()

            object = self.env['regulatory.document']
            records = object.search([('date', '<=',  datetime.today().strftime('%d-%m-%Y %H:%M:%S')),('state','=','activated')])
            for rec in records:
                expiry_date = datetime.strptime(rec.date,'%Y-%m-%d')
                start_reminder_date = expiry_date - timedelta(days=+days_offset_reminder)
                if today >=  start_reminder_date :
                    user_ids = []
                    group_obj = self.env.ref('rog_qhsse.group_receive_regulatory_document_email_notification')
                    for user in group_obj.users:
                        user_ids.append(user.id)
                    rec.message_unsubscribe_users(user_ids=user_ids)
                    rec.message_subscribe_users(user_ids=user_ids)
                    rec.message_post(_('FYI, There is a Regulatory Document (%s) for %s, that will expire on %s.') % (rec.document_type,rec.purpose_document,expiry_date.strftime('%d-%m-%Y')),
                                          subject='Regulatory Document Reminder' ,
                                          subtype='mail.mt_comment')

                    if today.strftime('%Y-%m-%d') == expiry_date.strftime('%Y-%m-%d'):
                        rec.state = 'deactivated'
        return True


    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_qhsse.group_receive_regulatory_document_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                '%s for (%s), which is being initiated by %s.') % (msg,
                                                                   self.name, self.env.user.name),
                              subject='%s' % (msg),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names, msg))


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('rd_code') or 'New'
        res = super(RegulatoryDocument, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return


    @api.multi
    def button_activate(self):
        self.state = 'activated'
        self.email_dispatch('Activated Reminder')
        return

    @api.multi
    def button_deactivate(self):
        self.state = 'deactivated'
        self.email_dispatch('DeActivated Reminder')
        return


    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    regulatory_authority = fields.Char(string='Regulatory Authority')
    document_type = fields.Char(string='Type of Document')
    purpose_document = fields.Char(string='Purpose Of Approval / certificate')
    frequency = fields.Char(string='Frequecy (Annual, A / Transaction based, T)')
    fees_amount = fields.Char(string='Fees/Amount Required')
    document_holder = fields.Char(string='Document Holder (Dept.)')
    last_date_issued = fields.Date(string='Last Date Issued')
    date = fields.Date(string='Expiry Date')
    status = fields.Selection([('valid','Valid'),('invalid','Invalid'),('not_available','Not Available')],string='Status')
    remark = fields.Text(string='Remarks')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('activated', 'Activated'),
        ('deactivated', 'DeActivated'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')



class RoutineActivity(models.Model):
    _name = 'routine.activity'
    _inherit = ['mail.thread']

    @api.model
    def run_notify_routine_activity(self):
        is_activate_routine_activity_reminder = self.env.user.company_id.is_routine_activity_reminder
        if is_activate_routine_activity_reminder :
            days_offset_reminder = self.env.user.company_id.routine_activity_reminder_days
            today = datetime.today()

            object = self.env['routine.activity']
            records = object.search([('date', '<=',  datetime.today().strftime('%d-%m-%Y %H:%M:%S')),('state','=','activated')])
            for rec in records:
                expiry_date = datetime.strptime(rec.date,'%Y-%m-%d')
                start_reminder_date = expiry_date - timedelta(days=+days_offset_reminder)
                if today >=  start_reminder_date :
                    user_ids = []
                    group_obj = self.env.ref('rog_qhsse.group_receive_routine_activity_email_notification')
                    for user in group_obj.users:
                        user_ids.append(user.id)
                    rec.message_unsubscribe_users(user_ids=user_ids)
                    rec.message_subscribe_users(user_ids=user_ids)
                    rec.message_post(_('FYI, The Routine Activity (%s)  for the action (%s), will be due on %s.') % (rec.activity,rec.action,expiry_date.strftime('%d-%m-%Y')),
                                          subject='Routine Activity Reminder' ,
                                          subtype='mail.mt_comment')

                    if today.strftime('%Y-%m-%d') == expiry_date.strftime('%Y-%m-%d'):
                        rec.state = 'deactivated'

                    #notify through email the responsible person
                    resp_ids = []
                    responsible_id = rec.responsible_id
                    if responsible_id:
                        resp_ids.append(responsible_id.id)
                        rec.message_subscribe_users(user_ids=resp_ids)
                        rec.message_post(_(
                                'FYI, You are responsible for the routine activity (%s), for the action (%s), which will be due on %s.') % (rec.activity,rec.action,expiry_date.strftime('%d-%m-%Y')),
                                              subject='Routine Activity Reminder to Responsible Person',
                                              subtype='mail.mt_comment')

                    #Create a new routine activity
                    new_expiry_date = False
                    frequency = rec.frequency
                    exp_date = datetime.strptime(rec.date,'%Y-%m-%d')
                    if frequency == 'quarterly':
                        new_expiry_date = exp_date + relativedelta(months=+3)
                    elif frequency == 'monthly' :
                        new_expiry_date = exp_date + relativedelta(months=1)
                    elif frequency == 'weekly':
                        new_expiry_date = exp_date + timedelta(weeks=+1)
                    elif frequency == 'annually':
                        new_expiry_date = exp_date + relativedelta(years=+1)
                    elif frequency == 'fortnightly':
                        new_expiry_date = exp_date + timedelta(weeks=+2)

                    new_routine = rec.copy()
                    new_routine.date = new_expiry_date
                    new_routine.message_unsubscribe_users(user_ids=user_ids)
                    new_routine.message_subscribe_users(user_ids=resp_ids)
                    new_routine.message_post(_('FYI, A new Routine Activity (%s), has been automatically created for the action (%s), which will be due on %s.') % (
                    new_routine.activity, rec.action, expiry_date.strftime('%d-%m-%Y')),
                                     subject='New Routine Activity Created Alert',
                                     subtype='mail.mt_comment')

        return True


    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_qhsse.group_receive_routine_activity_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                '%s for (%s), which is being initiated by %s.') % (msg,
                                                                   self.name, self.env.user.name),
                              subject='%s' % (msg),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names, msg))


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('ra_code') or 'New'
        res = super(RoutineActivity, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return


    @api.multi
    def button_activate(self):
        self.state = 'activated'
        self.email_dispatch('Activated Reminder')
        return

    @api.multi
    def button_deactivate(self):
        self.state = 'deactivated'
        self.email_dispatch('DeActivated Reminder')
        return


    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    activity = fields.Char(string='Activity')
    frequency = fields.Selection([('quarterly','Quarterly'),('monthly','Monthly'),('weekly','Weekly'),('annually','Annually'),('fortnightly','Fortnightly')])
    action = fields.Text(string='Action')
    responsible_id = fields.Many2one('res.users',string='Responsibility')
    last_execution_date = fields.Date(string='Last Execution Date')
    date = fields.Date(string='Next Date')
    status = fields.Selection([('up_to_date','Up to Date'),('not_up_to_date','Not Up to Date'),('on_going','On going')])
    remark = fields.Text(string='Remarks')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('activated', 'Activated'),
        ('deactivated', 'DeActivated'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')



class ResCompanyRetail(models.Model):
    _inherit = "res.company"

    is_qhsse_reminder = fields.Boolean(string='Activate QHHSE Meeting Reminder',default=True)
    qhsse_reminder_days = fields.Integer(string='Start QHHSE Meeting Reminder Days Before Expiry Date',default=1)
    is_emergency_drill_reminder = fields.Boolean(string='Activate Emergency Drill Reminder',default=True)
    emergency_drill_reminder_days = fields.Integer(string='Start Emergency Drill Reminder Days Before Expiry Date', default=1)
    is_security_meeting_reminder = fields.Boolean(string='Activate Security Meeting Reminder', default=True)
    security_meeting_reminder_days = fields.Integer(string='Start Security Meeting Reminder Days Before Expiry Date', default=1)
    is_inspection_reminder = fields.Boolean(string='Activate Inspection Reminder', default=True)
    inspection_reminder_days = fields.Integer(string='Start Inspection Reminder Days Before Expiry Date', default=7)
    is_regulatory_document_reminder = fields.Boolean(string='Activate Regulatory Document Reminder', default=True)
    regulatory_document_reminder_days = fields.Integer(string='Start Regulatory Document Reminder Days Before Expiry Date', default=30)
    is_routine_activity_reminder = fields.Boolean(string='Activate Routine Activity Reminder', default=True)
    routine_activity_reminder_days = fields.Integer(string='Start Routine Activity Reminder Days Before Expiry Date',default=3)