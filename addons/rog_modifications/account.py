# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError
from openerp.tools import amount_to_text
from datetime import datetime,date, timedelta


#THIS IS CAUSING RuntimeError: maximum recursion depth exceeded while calling a Python object
# class AccountPaymentExtend(models.Model):
#     _inherit = 'account.payment'
#
#     @api.multi
#     def post(self):
#         if self.is_date_changed and not self.user_has_groups('rog_modifications.group_date_rog'):
#             raise UserError(_(
#                 'Sorry, You cannot Validate this payment document, because the payment date field value requires verification. Please contact your superior to validate this payment'))
#         elif self.is_date_changed and self.user_has_groups('rog_modifications.group_date_rog'):
#             self.is_date_approved = True
#             self.date_approved_by = self.env.user
#         res = super(AccountPaymentExtend, self).post()
#         return res
#
#     @api.model
#     def create(self, vals):
#         res = super(AccountPaymentExtend, self).create(vals)
#         date_input = vals.get('payment_date', False)
#
#         if date_input:
#             selected_date = datetime.strptime(date_input, "%Y-%m-%d")
#             today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
#             if selected_date == today_date:
#                 res.is_date_changed = False
#                 res.is_date_approved = False
#                 res.date_changed_by = self.env.user
#             elif selected_date != today_date:
#                 res.is_date_changed = True
#                 res.is_date_approved = False
#                 res.date_changed_by = self.env.user
#
#                 # notify superior for date change
#                 user_ids = []
#                 group_obj = self.env.ref('rog_modifications.group_date_rog')
#                 user_names = ''
#                 for user in group_obj.users:
#                     user_names += user.name + ", "
#                     user_ids.append(user.id)
#                 res.message_subscribe_users(user_ids=user_ids)
#                 res.message_post(
#                     _(
#                         'The payment date field has been changed by %s, for the payment document %s, to %s, and requires approval') % (
#                         self.env.user.name, res.name, selected_date.strftime("%d/%m/%Y")),
#                     subject='Payment date field changed on payment document', subtype='mail.mt_comment')
#                 res.env.user.notify_info('%s Will Be Notified by Email for the change in date field' % (user_names))
#         return res
#
#
#     @api.multi
#     def write(self, vals):
#         date_input = vals.get('payment_date', False)
#
#         if date_input:
#             selected_date = datetime.strptime(date_input, "%Y-%m-%d")
#             today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
#             if selected_date == today_date:
#                 self.is_date_changed = False
#                 self.is_date_approved = False
#                 self.date_changed_by = self.env.user
#             elif selected_date != today_date:
#                 self.is_date_changed = True
#                 self.is_date_approved = False
#                 self.date_changed_by = self.env.user
#
#                 # notify superior for date change
#                 user_ids = []
#                 group_obj = self.env.ref('rog_modifications.group_date_rog')
#                 user_names = ''
#                 for user in group_obj.users:
#                     user_names += user.name + ", "
#                     user_ids.append(user.id)
#                 self.message_subscribe_users(user_ids=user_ids)
#                 self.message_post(
#                     _(
#                         'The payment date field has been changed by %s, for the payment document %s to %s, and requires approval') % (
#                         self.env.user.name, self.name, datetime.strftime(selected_date, "%d/%m/%Y")),
#                     subject='Payment date field changed on payment document', subtype='mail.mt_comment')
#                 self.env.user.notify_info('%s Will Be Notified by Email for the change in date field' % (user_names))
#         res = super(AccountPaymentExtend, self).write(vals)
#
#         return res
#
#     is_date_changed = fields.Boolean('Date Changed')
#     is_date_approved = fields.Boolean('Date Approved')
#     date_changed_by = fields.Many2one('res.users', string="Date Changed User")
#     date_approved_by = fields.Many2one('res.users', string="Date Approved User")
#





