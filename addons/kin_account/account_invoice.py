# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 -2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _
from openerp.tools.float_utils import float_compare
from urllib import urlencode
from urlparse import urljoin
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, RedirectWarning, ValidationError
from openerp.tools import amount_to_text
from datetime import datetime,date, timedelta

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('kin_account.email_template_edi_invoice_extend', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
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

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.is_from_inventory:
    #             raise UserError(_('Sorry, you are not allowed to delete this invoice that was created as a result of the Delivery Order'))
    #         if rec.is_cancelled_remaining_order:
    #             raise UserError(_('Sorry, you are not allowed to delete this invoice that was created as a result of the Cancelled Sales Order'))
    #         if rec.is_transfer_order:
    #             raise UserError(_('Sorry, you are not allowed to delete this invoice that was created as a result of the Product Transfer Order'))
    #
    #     return super(AccountInvoice, self).unlink()

    @api.multi
    def write(self, vals):
        is_partner = vals.get('partner_id',False)
        for rec in self:
            is_from_inventory = rec.is_from_inventory
            if is_partner and is_from_inventory :
                raise UserError(_('Sorry, you are not allowed to change the customer, that was set by the Delivery Order'))
            if is_partner and rec.is_cancelled_remaining_order :
                raise UserError(_('Sorry, you are not allowed to change the fields on this record, for the for the product qty. cancellation'))
            if is_partner and rec.is_transfer_order :
                raise UserError(_('Sorry, you are not allowed to change the fields on this record, for the product qty. order transfer'))

            res = super(AccountInvoice, rec).write(vals)
            if rec.partner_id.customer and  rec.partner_id.active == False :
                raise UserError(_('%s is not approved and active' % (rec.partner_id.name)))
        return res


    @api.multi
    def amount_to_text(self,amt,currency=False):
        big = ''
        small = ''
        if currency.name == 'NGN' :
            big = 'Naira'
            small = 'kobo'
        elif currency.name == 'USD':
            big = 'Dollar'
            small = 'Cent'
        else :
            big = 'Naira'
            small = 'kobo'

        amount_text =   amount_to_text(amt,currency).replace('euro',big).replace('Cent',small)
        return str.upper('**** ' + amount_text + '**** ONLY')


    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id')
    def _compute_amount(self):
        res = super(AccountInvoice,self)._compute_amount()
        #Total Amount
        amt_discount_total =  0.0
        for line in self.invoice_line_ids:
            amt_discount_total += line.discount_amt

        self.amt_discount_total = amt_discount_total




    @api.constrains('date_invoice')
    def check_date(self):
        for rec in self:
            set_date = rec.date_invoice
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


    @api.multi
    def btn_view_so(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Sales Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.sale_id])],
            #'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            #'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }


    @api.depends('sale_id')
    def _compute_so_count(self):
        for rec in self :
            rec.so_count = len(rec.sale_id)

    @api.multi
    def btn_view_picking(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Shipments'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.picking_id])],
            #'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            #'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('picking_id')
    def _compute_picking_count(self):
        for rec in self :
            rec.picking_count = len(rec.picking_id)


    @api.multi
    def btn_view_po(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Purchase Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.purchase_id1])],
            #'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            #'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }


    @api.depends('purchase_id1')
    def _compute_po_count(self):
        for rec in self :
            rec.po_count = len(rec.purchase_id1)


    def _get_url(self, module_name,menu_id,action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name,menu_id)[1]
        fragment['model'] =  'account.invoice'
        fragment['view_type'] = 'form'
        fragment['action']= model_data.get_object_reference(module_name,action_id)[1]
        query = {'db': self.env.cr.dbname}

