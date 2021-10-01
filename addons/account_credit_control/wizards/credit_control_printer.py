# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# 2018 kinsolve Solution


from openerp import _, api, fields, models
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare,float_round, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta

class CreditControlPrinter(models.TransientModel):
    """ Print lines """

    _name = "credit.control.printer"
    _rec_name = 'id'
    _description = 'Mass printer'

    @api.model
    def _get_line_ids(self):
        context = self.env.context
        if context.get('active_model') != 'credit.control.line':
            return False
        return context.get('active_ids', False)

    mark_as_sent = fields.Boolean(string='Mark letter lines as sent. Also creates penalty invoice if penalize parameters have been configured for the policy level',
                                  default=True,
                                  help="Only letter lines will be marked.")
    line_ids = fields.Many2many('credit.control.line',
                                string='Credit Control Lines',
                                default=_get_line_ids)

    @api.model
    def _credit_line_predicate(self, line):
        return True

    @api.model
    @api.returns('credit.control.line')
    def _get_lines(self, lines, predicate):
        return lines.filtered(predicate)

    @api.multi
    def print_lines(self):
        self.ensure_one()
        comm_obj = self.env['credit.control.communication']
        if not self.line_ids:
            raise UserError(_('No credit control lines selected.'))

        lines = self._get_lines(self.line_ids, self._credit_line_predicate)

        comms = comm_obj._generate_comm_from_credit_lines(lines)

        if self.mark_as_sent:
            comms._mark_credit_line_as_sent()

            # Penalize by generating an invoice for respective policy
            for line in lines:
                partner_id = line.partner_id
                balance_due = line.balance_due
                invoice_id = line.invoice_id
                due_date = line.date_due
                is_auto_validate_invoice = line.policy_level_id.is_auto_validate_invoice

                if line.policy_level_id.is_penalize and line.policy_level_id.penalize_percentage > 0 and line.policy_level_id.product_id:
                    inv = self.create_invoice(partner_id, invoice_id, due_date, balance_due, line.policy_level_id,is_auto_validate_invoice)

        report_name = 'account_credit_control.report_credit_control_summary'
        report_obj = self.env['report'].with_context(active_ids=comms.ids)

        return report_obj.get_action(comms, report_name)


    def create_invoice(self,partner_id,invoice,due_date,balance_due,policy_level_id,is_auto_validate_invoice,inv_type='out_invoice'):
        penalize_percentage = policy_level_id.penalize_percentage
        rate = (penalize_percentage / 100) * balance_due
        product_id = policy_level_id.product_id

        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        if not partner_id :
            raise UserError(_("No Partner Defined"))

        if not product_id :
            raise UserError(_("No Penalize Product Defined"))

        invoice_vals = {
            'name': invoice.number + " with due date at: " + datetime.strptime(due_date , "%Y-%m-%d").strftime("%d-%m-%Y")  or '',
            'origin': invoice.number + " with due date at: " + datetime.strptime(due_date , "%Y-%m-%d").strftime("%d-%m-%Y")  or '',
            'type': inv_type,
            'reference': invoice.number + " with due date at: " + datetime.strptime(due_date , "%Y-%m-%d").strftime("%d-%m-%Y")  or '',
            'account_id': partner_id.property_account_receivable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id,
            'is_pen_invoice': True,
            # 'company_id': sale_order.company_id.id,
            'user_id': self.env.user.id,
        }

        inv = inv_obj.create(invoice_vals)

        lines = []

        if not float_is_zero(1, precision_digits=precision):
            account = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(
                    _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                        product_id.name, product_id.id,
                        product_id.categ_id.name))


            default_analytic_account = self.env['account.analytic.default'].account_get(
                product_id.id, partner_id.id,
                self.env.user.id, datetime.today())

            inv_line = {
                'name' : "%s percent charge on %s balance due amount for %s" % (penalize_percentage,balance_due,invoice.number),
                # 'sequence': self.sequence,
                'origin': invoice.number + " with due date at : " + datetime.strptime(due_date , "%Y-%m-%d").strftime("%d-%m-%Y")  or '',
                'account_id': account.id,
                'price_unit': rate,
                'quantity': 1,
                'uom_id': product_id.uom_id.id,
                'product_id': product_id.id or False,
                'account_analytic_id':  default_analytic_account and default_analytic_account.analytic_id.id,
                'invoice_id': inv.id
            }
            self.env['account.invoice.line'].create(inv_line)


        if not inv.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if inv.amount_untaxed < 0:
            inv.type = 'out_refund'
            for line in inv.invoice_line_ids:
                line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in inv.invoice_line_ids:
            line._set_additional_fields(inv)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        inv.compute_taxes()

        #Send Email to accountants
        user_ids = []
        group_obj = self.env.ref('account.group_account_invoice')
        for user in group_obj.users:
            user_ids.append(user.id)
            inv.message_unsubscribe_users(user_ids=user_ids)
            inv.message_subscribe_users(user_ids=user_ids)
            inv.message_post(_(
                'A New defaulter Invoice has been created by %s for the customer - %s.') % (
                                  self.env.user.name, partner_id.name),
                              subject='A New defaulter Invoice has been created', subtype='mail.mt_comment')

        if is_auto_validate_invoice :
            inv.action_move_create()
            inv.invoice_validate()
        return inv