class AccountPaymentGroupExtend(models.Model):
    _inherit = 'account.payment.group'

    @api.multi
    def post(self):
        if self.is_date_changed and not self.user_has_groups('rog_modifications.group_date_rog'):
            raise UserError(_('Sorry, You cannot Validate this payment document, because the payment date field value requires verification. Please contact your superior to validate this payment'))
        elif self.is_date_changed and self.user_has_groups('rog_modifications.group_date_rog'):
            self.is_date_approved = True
            self.date_approved_by = self.env.user
        res = super(AccountPaymentGroupExtend, self).post()
        return res

    @api.model
    def create(self, vals):
        date_input = vals.get('payment_date', False)
        res = super(AccountPaymentGroupExtend, self).create(vals)

        if date_input:
            selected_date = datetime.strptime(date_input, "%Y-%m-%d")
            today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
            if selected_date == today_date:
                res.is_date_changed = False
                res.is_date_approved = False
                res.date_changed_by = self.env.user
            elif selected_date != today_date:
                res.is_date_changed = True
                res.is_date_approved = False
                res.date_changed_by = self.env.user

                # notify superior for date change
                user_ids = []
                group_obj = self.env.ref('rog_modifications.group_date_rog')
                user_names = ''
                for user in group_obj.users:
                    user_names += user.name + ", "
                    user_ids.append(user.id)
                res.message_subscribe_users(user_ids=user_ids)
                res.message_post(
                    _(
                        'The payment date field has been changed by %s, for the payment document %s, to %s, and requires approval') % (
                        self.env.user.name, res.name, selected_date.strftime("%d/%m/%Y")),
                    subject='Payment date field changed on payment document', subtype='mail.mt_comment')
                res.env.user.notify_info('%s Will Be Notified by Email for the change in date field' % (user_names))
        return res

    # @api.constrains('date_invoice')
    # def set_date_status(self):
    #     date_invoice = self.date_invoice
    #     selected_date = datetime.strptime(date_invoice, "%Y-%m-%d")
    #     today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
    #     if selected_date != today_date:
    #         self.is_date_changed = True
    #         self.is_date_approved = False
    #         self.date_changed_by = self.env.user

    @api.multi
    def write(self, vals):
        date_input = vals.get('payment_date', False)

        if date_input:
            selected_date = datetime.strptime(date_input, "%Y-%m-%d")
            today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
            if selected_date == today_date:
                self.is_date_changed = False
                self.is_date_approved = False
                self.date_changed_by = self.env.user
            elif selected_date != today_date:
                self.is_date_changed = True
                self.is_date_approved = False
                self.date_changed_by = self.env.user

                # notify superior for date change
                user_ids = []
                group_obj = self.env.ref('rog_modifications.group_date_rog')
                user_names = ''
                for user in group_obj.users:
                    user_names += user.name + ", "
                    user_ids.append(user.id)
                self.message_subscribe_users(user_ids=user_ids)
                self.message_post(
                    _(
                        'The payment date field has been changed by %s, for the payment document %s to %s, and requires approval') % (
                        self.env.user.name, self.name, datetime.strftime(selected_date,"%d/%m/%Y")),
                    subject='Payment date field changed on payment document', subtype='mail.mt_comment')
                self.env.user.notify_info('%s Will Be Notified by Email for the change in date field' % (user_names))
        res = super(AccountPaymentGroupExtend, self).write(vals)

        return res

    is_date_changed = fields.Boolean('Date Changed')
    is_date_approved = fields.Boolean('Date Approved')
    date_changed_by = fields.Many2one('res.users', string="Date Changed User")
    date_approved_by = fields.Many2one('res.users', string="Date Approved User")





class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    @api.multi
    def create_move(self, post_move=True):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.asset_id.is_ssd_sbu
        ctx['hr_department_id'] = self.asset_id.hr_department_id
        ctx['sbu_id'] = self.asset_id.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(AccountAssetDepreciationLine, self.with_context(ctx)).create_move(post_move)
        return res


