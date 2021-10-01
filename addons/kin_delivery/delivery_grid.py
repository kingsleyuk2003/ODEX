# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp import SUPERUSER_ID
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_is_zero, float_compare,float_round, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
from openerp.tools import amount_to_text
from dateutil.relativedelta import relativedelta
from datetime import *


class ProductLocation(models.Model):
    _name = 'kin.product.location'

    name = fields.Char('Product Location')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one('res.country.state',string='State')
    address = fields.Char('Address')
    delivery_rate_from_product_location_ids = fields.One2many('kin.delivery.rate','from_product_location_id',string='From Product Location Delivery Rate')
    delivery_rate_to_product_location_ids = fields.One2many('kin.delivery.rate', 'to_product_location_id', string='To Product Location Delivery Rate')
    is_default_source_location = fields.Boolean('Is Default Source location')


class DeliveryRate(models.Model):
    _name = 'kin.delivery.rate'

    from_product_location_id = fields.Many2one('kin.product.location',string='From Product Location',ondelete='restrict')
    to_product_location_id = fields.Many2one('kin.product.location',string='To Product Location',ondelete='restrict')
    delivery_rate = fields.Float(string='Delivery Rate')


class DeliveryRegister(models.Model):
    _name = 'kin.delivery.register'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Delivery Register'
    _order = 'name desc'


    def _compute_invoice_count(self):
        self.trucker_invoice_count = len(self.trucker_invoice_id)

    #CView the trucker Bill
    @api.multi
    def action_view_invoice(self):
        trucker_invoice_id = self.mapped('trucker_invoice_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree2')
        list_view_id = imd.xmlid_to_res_id('account.invoice_supplier_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_supplier_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'target': 'new'
        }
        if len(trucker_invoice_id) > 1:
            result['domain'] = "[('id','in',%s)]" % trucker_invoice_id.id
        elif len(trucker_invoice_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = trucker_invoice_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    def _compute_invoice_count_shortage(self):
        self.invoice_count_shortage = len(self.shortage_invoice_id)

    @api.multi
    def action_view_shortage_invoice(self):
        shortage_invoice_id = self.mapped('shortage_invoice_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'target': 'new'
        }
        if len(shortage_invoice_id) > 1:
            result['domain'] = "[('id','in',%s)]" % shortage_invoice_id.id
        elif len(shortage_invoice_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = shortage_invoice_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    def create_shortage_invoice(self, rate=0, qty=0, inv_type='out_invoice'):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        company = self.env.user.company_id
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        partner_id = self.partner_id
        if not partner_id:
            raise UserError(_("No Trucker Person Set"))

        invoice_vals = {
            'name': self.picking_id.name,
            'origin': self.picking_id.origin,
            'type': inv_type,
            'reference': self.picking_id.shipment_ref,
            'account_id': partner_id.property_account_receivable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id,
            'is_shortage_invoice': True,
            'user_id': self.env.user.id,
        }

        invoice = inv_obj.create(invoice_vals)

        lines = []

        if not float_is_zero(1, precision_digits=precision):
            account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(
                    _('Please define income account for the shortage product: "%s" (id:%d) - or for its category: "%s".') % (
                        self.product_id.name, self.product_id.id,
                        self.product_id.categ_id.name))

            default_analytic_account = self.env['account.analytic.default'].account_get(
                self.product_id.id, partner_id.id,
                self.env.user.id, datetime.today())

            inv_line = {
                'name': 'Shortage invoice for ' + partner_id.name,
                'origin': self.picking_id.origin,
                'account_id': account.id,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id or False,
                'account_analytic_id': default_analytic_account and default_analytic_account.analytic_id.id,
                'trucker_invoice_id': invoice.id
            }
            self.env['account.invoice.line'].create(inv_line)

        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if invoice.amount_untaxed < 0:
            invoice.type = 'out_refund'
            for line in invoice.invoice_line_ids:
                line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()

        # Send Email to accountants
        user_ids = []
        group_obj = self.env.ref('kin_delivery.group_receive_delivery_register_shortage_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New Shortage Invoice has been created from the delivery register %s for the delivery order %s by %s') % (
                                     self.name, self.picking_id.name, self.env.user.name),
                                 subject='A New Shortage Invoice has been created', subtype='mail.mt_comment')
        return invoice


    def create_invoice(self,rate=0,qty=0,inv_type='out_invoice'):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        company = self.env.user.company_id
        journal_domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', company.id)
        ]
        journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        if not journal_id:
            raise UserError(_('Please define an accounting purchase journal for this company.'))


        partner_id = self.partner_id
        if not partner_id :
            raise UserError(_("No Trucker Person Set"))


        invoice_vals = {
            'name': self.picking_id.name,
            'origin': self.picking_id.origin,
            'type': inv_type,
            'reference': self.picking_id.shipment_ref,
            'account_id': partner_id.property_account_payable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id.id,
            'is_delivery_invoice': True,
            # 'company_id': sale_order.company_id.id,
            'user_id': self.env.user.id,
        }

        invoice = inv_obj.create(invoice_vals)

        lines = []

        if not float_is_zero(1, precision_digits=precision):
            account = company.product_id.property_account_income_id or company.product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(
                    _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                        company.product_id.name, company.product_id.id,
                        company.product_id.categ_id.name))


            default_analytic_account = self.env['account.analytic.default'].account_get(
                company.product_id.id, partner_id.id,
                self.env.user.id, datetime.today())

            inv_line = {
                'name': 'Trucker Bill for ' + partner_id.name,
                'origin': self.picking_id.origin,
                'account_id': account.id,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': company.product_id.uom_id.id,
                'product_id': company.product_id.id or False,
                'account_analytic_id':  default_analytic_account and default_analytic_account.analytic_id.id,
                'trucker_invoice_id': invoice.id
            }
            self.env['account.invoice.line'].create(inv_line)


        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if invoice.amount_untaxed < 0:
            invoice.type = 'out_refund'
            for line in invoice.invoice_line_ids:
                line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()

        #Send Email to accountants
        user_ids = []
        group_obj = self.env.ref('kin_delivery.group_receive_delivery_register_trucker_bill_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New Trucker Invoice has been created from the delivery register %s for the delivery order %s by %s') % (
                                  self.name,  self.picking_id.name,self.env.user.name),
                              subject='A New Trucker Invoice has been created', subtype='mail.mt_comment')
        return invoice



    @api.multi
    def action_cleared(self):

        if self.quantity_delivered <= 0 :
            raise UserError(_('Quantity Delivered should be more than zero'))

        company = self.env.user.company_id

        if self.delivery_rate and company.is_enforce_trucker_delivery:
            if company.is_enforce_trucker_delivery and not company.product_id:
                raise UserError(_('Please set the transport income product on the general settings page'))
            inv = self.create_invoice(abs(self.delivery_rate), qty=self.quantity_delivered, inv_type='in_invoice')  # Trucker is a creditor
            self.trucker_invoice_id = inv.id
            self.state = 'cleared'


        shortage = self.quantity - self.quantity_delivered
        if shortage > 0 and company.is_create_shortage_invoice:
            if company.is_create_shortage_invoice and not self.product_id:
                raise UserError(_('No product for the delivery register'))
            if self.product_id.sales_price_transport_charge <= 0:
                raise UserError(_('Sales Price transport Charge is lesser than or equal to zero'))
            inv_shortage = self.create_shortage_invoice(abs(self.product_id.sales_price_transport_charge), qty=shortage,
                                      inv_type='out_invoice')  # Trucker is a debtor
            self.shortage_invoice_id = inv_shortage.id
            self.is_shortage = True



    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('delv_id_code') or 'New'
        res = super(DeliveryRegister, self).create(vals)
        return res

    @api.multi
    def action_cancel(self):
        self.trucker_invoice_id.unlink()
        self.shortage_invoice_id.unlink()
        self.state = 'cancel'


    @api.multi
    def action_draft(self):
        self.is_shortage = True
        self.state = 'draft'

    @api.multi
    def action_transit(self):
        self.state = 'transit'

    @api.multi
    def unlink(self):
        for rec in self:
            rec.trucker_invoice_id.unlink()
            rec.shortage_invoice_id.unlink()
        return super(DeliveryRegister, self).unlink()

    @api.multi
    def action_view_stock_picking(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Delivery Transfer'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.picking_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('picking_id')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_id)


    def _compute_shortage(self):
        for rec in self:
            rec.shortage = rec.quantity - rec.quantity_delivered

    name = fields.Char('Name')
    do_no = fields.Char('Delivery Order No')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity')
    quantity_delivered = fields.Float(string='Quantity Delivered')
    from_product_location_id = fields.Many2one('kin.product.location',string='From Product Location')
    to_product_location_id = fields.Many2one('kin.product.location',string='To Product Location')
    state = fields.Selection([('draft', 'Draft'), ('transit', 'Truck In Transit'), ('cleared', 'Truck Cleared'), ('cancel', 'Cancel')], default='draft',track_visibility='onchange')
    trucker_invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)
    trucker_invoice_id = fields.Many2one('account.invoice')
    invoice_count_shortage = fields.Integer(compute="_compute_invoice_count_shortage", string='# of Shortage Invoices', copy=False, default=0)
    shortage_invoice_id = fields.Many2one('account.invoice')
    is_shortage = fields.Boolean('Is Shortage')
    shortage = fields.Float(compute="_compute_shortage")
    do_date = fields.Date('Date',default=fields.Datetime.now)
    product_uom = fields.Many2one('product.uom',related='product_id.uom_id', string='Unit of Measure')
    delivery_rate = fields.Float('Delivery Rate')
    sales_price = fields.Float('Sales price')
    partner_id = fields.Many2one('res.partner', string="Trucker's Owner")
    customer_id = fields.Many2one('res.partner',string='Customer')
    truck_no = fields.Char('Truck No')
    other_ref = fields.Char('Other Reference')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Transfer')
    picking_count = fields.Integer(compute="_compute_picking_count", string='# of Transfer', copy=False, default=0)
    comment = fields.Text("Comment")



