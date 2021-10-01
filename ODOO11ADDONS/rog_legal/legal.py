# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from odoo import api, fields, models, _, SUPERUSER_ID

class LegalCase(models.Model):
    _name = 'legal.case'
    _inherit = ['mail.thread']

    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_legal.group_receive_legal_case_email_notification')
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
        vals['name'] = self.env['ir.sequence'].next_by_code('lc_code') or 'New'
        res = super(LegalCase, self).create(vals)
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
    def button_open_dispute(self):
        self.state = 'open_dispute'
        self.email_dispatch('Open Dispute')
        return

    @api.multi
    def button_close_dispute(self):
        self.state = 'close_dispute'
        self.email_dispatch('Close Dispute')
        return

    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    open_dispute_date = fields.Date(string='Open Dispute Date')
    close_dispute_date = fields.Date(string='Close Dispute Date')
    plantiff = fields.Char(string='Claimant/Plantiff')
    defendant = fields.Char(string='Defendant')
    case_file_no = fields.Char(string='Case File No.')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    description = fields.Text(string='Case Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open_dispute', 'Open Dispute'),
        ('close_dispute', 'Close Dispute'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    reminder_ids = fields.One2many('kin.reminder', 'legal_case_id', string='Reminders')
    suit_number = fields.Char(string='Suit Number')
    court_name = fields.Char(string='Court Name')
    judge_magistrate_name = fields.Char(string='Judge/Magistrate Name')
    location = fields.Char(string='Location')


class LegalAdvice(models.Model):
    _name = 'legal.advice'
    _inherit = ['mail.thread']

    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_legal.group_receive_legal_advice_email_notification')
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
        vals['name'] = self.env['ir.sequence'].next_by_code('la_code') or 'New'
        res = super(LegalAdvice, self).create(vals)
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
    def action_legal_request(self,msg):
        self.state = 'request'
        self.request_opinion = msg
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_legal.group_receive_legal_adviser')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                'A Request for Advise with ID (%s), is being requested by %s.') % (                                                             self.name, self.env.user.name),
                              subject='%s' % ('Request For Advice'),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for Request for Advise Stage' % (user_names))

        return


    @api.multi
    def action_legal_response(self, msg):
        self.state = 'response'
        self.answer = msg
        user_ids = []
        user_ids.append(self.requester_id.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                'The Response for Advice with ID (%s), by %s.') % (self.name, self.requester_id.name),
                              subject='%s' % ('Request For Advice'),
                              subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for the Response' % (self.requester_id.name))


    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    date = fields.Date(string='Date')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    requester_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user.id)
    request_opinion = fields.Text(string='Request for Opinion / Advice')
    answer = fields.Text(string='Legal Opinion / Advise Response')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Request for Advise'),
        ('response', 'Respond to Requester'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')




class Reminder(models.Model):
    _inherit = 'kin.reminder'

    legal_case_id = fields.Many2one('legal.case',string='Legal Case')