# for displaying tree view. Remove if you want to display form view
#         fragment['page'] = '0'
#         fragment['limit'] = '80'
#         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


 # For displaying a single record. Remove if you want to display tree view
        for record in self:
            fragment['id'] =  record.id
            res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


        return res

    @api.onchange('partner_id')
    def partner_change(self):
        journal_analytic = self.journal_id.analytic_account_id
        analytic_acc = False
        if journal_analytic:
            analytic_acc = journal_analytic
        for line in self.invoice_line_ids:
            line.account_analytic_id = analytic_acc

        return


    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line:
            # Load a PO line only once
            if line in self.invoice_line_ids.mapped('purchase_line_id'):
                continue
            if line.product_id.purchase_method == 'purchase':
                qty = line.product_qty - line.qty_invoiced
            else:
                qty = line.qty_received - line.qty_invoiced
            if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                qty = 0.0
            taxes = line.taxes_id or line.product_id.supplier_taxes_id
            invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
            data = {
                'purchase_line_id': line.id,
                'name': line.name,
                'origin': self.purchase_id.origin,
                'uom_id': line.product_uom.id,
                'product_id': line.product_id.id,
                'account_id': self.env['account.invoice.line'].with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
                'price_unit': line.order_id.currency_id.with_context(date=line.order_id.date_order or fields.Date.context_today(self)).compute(line.price_unit, self.currency_id),
                'quantity': qty,
                'discount': line.discount,
                'account_analytic_id':line.account_analytic_id.id,
                'invoice_line_tax_ids': invoice_line_tax_ids.ids,

            }
            account = new_lines.get_invoice_line_account('in_invoice', line.product_id, self.purchase_id.fiscal_position_id, self.env.user.company_id)
            if account:
                data['account_id'] = account.id
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        # if  invoice_line_tax_ids :
        #     self.compute_taxes()
        self.purchase_id = False
        return {}

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        if self.currency_id:
            for line in self.invoice_line_ids.filtered(lambda r: r.purchase_line_id):
                line.price_unit = line.purchase_id.currency_id.with_context(date=line.purchase_id.date_order or fields.Date.context_today(self)).compute(line.purchase_line_id.price_unit, self.currency_id)



    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice,self).action_cancel()

        analytic_lines = self.env['account.analytic.line']
        for line in self.invoice_line_ids:
            analytic_lines += line.discount_analytic_line

            data = {
                'cos': 0 ,
                'markup': 0,
                'gross_margin' : 0 ,
                'gross_profit' : 0 ,
                'cos_total' : 0
            }
            line.write(data)

        if analytic_lines:
            analytic_lines.unlink()

        return res


    @api.multi
    def invoice_validate(self):
        if self.type == 'out_invoice' and self.partner_id.is_enforce_credit_limit_so and self.partner_id.is_credit_limit_changed :
            raise UserError(_('Please contact the respective persons to approve the credit limit changes for this customer, before you may proceed with the invoice validation'))
        if self.type == 'out_invoice' and self.partner_id.is_enforce_credit_limit_so and self.amount_total > (self.amount_total - self.partner_id.credit + self.partner_id.credit_limit)  :
            raise UserError(_('The Total amount %s of this invoice has exceeded the Credit of %s plus Credit Limit of %s. i.e %s > %s '  % (self.amount_total,self.amount_total - self.partner_id.credit,self.partner_id.credit_limit,self.amount_total,self.amount_total - self.partner_id.credit + self.partner_id.credit_limit)))

        res = super(AccountInvoice,self).invoice_validate()

        res = []
        for line in self.invoice_line_ids:
            disc_amt =  (line.discount / 100) * line.price_unit

            disc_acct_analytic_purchase_id = line.product_id.disc_acct_analytic_purchase_id or line.product_id.categ_id.disc_acct_analytic_purchase_id
            disc_acct_analytic_sale_id = line.product_id.disc_acct_analytic_sale_id or line.product_id.categ_id.disc_acct_analytic_sale_id


            if (disc_amt and disc_acct_analytic_purchase_id and self.type == "in_invoice") or  (disc_amt and disc_acct_analytic_purchase_id and self.type == "in_refund")  or  (disc_amt and disc_acct_analytic_sale_id and self.type == "out_invoice") or (disc_amt and disc_acct_analytic_sale_id and self.type == "out_refund")  :

                account_disc_analytic  = False
                qty = line.quantity
                if self.type == "in_invoice" or self.type == "in_refund" :
                    account_disc_analytic = disc_acct_analytic_purchase_id
                elif self.type == "out_invoice"  or self.type == "out_refund"  :
                    account_disc_analytic = disc_acct_analytic_sale_id

                if self.type == "in_refund" or  self.type == "out_invoice" :
                    disc_amt = -disc_amt
                    qty = -line.quantity

                #Create analytic line
                amount = disc_amt * line.quantity
                analytic_dict = {
                    'name': 'Discount Line for:' + line.name.split('\n')[0][:64],
                    'date': self.date_invoice,
                    'account_id': account_disc_analytic.id,
                    'unit_amount': qty,
                    'product_id': line.product_id and line.product_id.id or False,
                    'product_uom_id': (line.uom_id and line.uom_id.id) or (line.product_id.uom_id and line.product_id.uom_id.id) or False,
                    'amount': self.company_currency_id.with_context(date=self.date_invoice or fields.Date.context_today(self)).compute(amount, self.currency_id) if self.currency_id else amount,
                    'general_account_id': line.account_id.id,
                    'ref': self.name,
                    #'move_id': self.id,
                    'invoice_line_id' : line.id,
                    'invoice_id' : self.id,
                    'user_id': self.user_id.id or self._uid,
                }
                analytic_id = self.env['account.analytic.line'].create(analytic_dict)
                line.discount_analytic_line = analytic_id

        return res

    @api.model
    def _anglo_saxon_sale_move_lines(self, i_line):
        """Return the additional move lines for sales invoices and refunds.

        i_line: An account.invoice.line object.
        res: The move line entries produced so far by the parent move_line_get.
        """
        inv = i_line.invoice_id
        company_currency = inv.company_id.currency_id.id

        if i_line.product_id.type in ('product', 'consu') and i_line.product_id.valuation == 'real_time':
            fpos = i_line.invoice_id.fiscal_position_id
            accounts = i_line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)
            # debit account dacc will be the output account
            dacc = accounts['stock_output'].id
            # credit account cacc will be the expense account
            cacc = accounts['expense'].id
            if dacc and cacc:
                price_unit = i_line._get_anglo_saxon_price_unit()
                i_line.cos = price_unit
                i_line._calculate_margin_markup_profit()
                return [
                    {
                        'type':'src',
                        'name': i_line.name[:64],
                        'price_unit': price_unit,
                        'quantity': i_line.quantity,
                        'price': self.env['account.invoice.line']._get_price(inv, company_currency, i_line, price_unit),
                        'account_id':dacc,
                        'product_id':i_line.product_id.id,
                        'uom_id':i_line.uom_id.id,
                        'account_analytic_id': False,
                    },

                    {
                        'type':'src',
                        'name': i_line.name[:64],
                        'price_unit': price_unit,
                        'quantity': i_line.quantity,
                        'price': -1 * self.env['account.invoice.line']._get_price(inv, company_currency, i_line, price_unit),
                        'account_id':cacc,
                        'product_id':i_line.product_id.id,
                        'uom_id':i_line.uom_id.id,
                        'account_analytic_id': False,
                    },
                ]
        return []


    picking_id = fields.Many2one('stock.picking')
    sale_id = fields.Many2one('sale.order')
    picking_count = fields.Integer(compute="_compute_picking_count", string='# of Pickings', copy=False, default=0)
    po_count = fields.Integer(compute="_compute_po_count", string='# of Purchase Orders', copy=False, default=0)
    so_count = fields.Integer(compute="_compute_so_count", string='# of Sales Orders', copy=False, default=0)
    purchase_id1 = fields.Many2one("purchase.order")
    amt_discount_total = fields.Monetary(string='Discounts', store=True, readonly=True, compute='_compute_amount')
    is_from_inventory = fields.Boolean(string='Is From Inventory')
    is_cancelled_remaining_order = fields.Boolean(string='Is Cancelled Remaining Order')
    is_transfer_order = fields.Boolean(string='Is Transfer Order')