class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def btn_view_delivery_register(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Delivery Register'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.delivery.register',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.delivery_register_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.one
    # @api.depends('pef_id')
    def _compute_delivery_count(self):
        self.delivery_count = len(self.delivery_register_id)


    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        company = self.env.user.company_id

        if self.partner_id and not self.partner_id.is_truck_delivery_exempt and self.picking_type_code == "outgoing" and company.is_enable_delivery_register :


            if company.is_enforce_trucker_delivery and not self.trucker_id or not self.from_product_location_id or not self.to_product_location_id :
                raise UserError(_('Please the following Fields for delivery are required: Trucker, From Product Location and To Product Location '))
            #create the delivery register
            delivery_register = self.env['kin.delivery.register']
            pack_operation_line = self.pack_operation_product_ids[0]

            # sale_order_lines = self.sale_id.mapped('order_line') #Get the One2many records, then do the following line to search/filter by the parameters where  line.product_id.id == pack_operation_line.product_id
            # so_line = sale_order_lines.filtered(lambda line: line.product_id.id == pack_operation_line.product_id.id)

            delivery_rate_obj = self.env['kin.delivery.rate']
            delivery_rate = delivery_rate_obj.search([('from_product_location_id', '=', self.from_product_location_id.id), ('to_product_location_id', '=', self.to_product_location_id.id)])[0].delivery_rate
            vals = {
                'do_no' : self.name,
                'product_id' : pack_operation_line.product_id.id,
                'quantity' : pack_operation_line.product_qty,
                'from_product_location_id' : self.from_product_location_id.id,
                'to_product_location_id': self.to_product_location_id.id,
                'product_uom' : pack_operation_line.product_uom_id.id,
                'delivery_rate' : delivery_rate,
                'partner_id' : self.trucker_id.partner_id.id,
                'customer_id':self.partner_id.id,
                'state' : 'draft',
                'truck_no': self.trucker_id.name,
                'picking_id':self.id,
                'sales_price':pack_operation_line.product_id.sales_price_transport_charge

            }
            delivery_register_obj = delivery_register.create(vals)
            self.delivery_register_id = delivery_register_obj

            #Notify the Delivery register offcers
            user_ids = []
            group_obj = self.env.ref('kin_delivery.group_receive_delivery_register_notification')
            for user in group_obj.users:
                user_ids.append(user.id)
                self.message_subscribe_users(user_ids=user_ids)
                self.message_post(_('A New Delivery Register from %s has been Created for the Picking Document %s.') % (
                    self.env.user.name, self.name),
                                  subject='A New Delivery Register has been Created ', subtype='mail.mt_comment')

        return  res


    def default_product_location(self):
        prod_loc = self.env['kin.product.location']
        loc = prod_loc.search([('is_default_source_location', '=', True)])
        return loc and loc[0]


    trucker_id = fields.Many2one('kin.trucker',string='Trucker')
    from_product_location_id = fields.Many2one('kin.product.location', string='From Product Location', default=default_product_location)
    to_product_location_id = fields.Many2one('kin.product.location', string='To Product Location')
    delivery_register_id = fields.Many2one('kin.delivery.register',string='Delivery Register')
    delivery_count = fields.Integer(compute="_compute_delivery_count", string='# of Delivery', copy=False, default=0)


class ResCompanyDelivery(models.Model):
    _inherit = "res.company"

    product_id = fields.Many2one('product.product', string='Transport Income Product')
    is_enforce_trucker_delivery = fields.Boolean(string='Enforce Trucker and Route Information on Delivery Order',default=True)
    is_create_shortage_invoice = fields.Boolean(string='Create Shortage Invoice to Driver',default=True)
    is_enable_delivery_register = fields.Boolean(string='Enable Delivery Register Records')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_delivery_invoice = fields.Boolean(string='Delivery Bill')
    is_shortage_invoice = fields.Boolean(string='Shortage Invoice')


class Trucker(models.Model):
    _name = 'kin.trucker'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Truckers'


    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        self.state = 'confirm'

    @api.multi
    def action_approve(self):
        self.state = 'approve'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    name = fields.Char('Truck No.', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner',string='Truck Owner', track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirm'),
         ('approve', 'Approved'),
         ('cancel', 'Cancel')],
        default='draft', track_visibility='onchange')
    chassis_no = fields.Char('Chassis No.')
    tanker_capacity = fields.Float('Tanker Capacity')
    model_make = fields.Char('Model Make')
    insurance_policy = fields.Char('Insurance Policy')
    owner_contact_no = fields.Char('Owner COntact No.')
    successor_name = fields.Char('Successor Name')
    successor_contact = fields.Char('Successor Contact')
    vehicle_date = fields.Date('Vehicle Date')
    insurance_date = fields.Date('Insurance Date')
    insurance_premium = fields.Float('Insurance Premium')
    comment = fields.Text('Note')