class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    @api.model
    def create(self, vals):
        dept_id = vals.get('department_id',False)
        category_id = vals.get('category_id',False)
        if dept_id and category_id :
            categ_obj = self.env['account.asset.category']
            categ_code = categ_obj.browse(category_id).code
            categ_last_num = categ_obj.browse(category_id).last_number
            categ_obj.browse(category_id).last_number = categ_last_num + 1
            dept_code = self.env['hr.department'].browse(dept_id).code
            str_code = "%s/%s/%s"  % (categ_code,dept_code,categ_last_num)
            vals['code1'] = str_code

        res = super(AccountAsset, self).create(vals)
        return res

    code1 = fields.Char(string='Code Reference')
    department_id = fields.Many2one('hr.department',string='Department')
    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')




class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'


    @api.v7
    def process_reconciliations(self, cr, uid, ids, data, context=None):
        ctx = context or {}
        objs = self.pool.get('account.bank.statement.line').browse(cr,uid,ids,context=context)
        ctx['is_ssd_sbu'] = objs.statement_id.is_ssd_sbu
        ctx['hr_department_id'] = objs.statement_id.hr_department_id
        ctx['sbu_id'] = objs.statement_id.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(AccountBankStatementLine, self).process_reconciliations(cr=cr, uid=uid, ids=ids, data=data, context=ctx)
        return res



class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')