class AccountInvoiceLineExtend(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.product_id.type in ('product','consu'):
                raise UserError(_('Sorry, you are not allowed to delete this invoice line that was create as a result of the Delivery Order'))

        return super(AccountInvoiceLineExtend, self).unlink()

    @api.multi
    def write(self, vals):
        product_id = vals.get('product_id',False)
        account_id = vals.get('account_id',False)
        qty = vals.get('quantity',False)
        is_product = False
        if product_id :
            if self.env['product.product'].browse(product_id).type in ('product','consu'):
                is_product = True
        is_from_inventory = self.invoice_id.is_from_inventory

        if is_product and is_from_inventory :
            raise UserError(_('Sorry, you are not allowed to change the product, that was set by the Delivery Order'))
        if account_id and is_from_inventory :
            raise UserError(_('Sorry, you are not allowed to change the account for the product, that was set by the Delivery Order'))
        if qty and is_from_inventory :
            raise UserError(_('Sorry, you are not allowed to change the quantity for the product, that was set by the Delivery Order'))

        is_cancelled_remaining_order = self.invoice_id.is_cancelled_remaining_order
        if is_product and is_cancelled_remaining_order :
            raise UserError(_('Sorry, you are not allowed to change the product, that was set by the product cancellation activity from the sales app'))

        if account_id and is_cancelled_remaining_order :
            raise UserError(_('Sorry, you are not allowed to change the account, that was set by the product cancellation activity from the sales app'))

        if qty and is_cancelled_remaining_order :
            raise UserError(_('Sorry, you are not allowed to change the qty. that was set by the product cancellation activity from the sales app'))

        is_transfer_order = self.invoice_id.is_transfer_order
        if is_product and is_transfer_order:
            raise UserError(_('Sorry, you are not allowed to change the product, that was set by the product transfer qty. order from the sales app'))

        if account_id and is_transfer_order:
            raise UserError(_('Sorry, you are not allowed to change the account, that was set by the product transfer qty. order from the sales app'))

        if qty and is_transfer_order:
            raise UserError(_('Sorry, you are not allowed to change the qty, that was set by the product transfer qty. order from the sales app'))


        res = super(AccountInvoiceLineExtend, self).write(vals)
        return res



    @api.onchange('discount_amt')
    def _onchange_discount_amt(self):
        for line in self:
            if line.price_unit:
                disc_amt = line.discount_amt
                line.discount = (disc_amt / line.price_unit) * 100

                currency = line.invoice_id and line.invoice_id.currency_id or None
                price = line.price_unit * (1 - (self.discount or 0.0) / 100.0)
                taxes = False
                if line.invoice_line_tax_ids:
                    taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)

                line.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else line.quantity * price

                if line.invoice_id.currency_id and line.invoice_id.currency_id != line.invoice_id.company_id.currency_id:
                    price_subtotal_signed = line.invoice_id.currency_id.compute(price_subtotal_signed, line.invoice_id.company_id.currency_id)
                sign = line.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
                line.price_subtotal_signed = price_subtotal_signed * sign


    @api.onchange('discount')
    def _onchange_discount(self):
        for line in self:
            if line.price_unit:
                disc_amt =  (line.discount / 100) * line.price_unit
                line.discount_amt = disc_amt


    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        res = super(AccountInvoiceLineExtend,self)._compute_price()

        disc_amt =  (self.discount / 100) * self.price_unit
        self.discount_amt = disc_amt



    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLineExtend,self)._onchange_product_id()

        # Analytic Defaults already takes care of this
        # if self.invoice_id.partner_id.acct_analytic_sale_id :
        #     self.account_analytic_id = self.invoice_id.partner_id.acct_analytic_sale_id
        #
        if self.invoice_id.journal_id.analytic_account_id:
            self.account_analytic_id = self.invoice_id.journal_id.analytic_account_id

        # Set discount amount field
        disc_amt = (self.discount / 100) * self.price_unit
        self.discount_amt = disc_amt

        return res





    def _set_additional_fields(self, invoice):
        """ Some modules, such as Purchase, provide a feature to add automatically pre-filled
            invoice lines. However, these modules might not be aware of extra fields which are
            added by extensions of the accounting module.
            This method is intended to be overridden by these extensions, so that any new field can
            easily be auto-filled as well.
            :param invoice : account.invoice corresponding record
            :rtype line : account.invoice.line record
        """

        # It is needed because for invoices that are ceated as a result of inventory transfer action
        res =  super(AccountInvoiceLineExtend,self)._set_additional_fields(invoice)

        # Analytic Defaults already takes care of this
        # if self.invoice_id.partner_id.acct_analytic_sale_id :
        #     self.account_analytic_id = self.invoice_id.partner_id.acct_analytic_sale_id
        if self.invoice_id.journal_id.analytic_account_id:
            self.account_analytic_id = self.invoice_id.journal_id.analytic_account_id
        return  res


    def _calculate_margin_markup_profit(self):
        self.ensure_one()
        if self.cos and (self.price_subtotal_signed > 0 ): # Invoice
            total_cos = self.cos * self.quantity
            gross_profit = self.price_subtotal - total_cos
            self.markup = (gross_profit / total_cos) * 100
            self.gross_margin = (gross_profit / self.price_subtotal) * 100
            self.gross_profit = gross_profit
            self.cos_total = total_cos
        elif self.cos and (self.price_subtotal_signed < 0 ): # Refund  Invoice or a negative invoice line
            total_cos = self.cos * self.quantity
            gross_profit = -(self.price_subtotal - total_cos)
            self.markup = (gross_profit / total_cos) * 100
            self.gross_margin = -(gross_profit / self.price_subtotal_signed) * 100
            self.gross_profit = gross_profit
            self.cos_total = -total_cos



    @api.multi
    def show_invoice(self):
        return {
            'name': _('Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.invoice_id.id)],
            'target': 'new'
        }




    discount_amt = fields.Monetary(string='Disc./ Unit (Amt.)')
    discount_analytic_line = fields.Many2one('account.analytic.line',string="Discount Analytic Line")
    cos = fields.Monetary(string='Unit Cost of Sales')
    cos_total = fields.Monetary(string='Total Cost of Sales')
    # Another example of Gross margin/Gross Profit margin/Gross Income  is: lets say i want to make
    # 30% gross profit margin from each item i sell, then if i sell an item for N100, then i will want
    # to make N30 from it, or for each N1, i want to make 30Kobo. Then the calculation is as follow:
    # (30/100)profit margin * N100 item = N30 gain
    # 100 - 30 = N70 cost price
    # The the markup percentage i need to add to all my item to attain the 30% gross margin profit is:
    # markup% = (30/70) * 100 = 42.86%
    # It means that i need to add 42.86% markup of the cost price on all my items to make 30% gross margin for all my items
    # usually amount carry so much noise. so use GP margin to express gross profit amount in percentage.
    # Lets say for each N100 item i sell, I made N20. then my gross profit percentage or gross margin will be calulated as follows;
    # if N100 item = N20 gross profit,
    # then N1 item = X gross profit,
    # N100 item * X gross profit = N20 gross profit * N1 item;
    # X gross_profit = (N20 gross profit * N1 item) / N100 item
    # X gross_profit = N0.2 gross profit
    # thus, N1 Item = N0.2 gross profit
    # If gross profit is changed to gross profit percentage(also called gross profit margin);
    # then N0.2 * 100 = 20%,
    # so for each N1 item, I make 20% gross profit
    # the same calculation style can be used for markup percentage calculation, for adding markup on top of cost price to get selling price
    # if for every N80 cost price = N20 gross profit, then N1 cp = X gp. X gp = 0.25. It means I need to add 25% of the item cost price to the item cost price to get the selling price
    gross_profit = fields.Monetary(string='Gross Profit', help="Gross Profit(Gross Income) = Selling Price(Net Revenue) - Total Cost of Sales. It becomes gross margin/gross profit margin/gross profit percentage, when gross profit is divided by net sales(revenue). see: https://en.wikipedia.org/wiki/Gross_profit, http://www.myaccountingcourse.com/financial-ratios/gross-profit-margin")
    markup = fields.Float(string='Markup(%)',help="Gross Profit(Gross Income) / Cost of Sales. The percentage added on the cost of goods to get the selling price")
    gross_margin = fields.Float(string='Gross Profit Margin(%)' ,help="Gross Profit / Selling Price(Revenue). Also known as Gross Margin/Gross Profit Margin/Gross Income Margin/Gross Profit Percentage. The gross profit divided by net revenue(sales). e.g.if gp margin is 33% then it means that for every 1 naira sales/revenue, the company gains extra 0.33 naira. thus, the company makes 33% gross profit for each of item sold. Small GP Margin may mean the COG sold is on the high side, or the selling price is low, that is why the profit is low, and viceversa. GP margin measures how efficient a company is, with respect to the goods that are purchased/manufactured. It shows how much profit a company makes for each sold item" )
    date_invoice = fields.Date(string="Line Date",related='invoice_id.date_invoice',ondelete='cascade', index=True,store=True)
    categ_id = fields.Many2one('product.category',string='Prod. Category',related='product_id.categ_id')


# class ResPartner(models.Model):
#     _inherit = "res.partner"
#
#     acct_analytic_sale_id = fields.Many2one('account.analytic.account', string="Sales Analytic Account")