class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_truck_delivery_exempt = fields.Boolean('Truck Delivery Exemption')
    delivery_location_id = fields.Many2one('kin.product.location',string='Default Delivery Location')


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    sales_price_transport_charge = fields.Float(string='Sales Price transport Charge')


class AccountInvoiceGrid(models.Model):
    _inherit = 'account.invoice'


    @api.multi
    def btn_view_delivery(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Delivery Register Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.delivery.register',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.delivery_register_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('delivery_register_ids')
    def _compute_dev_count(self):
        for rec in self:
            rec.dev_count = len(rec.delivery_register_ids)

    @api.multi
    def btn_view_delivery_shortage(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Delivery Register Shortage Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.delivery.register',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.delivery_register_shortage_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('delivery_register_ids')
    def _compute_dev_count(self):
        for rec in self:
            rec.dev_count = len(rec.delivery_register_ids)

    @api.depends('delivery_register_shortage_ids')
    def _compute_dev_short_count(self):
        for rec in self:
            rec.dev_short_count = len(rec.delivery_register_shortage_ids)

    dev_count = fields.Integer(compute="_compute_dev_count", string='# of Delivery Records', copy=False, default=0)
    delivery_register_ids = fields.One2many('kin.delivery.register', 'trucker_invoice_id', string='Invoices', readonly=True)
    dev_short_count = fields.Integer(compute="_compute_dev_short_count", string='# of Delivery Shortage Records', copy=False, default=0)
    delivery_register_shortage_ids = fields.One2many('kin.delivery.register', 'shortage_invoice_id', string='Shortage Invoices', readonly=True)