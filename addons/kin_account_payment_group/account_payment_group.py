# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _
from openerp.tools import amount_to_text
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from openerp.tools import float_compare, float_is_zero
from collections import OrderedDict

class AccountPaymentGroupExtend(models.Model):
    _inherit = 'account.payment.group'

    @api.multi
    def action_receipt_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('kin_account_payment_group.email_template_payment_receipt', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.payment.group',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            #mark_invoice_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }


    @api.multi
    def get_references(self):
        pay_list = []
        payment_ids = self.payment_ids
        for pay_line in payment_ids:
            if pay_line.ref_no:
                pay_list.append(pay_line.ref_no)
        return ', '.join(pay_list)

    @api.multi
    def get_paymethods(self):
        pay_list = []
        payment_ids = self.payment_ids
        for pay_line in payment_ids:
            if pay_line.journal_id:
                pay_list.append(pay_line.journal_id.name)
        return ', '.join(pay_list)

    @api.multi
    def get_paid_invoices(self):
        inv_list =[]
        matched_move_line_ids = self.matched_move_line_ids
        for matched_line in matched_move_line_ids :
            inv_list.append(matched_line.invoice_id.number)
        return ', '.join(inv_list)


    @api.multi
    def amount_to_text(self, amt, currency=False):
        dd = self.mapped('matched_move_line_ids')
        ddd = list(set(dd))
        big = ''
        small = ''
        if currency.name == 'NGN':
            big = 'Naira'
            small = 'kobo'
        elif currency.name == 'USD':
            big = 'Dollar'
            small = 'Cent'
        else:
            big = 'Naira'
            small = 'kobo'

        amount_text = amount_to_text(amt, currency).replace('euro', big).replace('Cent', small)
        return str.upper('**** ' + amount_text + '**** ONLY')



    @api.multi
    def cancel(self):
        for rec in self:
            #no need for this, since the reconciled fields are not ticked
            # for move_line in rec.fx_move_id.line_ids:
            #     move_line.remove_move_reconcile()
            rec.fx_move_id.button_cancel()
            rec.fx_move_id.unlink()
        return super(AccountPaymentGroupExtend,self).cancel()


    @api.multi
    def post(self):

        if not self.name:
            self.name = self.env['ir.sequence'].get('receipt_id_code')

        # for rec in self:
        #     #Forex gain Loss
        #     pay_rate = payment_amt = amt_comp_currency = 0
        #     currency_id = company_payment_id = False
        #     destination_account_id = False
        #     partner_id = False
        #     pay_obj = False
        #
        #     payment_id = False
        #     if rec.payment_ids :
        #         payment_id = rec.payment_ids[0]
        #     else:
        #         raise UserError('Sorry, record at least one payment line')
        #     if payment_id :
        #         if payment_id.payment_type == 'inbound' : #This is for either receiving money from either refunds or customer
        #             pay_amt = -payment_id.amount
        #         else:
        #             pay_amt = payment_id.amount
        #
        #         if abs(pay_amt) > payment_id.amount_company_currency:
        #             pay_rate = payment_id.amount_company_currency / pay_amt
        #         elif abs(pay_amt) < payment_id.amount_company_currency:
        #             pay_rate = pay_amt / payment_id.amount_company_currency
        #
        #         payment_amt = payment_id.amount
        #         currency_id = payment_id.currency_id
        #         company_payment_id = payment_id.company_payment_id # company currency
        #         destination_account_id = payment_id.destination_account_id
        #         partner_id = payment_id.partner_id
        #         amt_comp_currency\
        #             = payment_id.amount_company_currency
        #         pay_obj = payment_id
        #
        #     if payment_id and company_payment_id !=  currency_id :
        #         if len(rec.payment_ids) != 1:
        #             raise UserError(_('Please only one payment line is needed for the foreign transactions'))
        #
        #         if len(rec.to_pay_move_line_ids) != 1:
        #             raise UserError(_('Please you can only pay one invoice at a time for foreign transactions, to properly calculate the foreign exchange difference between the payment and the invoice'))
        #
        #         for move_line in rec.to_pay_move_line_ids:
        #             #to know how much has been paid so far
        #             total_prev_amt = 0
        #             for prev_payment in move_line.invoice_id.payment_move_line_ids:
        #                 total_prev_amt += prev_payment.amount_currency
        #
        #             balance = move_line.balance
        #             amount_currency = move_line.amount_currency
        #
        #             if balance > amount_currency :
        #                 debt_conv_rate = balance / amount_currency
        #             elif balance < amount_currency :
        #                 debt_conv_rate = amount_currency / balance
        #
        #             if (abs(total_prev_amt) + abs(payment_amt)) > abs(amount_currency) :
        #                 payment_amt = abs(amount_currency) - abs(total_prev_amt)
        #
        #             pay_amt = pay_rate * payment_amt
        #             debt_amt = debt_conv_rate * payment_amt
        #
        #             if pay_rate != debt_conv_rate:
        #                 rate = pay_rate - debt_conv_rate
        #                 forex_amt = rate * payment_amt
        #
        #                 # create the forex gain or loss
        #                 journal_id = self.env.ref('kin_account_payment_group.forex_gain_loss_journal')
        #                 if not journal_id:
        #                     raise UserError(_('The Forex Gain/Loss Journal is Not Present'))
        #
        #                 debit_account_id = journal_id.default_debit_account_id
        #                 if not debit_account_id:
        #                     raise UserError(_('Please set the Default Debit Account field on the Forex Gain/Loss Journal'))
        #
        #                 credit_account_id = journal_id.default_credit_account_id
        #                 if not credit_account_id:
        #                     raise UserError(_('Please set the Default Credit Account field on the Forex Gain/Loss Journal'))
        #
        #                 mv_lines = []
        #                 move_line_a = move_line_b = ()
        #
        #                 move_id = self.env['account.move'].create({
        #                         'journal_id': journal_id.id,
        #                         'company_id': self.env.user.company_id.id,
        #                         'date': pay_obj.payment_date
        #                     })
        #
        #                 if forex_amt > 0 : #debit Balance so Debit Fx Loss and credit payable
        #                     move_line_a = (0, 0, {
        #                             'name': rec.name.split('\n')[0][:64] + ' Currency exchange difference',
        #                             'account_id': debit_account_id.id,
        #                             'partner_id': partner_id.id,
        #                             'debit': abs(forex_amt),
        #                             'credit': 0,
        #                             'ref': rec.name,
        #                         })
        #                     mv_lines.append(move_line_a)
        #
        #                     move_line_b = (0, 0, {
        #                             'name': self.name.split('\n')[0][:64] + ' Currency exchange difference',
        #                             'account_id': destination_account_id.id,
        #                             'partner_id': partner_id.id,
        #                             'debit': 0,
        #                             'credit': abs(forex_amt),
        #                             'ref': rec.name,
        #                             'reconciled': True,  #It prevents it from showing on the invoices on the list of outstanding credits
        #                         })
        #                     mv_lines.append(move_line_b)
        #                 elif forex_amt < 0 : # Debit Trade payable and Credit Fx Gain
        #                     move_line_a = (0, 0, {
        #                         'name': rec.name.split('\n')[0][:64] + ' Currency exchange difference',
        #                         'account_id': destination_account_id.id,
        #                         'partner_id': partner_id.id,
        #                         'debit': abs(forex_amt),
        #                         'credit': 0,
        #                         'ref': rec.name,
        #                         'reconciled': True, #It prevents it from showing on the invoices on the list of outstanding credits
        #                     })
        #                     mv_lines.append(move_line_a)
        #
        #                     move_line_b = (0, 0, {
        #                         'name': self.name.split('\n')[0][:64] + ' Currency exchange difference',
        #                         'account_id': credit_account_id.id,
        #                         'partner_id': partner_id.id,
        #                         'debit': 0,
        #                         'credit': abs(forex_amt),
        #                         'ref': rec.name,
        #                     })
        #                     mv_lines.append(move_line_b)
        #
        #
        #                 if mv_lines:
        #                     move_id.write({'line_ids': mv_lines})
        #                     rec.fx_move_id = move_id
        #                     move_line.move_id.fx_move_id = move_id
        #                     move_id.post()
        res = super(AccountPaymentGroupExtend, self).post()

                        # rate = line.currency_id.with_context(date=date).rate
                    # amount_residual_currency += sign_partial_line * line.currency_id.round(partial_line.amount * rate)

        return res

    @api.constrains('payment_voucher_no')
    def check_payment_voucher(self):
        if self.env.user.company_id.is_restrict_payment_voucher_no :
            for rec in self:
                if len(rec.search([('payment_voucher_no', '=', rec.payment_voucher_no)])) > 1:
                    raise ValidationError('Payment Voucher No. Already Exist')


    name = fields.Char(string='Receipt Number', readonly=True, states={'draft': [('readonly', False)]})
    narration = fields.Text('Narration')
    payment_voucher_no = fields.Char(string='Payment Voucher Number')
    partner_tag_ids = fields.Many2many('res.partner.category',related='partner_id.category_id',string='Partner Tags')
    fx_move_id = fields.Many2one('account.move', string='FX Move')
    user_id = fields.Many2one('res.users',string='User',default=lambda self: self.env.user)


class ResCompanyRetail(models.Model):
    _inherit = "res.company"

    is_restrict_payment_voucher_no = fields.Boolean(string='Is Restrict By Payment Voucher No.')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    partner_tag_ids = fields.Many2many('res.partner.category', related='partner_id.category_id', string='Partner Tags')
    amount_company_currency = fields.Monetary(currency_field='company_payment_id')
    company_payment_id = fields.Many2one('res.currency', related='payment_group_company_id.currency_id')
    fx_move_id = fields.Many2one(related='payment_group_id.fx_move_id', string='FX Move',store=True)


class AccountMove(models.Model):
    _inherit = 'account.move'

    fx_move_id = fields.Many2one('account.move', string='FX Move')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def remove_move_reconcile(self):
        for rec in self:
            rec.move_id.fx_move_id.button_cancel()
            rec.move_id.fx_move_id.unlink()
        return super(AccountMoveLine,self).remove_move_reconcile()


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"


    @api.model
    def create(self, vals):
        ctx = dict(self._context)
        ctx['skip_full_reconcile_check'] = True
        res = super(AccountPartialReconcile, self.with_context(ctx)).create(vals)

        return res

