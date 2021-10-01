# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError
from datetime import datetime,date, timedelta

class ReportHead(models.Model):
    _name = 'account.report.head'

    name = fields.Char(string='Report Head')


class AccountSubClass(models.Model):
    _name = 'account.subclass'

    name = fields.Char(string='Name')

class AccountAccountExtend(models.Model):
    _inherit = 'account.account'

    tag_ids = fields.Many2many('account.account.tag', 'account_account_account_tag', 'account_account_id','account_account_tag_id')
    sub_classification = fields.Many2one('account.subclass',string='Internal Classification')
    report_head_id = fields.Many2one('account.report.head',string='IFRS Classification')

class AccountAccountTagExtend(models.Model):
    _inherit = 'account.account.tag'

    account_ids = fields.Many2many('account.account','account_account_account_tag','account_account_tag_id' ,'account_account_id', string="Accounts")


class AccountJournalExtend(models.Model):
    _inherit = "account.journal"

    analytic_account_id = fields.Many2one('account.analytic.account',string='Analytic Account', help='This helps to automatically populate the invoices with the set analytic account')


class AccountAnalyticLineExtend(models.Model):
    _inherit = 'account.analytic.line'

    invoice_id = fields.Many2one('account.invoice',string="Invoice")
    invoice_line_id = fields.Many2one('account.invoice.line',string="Invoice Line")


class AccountMoveExtend(models.Model):
    _name = 'account.move'
    _inherit = ['account.move','mail.thread']

    journal_id = fields.Many2one(track_visibility='onchange')
    ref = fields.Char(track_visibility='onchange')
    date = fields.Date(track_visibility='onchange')
    currency_id = fields.Many2one(track_visibility='onchange')
    rate_diff_partial_rec_id = fields.Many2one(track_visibility='onchange')
    line_ids = fields.One2many(track_visibility='onchange')
    partner_id = fields.Many2one(track_visibility='onchange')
    amount = fields.Monetary(track_visibility='onchange')
    # narration = fields.Text(string='Internal Note')
    company_id = fields.Many2one(track_visibility='onchange')
    matched_percentage = fields.Float(track_visibility='onchange')
    statement_line_id = fields.Many2one(track_visibility='onchange')
    dummy_account_id = fields.Many2one(track_visibility='onchange')
    state = fields.Selection(track_visibility='onchange')



class AccountBankStatementLineExtend(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.multi
    def button_reconcile(self):
        amount = self.amount
        debit = self.move_line_id.debit
        credit = self.move_line_id.credit
        if debit > 0 and amount < 0:
            raise ValidationError(_('All debit amounts(Increase) for bank/cash account type have +ve sign'))
        if credit < 0 and amount > 0:
            raise ValidationError(_('All credit amounts(Decrease) for bank/cash account type have -ve sign'))
        if debit > 0 and amount != debit:
            raise ValidationError(_('Journal Item debit amount must equal line amount, otherwise use the statement reconcile button above'))
        if credit < 0 and amount != credit:
            raise ValidationError(_('Journal Item credit amount must equal line amount, otherwise use the statement reconcile button above '))


        move_line_id = self.move_line_id
        ctx = self.env.context
        data = []
        data.append({'payment_aml_ids':[move_line_id.id]})
        res = self.pool.get('account.bank.statement.line').process_reconciliations(self.env.cr,self.env.uid,self.ids,data,context=ctx)
        # process_reconciliations(self, cr, uid, ids, data, context=None):
        return




class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.constrains('payment_date')
    def check_date(self):
        for rec in self:
            set_date = rec.payment_date
            restrict_users = self.env.ref('kin_account.group_restrict_account_date').users
            if set_date and self.env.user in restrict_users:
                dayback = self.env.user.company_id.restrict_days
                selected_date = datetime.strptime(set_date, "%Y-%m-%d")
                allowed_date = datetime.strptime(str(date.today()), "%Y-%m-%d") - timedelta(days=+dayback)
                if selected_date < allowed_date:
                    raise ValidationError('Backdating is not allowed, before %s ' % (datetime.strftime(allowed_date,'%d-%m-%Y')))



class AccountPaymentGroupExtend(models.Model):
    _inherit = 'account.payment.group'

    @api.constrains('payment_date')
    def check_date(self):
        for rec in self:
            set_date = rec.payment_date
            restrict_users = self.env.ref('kin_account.group_restrict_account_date').users
            if set_date and self.env.user in restrict_users:
                dayback = self.env.user.company_id.restrict_days
                selected_date = datetime.strptime(set_date, "%Y-%m-%d")
                allowed_date = datetime.strptime(str(date.today()), "%Y-%m-%d") - timedelta(days=+dayback)
                if selected_date < allowed_date:
                    raise ValidationError('Backdating is not allowed, before %s ' % (datetime.strftime(allowed_date,'%d-%m-%Y')))

                today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
                if selected_date > today_date :
                    raise ValidationError('Date forwarding is not allowed, after %s ' % (datetime.strftime(today_date,'%d-%m-%Y')))



class ResCompany(models.Model):
    _inherit = "res.company"

    restrict_days = fields.Integer(string='Restrict Transaction Day',default=1)