class AccountFiscalYearClosing(models.Model):

    _inherit = 'account.fiscalyear.closing'

    @api.multi
    def button_calculate(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(AccountFiscalYearClosing,self.with_context(ctx)).button_calculate()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.onchange('pay_now')
    def onchange_partner_id(self):
        if self.pay_now == 'pay_now':
            liq_journal = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1)
            self.account_id = liq_journal.default_debit_account_id \
                if self.voucher_type == 'sale' else liq_journal.default_credit_account_id
        else:
            if self.partner_id:
                self.account_id = self.partner_id.property_account_receivable_id \
                    if self.voucher_type == 'sale' else self.partner_id.property_account_payable_id
            else:
                self.account_id = self.journal_id.default_debit_account_id \
                    if self.voucher_type == 'sale' else self.journal_id.default_credit_account_id

    @api.multi
    def action_move_line_create(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(AccountVoucher,self.with_context(ctx)).action_move_line_create()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')




class AccountPaymentExtend(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        for rec in self:
            ctx = dict(rec._context)
            ctx['is_ssd_sbu'] = rec.is_ssd_sbu
            ctx['hr_department_id'] = rec.hr_department_id
            ctx['sbu_id'] = rec.sbu_id
            ctx['is_ssa_allow_split'] = True
            res = super(AccountPaymentExtend, rec.with_context(ctx)).post()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')


class AccountMoveExtend(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        ctx = dict(self._context)
        is_ssd_sbu = ctx.get('is_ssd_sbu', False)  # ssd
        hr_department_id = ctx.get('hr_department_id', False)  # shared service dept.
        sbu_id = ctx.get('sbu_id', False)
        is_ssa_allow_split = ctx.get('is_ssa_allow_split', True)

        vals['is_ssd_sbu'] = is_ssd_sbu or vals.get('is_ssd_sbu',False)
        vals['hr_department_id'] = hr_department_id and hr_department_id.id or vals.get('hr_department_id',False)
        vals['sbu_id'] = sbu_id and sbu_id.id or vals.get('sbu_id',False)
        vals['is_ssa_allow_split'] = is_ssa_allow_split or vals.get('is_ssa_allow_split',True)
        res = super(AccountMoveExtend, self).create(vals)

        #remove entries that have 0 debit or credit. this will often occur for the recivable account for the invoice, when the main invoice is generated with the exact sales amount as the advance amount.
        for move_line in res.line_ids :
            if move_line.debit == 0 and move_line.credit == 0:
                move_line.unlink()
        return res

    # @api.multi
    # def post(self):
    #     res = super(AccountMoveExtend,self).post()
    #     if self.loan_id:
    #         self.is_loan_entry = True
    #         amt = self.amount
    #         self.loan_id.total_cash += amt
    #         loan_lines = self.loan_id.loan_lines
    #         loan_lines_ids = [ll.id for ll in loan_lines]
    #         loan_lines_ids.reverse()
    #         loan_lines_objs = self.loan_id.loan_lines.browse(loan_lines_ids)
    #         for loan_line in loan_lines_objs:
    #             amt = amt - loan_line.amount
    #             if amt >= 0:
    #                 if loan_line.paid :
    #                     raise UserError('Sorry, loan line already paid')
    #                 loan_line.amount = 0
    #             elif amt < 0:
    #                 loan_line.amount = abs(amt)
    #                 break
    #
    #     return res

    @api.multi
    def button_cancel(self):
        res = super(AccountMoveExtend,self).button_cancel()
        if self.is_loan_entry:
            #self.loan_id.total_cash -= self.amount
            #the loan lines that have been paid in cash cannot be refunded and should not be adjusted. rather a new loan request should be created for the refund and set at the appropriate month
            raise UserError('Sorry, this entry cannot be unposted. please contact the admin')
        return res




    hr_department_id = fields.Many2one('hr.department', string='Shared Service',track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU',track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category',track_visibility='onchange')
    is_ssa_allow_split = fields.Boolean(string='Allow SSA Split', help="Allow Shared Service Allocation",default=True,track_visibility='onchange')
    loan_id = fields.Many2one('hr.loan',string='Loan Request')
    is_loan_entry = fields.Boolean(string='Is loan entry',copy=False)





class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        date_input = vals.get('date_invoice', False)
        res = super(AccountInvoice, self).create(vals)

        if date_input:
            selected_date = datetime.strptime(date_input, "%Y-%m-%d")
            today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
            if selected_date == today_date:
                res.is_date_changed = False
                res.is_date_approved = False
                res.date_changed_by = self.env.user
            elif selected_date != today_date:
                res.is_date_changed = True
                res.is_date_approved = False
                res.date_changed_by = self.env.user

                # notify superior for date change
                user_ids = []
                group_obj = self.env.ref('rog_modifications.group_date_rog')
                user_names = ''
                for user in group_obj.users:
                    user_names += user.name + ", "
                    user_ids.append(user.id)
                res.message_subscribe_users(user_ids=user_ids)
                res.message_post(
                    _(
                        'The invoice date field has been changed by %s, for the invoice %s, to %s and requires verification. Please contact your superior') % (
                        self.env.user.name, res.name, selected_date.strftime("%d/%m/%Y")),
                    subject='Invoice date field changed on invoice', subtype='mail.mt_comment')
                res.env.user.notify_info('%s Will Be Notified by Email for the change in date field' % (user_names))
        return res

    # @api.constrains('date_invoice')
    # def set_date_status(self):
    #     date_invoice = self.date_invoice
    #     selected_date = datetime.strptime(date_invoice, "%Y-%m-%d")
    #     today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
    #     if selected_date != today_date:
    #         self.is_date_changed = True
    #         self.is_date_approved = False
    #         self.date_changed_by = self.env.user

    @api.multi
    def write(self, vals):
        date_input = vals.get('date_invoice', False)

        if date_input:
            selected_date = datetime.strptime(date_input, "%Y-%m-%d")
            today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
            if selected_date == today_date:
                self.is_date_changed = False
                self.is_date_approved = False
                self.date_changed_by = self.env.user
            elif selected_date != today_date:
                self.is_date_changed = True
                self.is_date_approved = False
                self.date_changed_by = self.env.user

                # notify superior for date change
                user_ids = []
                group_obj = self.env.ref('rog_modifications.group_date_rog')
                user_names = ''
                for user in group_obj.users:
                    user_names += user.name + ", "
                    user_ids.append(user.id)
                self.message_subscribe_users(user_ids=user_ids)
                self.message_post(
                    _(
                        'The invoice date field has been changed by %s, for the invoice %s, to %s and requires verification. Please contact your superior') % (
                        self.env.user.name, self.name, selected_date.strftime("%d/%m/%Y")),
                    subject='Invoice date field changed on invoice', subtype='mail.mt_comment')
                self.env.user.notify_info('%s Will Be Notified by Email for the change in date field' % (user_names))
        res = super(AccountInvoice, self).write(vals)

        return res


    @api.multi
    def action_move_create(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split']  = True

        if self.is_date_changed and not self.user_has_groups('rog_modifications.group_date_rog'):
            raise UserError(_('Sorry, You cannot Validate this Invoice, because the date field value requires verification. Please contact your superior to validate the invoice'))
        elif self.is_date_changed and self.user_has_groups('rog_modifications.group_date_rog'):
            self.is_date_approved = True
            self.date_approved_by = self.env.user
        res = super(AccountInvoice,self.with_context(ctx)).action_move_create()
        return res

    @api.multi
    def amount_to_text(self, amt, currency):
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

    hr_department_id = fields.Many2one('hr.department', string='Shared Service',track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU',track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ],  string='Category',track_visibility='onchange')
    is_date_changed = fields.Boolean('Date Changed')
    is_date_approved = fields.Boolean('Date Approved')
    date_changed_by = fields.Many2one('res.users',string="Date Changed User")
    date_approved_by = fields.Many2one('res.users', string="Date Approved User")



class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    hr_department_id = fields.Many2one(related='invoice_id.hr_department_id', store=True)



class AccountMoveLineExtend(models.Model):
    _inherit = 'account.move.line'

    hr_department_id = fields.Many2one('hr.department',string='Department')
    loan_id = fields.Many2one(related='move_id.loan_id')


    @api.model
    def create(self, vals, apply_taxes=False):
        move_obj = self.env['account.move'].browse(vals['move_id'])
        is_ssd_sbu = move_obj.is_ssd_sbu
        hr_department_id = move_obj.hr_department_id
        sbu_id = move_obj.sbu_id
        is_ssa_allow_split = vals.get('is_ssa_allow_split',True)

        debit = vals.get('debit', False)
        credit = vals.get('credit', 0)

        if hr_department_id and is_ssd_sbu == 'ssd' and is_ssa_allow_split :
            ssa_objects = self.env['shared.service.allocation'].search([('hr_department_id','=',hr_department_id.id)])
            hr_dept = hr_department_id.name
            if not ssa_objects:
                raise UserError(_('Please Contact the administrator to configure the shared service allocation for this department %s' % (hr_dept)))
            perc_100 = 0
            for ssa_object in ssa_objects:
                sbu_perc_amt = ssa_object.percentage_allocation
                perc_100 += sbu_perc_amt
                sbu_analytic_id = ssa_object.sbu_id.sbu_analytic_account_id.id

                vals['debit'] = (sbu_perc_amt/100) * debit
                vals['credit'] = (sbu_perc_amt/100) * credit
                vals['analytic_account_id'] = sbu_analytic_id
                vals['hr_department_id'] = hr_department_id.id
                if sbu_perc_amt != 0:
                    move_line = super(AccountMoveLineExtend, self).create(vals)
            if perc_100 != 100 :
                raise UserError(_('Please contact the administrator to properly configure the shared service allocation for this department %s. The total percentage must be equal 100 percent, but it is currently %s percent' % (hr_dept,perc_100)))
        elif sbu_id and is_ssd_sbu == 'sbu' and is_ssa_allow_split:
            vals['analytic_account_id'] = sbu_id.sbu_analytic_account_id.id
            move_line = super(AccountMoveLineExtend, self).create(vals)
        elif is_ssa_allow_split :
            raise UserError(_('Please fill in the Shared Service Allocation fields'))
        else :
            raise UserError(_('Sorry, it is not your fault. Every back-end journal entry must have an analytic account. Please Contact the Developer to further code this process. '))

        return move_line





class SBU(models.Model):
    _name = 'sbu'

    name = fields.Char(string='SBU',required=True)
    sbu_analytic_account_id = fields.Many2one('account.analytic.account', string='SBU Analytic Account',required=True)


class SharedServiceAllocation(models.Model):
    _name = 'shared.service.allocation'

    hr_department_id = fields.Many2one('hr.department', string='Shared Service',required=True)
    sbu_id = fields.Many2one('sbu', string='SBU',required=True)
    percentage_allocation = fields.Float(string='Percentage Allocation',required=True)





class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    code = fields.Char(string='Code Reference')
    last_number = fields.Integer(string="Last Number for the Asset",default=1)



class HRDepartment(models.Model):
    _inherit = 'hr.department'

    code = fields.Char(string='Code Reference')

