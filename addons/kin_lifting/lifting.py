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


class ProductLifting(models.Model):
    _name = 'product.lifting'
    _inherit = ['mail.thread']
    _order = 'do_number desc'


    @api.multi
    def action_view_picking(self):
        picking_id = self.mapped('picking_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')

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
        if len(picking_id) > 1:
            result['domain'] = "[('id','in',%s)]" % picking_id.id
        elif len(picking_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = picking_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def amount_to_text(self, amt):
        amount_text = amount_to_text(amt).replace('euro', '').replace('Cent', '')
        return str.upper(amount_text + ' ')

    @api.model
    def create(self,vals):
        res = super(ProductLifting,self).create(vals)

        if res.picking_id.pack_operation_product_ids :
            IssuedProducts = res.picking_id.pack_operation_product_ids.filtered(
                lambda dline: dline.product_id == res.product_id)
            if not IssuedProducts:
                raise UserError(_('%s does not exist in the operation products to be issued.' % (res.product_id.name)))

        if res.picking_id.operation_type == 'outgoing'  and res.picking_id.sale_id and res.picking_id.sale_id.station_product_allocation_ids  and not res.sale_product_distribution_id:

            product_distribution = res.picking_id.sale_id.station_product_allocation_ids

            #then create the sales order equivalent
            sd_vals = {'product_id': vals.get('product_id') ,
                       'delivered_qty': vals.get('delivered_qty'),
                       'state': vals.get('state'),
                       'to_product_location_id': vals.get('to_product_location_id'),
                       'ordered_qty': vals.get('ordered_qty'),
                       'lift_date': vals.get('lift_date'),
                       'partner_id': vals.get('partner_id'),
                       'picking_id': vals.get('picking_id'),
                       'picking_product_lifting_id': res.id,
                       'sale_id':res.picking_id.sale_id.id,
                       'origin':res.picking_id.origin,
                       'is_created_from_stock' : True,
                       'truck_id' : res.picking_id.trucker_id and res.picking_id.trucker_id.id or False,
                       }
            sd_id = product_distribution.create(sd_vals)
            res.sale_product_distribution_id = sd_id
        if res.picking_id:
            res.truck_id = res.picking_id.trucker_id
            res.from_product_location_id = res.picking_id.from_product_location_id
            res.do_number = res.picking_id.name
            res.ref_tlo = res.picking_id.ref_tlo
            res.origin = res.picking_id.origin
            if not res.ido_number:
                res.ido_number = res.env['ir.sequence'].next_by_code('ido_code')


        return res



    @api.multi
    def write(self,vals):

        if self.sale_product_distribution_id :
            #Note that the sales should not be allowed to edit  product distribution parameter because of the following error
            #"RuntimeError: maximum recursion depth exceeded while calling a Python object"
            if vals.get('ido_number',False) :
                self.sale_product_distribution_id.ido_number = vals.get('ido_number')
            if vals.get('truck_id',False) :
                self.sale_product_distribution_id.truck_id = vals.get('truck_id')
            if vals.get('from_product_location_id',False) :
                self.sale_product_distribution_id.from_product_location_id = vals.get('from_product_location_id')
            if vals.get('picking_id',False) :
                self.sale_product_distribution_id.picking_id = vals.get('picking_id')
            if vals.get('to_product_location_id',False) and self.sale_product_distribution_id.to_product_location_id :
                pass
                #raise UserError(_('Sorry, you cannot change the delivery location for the I.D.O that is linked to the Sales Order line. You may rather delete and re-add this I.D.O'))
                #self.sale_product_distribution_id.to_product_location_id = vals.get('to_product_location_id')
            if vals.get('partner_id',False) and self.sale_product_distribution_id.partner_id :
                #raise UserError(_('Sorry, you cannot change the Customer for the I.D.O that is linked to the Sales Order line. You may rather delete and re-add this I.D.O'))
                pass
            if vals.get('do_number',False) :
                self.sale_product_distribution_id.do_number = vals.get('do_number')
            if vals.get('ref_tlo',False) :
                self.sale_product_distribution_id.ref_tlo = vals.get('ref_tlo')
            if vals.get('product_id',False) and self.sale_product_distribution_id.product_id :
                #raise UserError(_('Sorry, you cannot change the Product for the I.D.O that is linked to the Sales Order line. You may rather delete and re-add this I.D.O'))
                pass
            if vals.get('ordered_qty',False) and self.sale_product_distribution_id.ordered_qty :
                #raise UserError(_('Sorry, you cannot change the Ordered Qty. for the I.D.O that is linked to the Sales Order line. You may rather delete and re-add this I.D.O'))
                pass
            if vals.get('delivered_qty',False) :
                self.sale_product_distribution_id.delivered_qty = vals.get('delivered_qty')
            if vals.get('is_duty_free',False) :
                self.sale_product_distribution_id.is_duty_free = vals.get('is_duty_free')
            if vals.get('lift_date',False) :
                self.sale_product_distribution_id.lift_date = vals.get('lift_date')
            if vals.get('delivery_rate',False) :
                self.sale_product_distribution_id.delivery_rate = vals.get('delivery_rate')
            if vals.get('trucker_invoice_id',False) :
                self.sale_product_distribution_id.trucker_invoice_id = vals.get('trucker_invoice_id')
            if vals.get('customer_invoice_id',False) :
                self.sale_product_distribution_id.customer_invoice_id = vals.get('customer_invoice_id')
        else:
            pass
            #Create the new lifting record correspondence  on the sales order. this is for manually added lifting records without no link.
            # vals= {}
            # self.sale_id.station_product_allocation_ids.create()


        return super(ProductLifting,self).write(vals)


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state == 'done' :
                raise UserError(_('This line cannot be removed because product has been delivered for this line. You may cancel and reset back to draft, then try deleting the line'))

            rec.sale_product_distribution_id.unlink()
        return super(ProductLifting, self).unlink()


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



    def create_shortage_invoice(self, rate=0, qty=0, inv_type='out_invoice'):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        company = self.env.user.company_id
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        partner_id = self.truck_id.partner_id
        if not partner_id:
            raise UserError(_("No Trucker Company Set for the Truck. Please check truck configuration page"))

        invoice_vals = {
            'name': self.picking_id.name,
            'origin': self.picking_id.origin,
            'type': inv_type,
            'reference': self.picking_id.shipment_ref,
            'account_id': partner_id.property_account_receivable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id,
            'is_shortage_invoice': True,
            'user_id': self.picking_id.sale_id.user_id.id,
            'picking_shortage_id' : self.picking_id.id,
            'is_from_inventory' : True,
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

            orderline = self.picking_id.sale_id.order_line.filtered(lambda line: line.product_id == self.product_id)
            if not orderline:
                raise UserError(_('No Sales Order Line for this Product: %s' % (self.product_id.name)))
            inv_line = {
                'name': 'Shortage invoice for %s for %s at rate of %s' % (partner_id.name,qty, rate),
                'origin': self.do_number,
                'account_id': account.id,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id or False,
                'account_analytic_id': default_analytic_account and default_analytic_account.analytic_id.id,
                'invoice_id': invoice.id,
                'sale_line_ids': [(6, 0, [orderline.id])] # Never remove this sale_line_ids. This determines the cost of goods sold using the FIFO and not from the product page
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
        group_obj = self.env.ref('kin_lifting.group_receive_lifting_record_shortage_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New D.O Lifting Shortage Invoice has been created from the Instant D.O %s for the Mother D.O %s by %s') % (
                                     self.name, self.picking_id.name, self.env.user.name),
                                 subject='A New Lifting Shortage Invoice has been created', subtype='mail.mt_comment')
        return invoice


    def create_customer_invoice(self):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        company = self.env.user.company_id
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        partner_id = self.partner_id
        if not partner_id:
            raise UserError(_("No Customer Set"))

        invoice_vals = {
            'name': self.picking_id.name,
            'origin': self.picking_id.origin,
            'type': 'out_invoice',
            'reference': self.picking_id.shipment_ref,
            'account_id': partner_id.property_account_receivable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id,
            'user_id': self.picking_id.sale_id.user_id.id,
            'product_allocation_customer_invoice_id' : self.picking_id.id,
            'is_duty_free' : self.picking_id.is_duty_free,
            'is_from_inventory': True
        }
        invoice = inv_obj.create(invoice_vals)

        lines = []

        if not float_is_zero(1, precision_digits=precision):
            account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(
                    _('Please define income account for the product: "%s" (id:%d) - or for its category: "%s".') % (
                        self.product_id.name, self.product_id.id,
                        self.product_id.categ_id.name))

            default_analytic_account = self.env['account.analytic.default'].account_get(
                self.product_id.id, partner_id.id,
                self.env.user.id, datetime.today())

            orderline = self.picking_id.sale_id.order_line.filtered(lambda line: line.product_id == self.product_id)
            if not orderline:
                raise UserError(_('No Sales Order Line for this Product: %s' % (self.product_id.name)))
            inv_line = {
                'name' :  self.product_id.name,
                'origin': orderline.order_id.name,
                'account_id': account.id,
                'price_unit': orderline.price_unit,
                'quantity': self.delivered_qty,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id or False,
                'account_analytic_id': default_analytic_account and default_analytic_account.analytic_id.id,
                'invoice_id': invoice.id,
                'is_duty_free':self.is_duty_free,
                'sale_line_ids': [(6, 0, [orderline.id])]  #Never remove this sale_line_ids. This determines the cost of goods sold using the FIFO and not from the product page
            }
            self.env['account.invoice.line'].create(inv_line)

            orderline_services = self.picking_id.sale_id.order_line.filtered(lambda line: line.product_id.type == 'service')
            for line in orderline_services :
                service_account = line.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
                sinv_line = {
                    'name':line.product_id.name,
                    'origin': line.order_id.name,
                    'account_id': service_account.id,
                    'price_unit': line.price_unit,
                    'quantity': self.delivered_qty,
                    'uom_id': line.product_id.uom_id.id,
                    'product_id': line.product_id.id or False,
                    'account_analytic_id': default_analytic_account and default_analytic_account.analytic_id.id,
                    'invoice_id': invoice.id,
                    #'sale_line_ids': [(6, 0, [orderline_services.id])] #no need for this, because it generates error if the services are more than one
                }
                self.env['account.invoice.line'].create(sinv_line)

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
        group_obj = self.env.ref('kin_lifting.group_receive_lifting_delivered_customer_invoice_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New Customer Invoice has been created as a result of the delivered Qty from the Instant D.O  %s for the delivery order %s by %s') % (
                                     self.name, self.picking_id.name, self.env.user.name),
                                 subject='A New Customer Invoice has been created', subtype='mail.mt_comment')
        return invoice



    def create_trucker_bill(self,rate=0,qty=0,inv_type='out_invoice'):
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

        partner_id = self.truck_id.partner_id
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
            'product_allocation_trucker_bill_id': self.picking_id.id,
            'user_id': self.picking_id.sale_id.user_id.id,
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
                'name': 'Trucker Bill for %s (%s), for qty of %s at rate of %s' % (partner_id.name,self.truck_id.name,qty,rate),
                'origin': self.picking_id.origin,
                'account_id': account.id,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': company.product_id.uom_id.id,
                'product_id': company.product_id.id or False,
                'account_analytic_id':  default_analytic_account and default_analytic_account.analytic_id.id,
                'invoice_id': invoice.id
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
                'A New Trucker Invoice has been created from the lifting record with delivery order %s by %s') % (
                                   self.picking_id.name,self.env.user.name),
                              subject='A New Trucker Invoice has been created', subtype='mail.mt_comment')
        return invoice


    @api.onchange('ordered_qty','delivered_qty')
    def _check_negative_qty(self):
        for rec  in self:
            if rec.ordered_qty < 0:
                raise UserError(_('Issued Qty. cannot be lesser than  Zero'))
            if rec.delivered_qty < 0:
                raise UserError(_('Delivered Qty. cannot be lesser than Zero'))

    @api.onchange('partner_id')
    def _compute_delivery(self):
        for rec in self:
            rec.to_product_location_id = self.partner_id.delivery_location_id



    @api.onchange('to_product_location_id')
    def _compute_delivery_rate(self):
        delivery_rate_obj = self.env['kin.delivery.rate']
        for rec in self:
            if rec.picking_id.from_product_location_id and  rec.to_product_location_id:
                search_rec = delivery_rate_obj.search(
                    [('from_product_location_id', '=', rec.picking_id.from_product_location_id.id),
                     ('to_product_location_id', '=', rec.to_product_location_id.id)])
                if search_rec :
                    rec.delivery_rate = search_rec[0].delivery_rate


    def compare_qty(self):
        if self.picking_id.state == 'done':
            picking_id = self.picking_id
            for line in picking_id.pack_operation_product_ids:
                issued_qty = 0
                IssuedProducts = picking_id.product_lifting_ids.filtered(lambda dline: dline.product_id == line.product_id)
                if not IssuedProducts:
                    raise UserError(_('%s does not exist in the operation products to be issued'%(line.product_id.name)))
                for isuline in IssuedProducts:
                    issued_qty += isuline.ordered_qty
                if IssuedProducts and line.qty_done != issued_qty :
                    raise UserError(_('Sorry, the product (%s) operation done qty (%s) must equal the total product lifting issued qty (%s). So you have (%s) qty of (%s) left to be set on the Issued Qty. for the Lifting Records'%(line.product_id.name,line.qty_done,issued_qty,line.qty_done - issued_qty,line.product_id.name )))


    @api.multi
    def action_print_ido(self):
        return self.env['report'].get_action(self, 'kin_lifting.report_instant_delivery_order_lifting')


    @api.multi
    def action_mark_transit(self):
        if not self.truck_id:
            raise UserError(_('Please assign the truck for this D.O'))
        picking_id = self.picking_id
        IssuedProducts = picking_id.pack_operation_product_ids.filtered(lambda dline: dline.product_id == self.product_id)
        if not IssuedProducts:
            raise UserError(_('%s does not exist in the operation products to be issued. Ensure that the the Mother D.O done qty has been set and validated before performing this operation' % (self.product_id.name)))
        if picking_id.state != 'done' :
            raise UserError(_('Please validate the Mother D.O before performing this task'))

        # check if the total done qty matches issued qty in product lifting
        self.compare_qty()
        self.state = 'in_transit'

    @api.multi
    def action_validate(self):
        if self.customer_invoice_id :
            raise UserError(_("A customer's invoice record has been previously created. Please refresh your browser"))

        if self.trucker_invoice_id :
            raise UserError(_("A trucker's bill record has been previously created. Please refresh your browser"))

        if self.picking_id.shortage_invoice_id:
            raise UserError(_('A shortage invoice record has been previously created. Please refresh your browser'))

        picking_id = self.picking_id
        if picking_id.state != 'done':
            raise UserError(_('Set the Done Qty on the Operations tab and Validate the Mother Delivery Order before validating the Instant Delivery Order'))

        if self.picking_id.partner_id :
            is_aminata_reserve = self.picking_id.partner_id.is_aminata_retail_reserve
            if is_aminata_reserve:
                if self.ordered_qty != self.delivered_qty:
                    raise UserError('Sorry, Delivered Qty. must be Equal to Lifted Quantity for %s' % self.picking_id.partner_id.name)

        IssuedProducts = picking_id.pack_operation_product_ids.filtered(lambda dline: dline.product_id == self.product_id)
        if not IssuedProducts:
            raise UserError(_('%s does not exist in the operation products to be issued' % (self.product_id.name)))

        self.state = 'done'
        picking_obj = self.env['stock.picking']
        company = self.env.user.company_id

        if self.delivered_qty <= 0 :
            raise UserError(_('Delivered Quantity should be more than zero'))

        if self.ordered_qty <= 0:
            raise UserError(_('Ordered Quantity should be more than zero'))

        if not self.do_number:
            raise UserError(_('D.O Number has not been populated on the lifting record. Please select the truck to automatically populate the D.O Number for each lifting record'))
        picking_id = self.picking_id
        undone_pa = picking_id.product_lifting_ids.filtered(lambda pa: pa.state != 'done')
        if not undone_pa :
            #check if the total done qty matches issued qty in product lifting
            self.compare_qty()

            #calculate the shortage invoice if any
            shortage = picking_id.shortage
            if shortage > 0 and company.is_create_shortage_invoice:
                if company.is_create_shortage_invoice and not self.product_id:
                    raise UserError(_('No product for the lifting record'))
                if self.product_id.sales_price_transport_charge <= 0:
                    raise UserError(_('Sales Price transport Charge is lesser than or equal to zero'))
                inv_shortage = self.create_shortage_invoice(abs(self.product_id.sales_price_transport_charge),
                                                            qty=shortage,
                                                            inv_type='out_invoice')  # Trucker is a debtor
                picking_id.shortage_invoice_id = inv_shortage
                picking_id.is_shortage = True

        #create customers invoice based on delivered qty
        self.customer_invoice_id = self.create_customer_invoice()

        #create truckers bill based on delivered qty
        if self.delivery_rate and self.delivery_rate != 0 and company.is_enforce_trucker_delivery:
            if company.is_enforce_trucker_delivery and not company.product_id:
                raise UserError(_('Please set the transport income product on the general settings page'))
            inv = self.create_trucker_bill(abs(self.delivery_rate), qty=self.delivered_qty, inv_type='in_invoice')  # Trucker is a creditor
            self.trucker_invoice_id = inv



    @api.multi
    def action_cancel_reset(self):
        self.trucker_invoice_id.unlink()
        if self.customer_invoice_id :
            self.customer_invoice_id.is_from_inventory =  False
        self.customer_invoice_id.unlink()
        if self.picking_id.shortage_invoice_id:
            self.picking_id.shortage_invoice_id.is_from_inventory =  False
        self.picking_id.shortage_invoice_id.unlink()
        self.state = 'draft'

    @api.onchange('partner_id')
    def _set_address(self):
        for rec in self:
            rec.address = rec.partner_id.street

    ido_number = fields.Char(string='I.D.O Number')
    name = fields.Char(related='ido_number')
    truck_id = fields.Many2one('kin.trucker', string='Truck No.')
    from_product_location_id = fields.Many2one('kin.product.location', string='Source Product Location')
    to_product_location_id = fields.Many2one('kin.product.location', string='Delivery Location')
    partner_id = fields.Many2one('res.partner', string='Customer')
    picking_id = fields.Many2one('stock.picking', string='Picking')
    do_number = fields.Char(string='D.O. Number')
    ref_tlo = fields.Char(string='Ref. T.L.O')
    origin = fields.Char(string='Ref. P.O')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    ordered_qty = fields.Float(string='Lifted Qty')
    delivered_qty = fields.Float(string='Delivered Qty.')
    sale_id = fields.Many2one('sale.order', string='Sales')
    lift_date = fields.Date('Lift Date', default=fields.Datetime.now)
    delivery_rate = fields.Float('Delivery Rate',compute='_compute_delivery_rate')
    trucker_invoice_id = fields.Many2one('account.invoice', string='Trucker Bill')
    customer_invoice_id = fields.Many2one('account.invoice', string='Customer Invoice')
    partner_truck_id = fields.Many2one('res.partner', string="Trucker's Owner")
    sale_product_distribution_id = fields.Many2one('station.product.allocation',string='Sales Product Allocation')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get(
        'product.lifting'))
    state = fields.Selection([('draft', 'Draft'), ('in_transit', 'Transit'), ('done', 'Done'), ('cancel', 'Cancel')],
                             default='draft', string='Status')
    is_duty_free = fields.Boolean('Is Duty Free')
    address = fields.Text(string="Address")
    plate_no = fields.Char('Plate No.')
    is_show_other_customer_name = fields.Boolean('Show Other Customer Name')
    other_customer_name =  fields.Char(string='Other Customer Name')





class StationProductAllocation(models.Model):
    _name = 'station.product.allocation'

    @api.multi
    def write(self,vals):
        res = super(StationProductAllocation,self).write(vals)

        if self.picking_product_lifting_id :
            # if  self.picking_product_lifting_id.state == 'done':
            #     raise UserError(_('Sorry, the product has been lifted already and delivered successfully. So no change can be effected'))
            if vals.get('partner_id',False) :
                self.picking_product_lifting_id.partner_id = vals.get('partner_id')
            if vals.get('to_product_location_id',False) :
                self.picking_product_lifting_id.to_product_location_id = vals.get('to_product_location_id')
            if vals.get('product_id',False) :
                self.picking_product_lifting_id.product_id = vals.get('product_id')
            if vals.get('ordered_qty',False) :
                self.picking_product_lifting_id.ordered_qty = vals.get('ordered_qty')


        return res


    ido_number = fields.Char(string='I.D.O Number')
    truck_id = fields.Many2one('kin.trucker', string='Truck No.')
    from_product_location_id = fields.Many2one('kin.product.location', string='Source Product Location')
    to_product_location_id = fields.Many2one('kin.product.location', string='Delivery Location')
    partner_id = fields.Many2one('res.partner', string='Customer')
    picking_id = fields.Many2one('stock.picking',string='Picking')
    do_number = fields.Char(string='D.O. Number')
    ref_tlo = fields.Char(string='Ref. T.L.O')
    origin = fields.Char(string='Ref. P.O',related='sale_id.name')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    ordered_qty = fields.Float(string='Ordered Qty')
    delivered_qty = fields.Float(string='Delivered Qty.')
    sale_id = fields.Many2one('sale.order',string='Sales')
    lift_date = fields.Date('Lift Date',default=fields.Datetime.now)
    delivery_rate = fields.Float('Delivery Rate')
    is_duty_free = fields.Boolean('Is Duty Free')
    trucker_invoice_id = fields.Many2one('account.invoice',string='Trucker Bill')
    customer_invoice_id = fields.Many2one('account.invoice', string='Customer Invoice')
    partner_truck_id = fields.Many2one('res.partner', string="Trucker's Owner")
    picking_product_lifting_id = fields.Many2one('product.lifting',string='Product Lifting')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True)
    company_id = fields.Many2one('res.company',default=lambda self: self.env['res.company']._company_default_get('station.product.allocation'))
    state = fields.Selection([('draft', 'Draft'),('in_transit','Transit'), ('done', 'Done'), ('cancel', 'Cancel')], default='draft' ,string='Status')
    is_created_from_stock = fields.Boolean(string='Created From Inventory')

class SalesOrderLifting(models.Model):
    _inherit = 'sale.order'

    def compare_qty(self):
        for line in self.order_line:
            distribution_qty = 0
            distrProducts = self.station_product_allocation_ids.filtered(lambda dline: dline.product_id == line.product_id)
            for dpline in distrProducts:
                distribution_qty += dpline.ordered_qty
            if distrProducts and line.product_uom_qty != distribution_qty :
                raise UserError(_('Sorry, the product (%s) total ordered qty must equal the total product allocation qty.'%(line.product_id.name)))


    @api.multi
    def write(self,vals):
        res = super(SalesOrderLifting,self).write(vals)
        if not vals.get('invoice_ids',False):
            for rec in self:
                rec.compare_qty()
        return res

    station_product_allocation_ids = fields.One2many('station.product.allocation','sale_id',string='Product Distribution')


class StockPicking(models.Model):
    _inherit = "stock.picking"


    @api.onchange('is_duty_free')
    def _set_is_duty_free(self):
        for rec in self:
            for pa in self.product_lifting_ids:
                pa.is_duty_free = rec.is_duty_free

    @api.model
    def create(self,vals):
        res = super(StockPicking,self).create(vals)
        #duplicate sales order product distribution here
        if res.operation_type == 'outgoing':
            product_lifting_obj = self.env['product.lifting']
            sale_order = self.env['sale.order']
            sale_order_obj = sale_order.search([('name', '=', res.origin)])

            for prod_distr_line in sale_order_obj.station_product_allocation_ids :
                lift_vals = {
                    'to_product_location_id': prod_distr_line.to_product_location_id.id,
                    'partner_id': prod_distr_line.partner_id.id,
                    'picking_id': res.id,
                    'origin': res.origin,
                    'product_id': prod_distr_line.product_id.id,
                    'product_uom': prod_distr_line.product_uom.id,
                    'ordered_qty': prod_distr_line.ordered_qty,
                    'sale_id': sale_order_obj.id,
                    'sale_product_distribution_id':  prod_distr_line.id,
                }

                lift_id = product_lifting_obj.create(lift_vals)
                prod_distr_line.picking_product_lifting_id = lift_id
                prod_distr_line.picking_id = self

            if res.backorder_id:
                res.product_lifting_ids.unlink()

        return res

    def _compute_invoice_count_shortage(self):
        for rec in self:
            rec.invoice_count_shortage = len(rec.shortage_invoice_id)

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


    @api.onchange('trucker_id')
    def _compute_set_truckers(self):
        for rec in self:
            for pa in rec.product_lifting_ids:
                pa.truck_id = rec.trucker_id
                pa.from_product_location_id = rec.from_product_location_id
                # pa.picking_id = self
                pa.do_number = rec.name
                pa.ref_tlo = rec.ref_tlo
                if not pa.ido_number:
                    pa.ido_number = rec.env['ir.sequence'].next_by_code('ido_code')


    @api.onchange('product_lifting_ids')
    def _compute_shortage(self):
        for rec in self:
            total_ordered_qty = total_delivered_qty  = 0
            for pa in rec.product_lifting_ids:
                total_ordered_qty += pa.ordered_qty
                total_delivered_qty += pa.delivered_qty
            rec.shortage = total_ordered_qty - total_delivered_qty
            if rec.shortage > 0 :
                rec.is_shortage = True
            else:
                rec.is_shortage = False



    trucker_invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)
    trucker_invoice_id = fields.Many2one('account.invoice')
    invoice_count_shortage = fields.Integer(compute="_compute_invoice_count_shortage", string='# of Shortage Invoices',
                                            copy=False, default=0)
    shortage_invoice_id = fields.Many2one('account.invoice', string='Shortage Invoice')
    is_shortage = fields.Boolean('Is Shortage')
    shortage = fields.Float(string='Shortage',compute='_compute_shortage')
    comment = fields.Text("Comment")
    sales_price = fields.Float('Pump price')
    is_duty_free = fields.Boolean('Is Duty Free')
    product_lifting_ids = fields.One2many('product.lifting','picking_id',string='Product Lifting Records')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def btn_view_shortage_picking(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Shortage Pickings'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.picking_shortage_id])],
            #'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            #'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('picking_shortage_id')
    def _compute_shortage_picking_count(self):
        for rec in self :
            rec.picking_shortage_count = len(rec.picking_shortage_id)

    @api.multi
    def btn_view_customer_picking(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Customer Pickings'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.product_allocation_customer_invoice_id])],
            #'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            #'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('product_allocation_customer_invoice_id')
    def _compute_pa_customer_count(self):
        for rec in self :
            rec.pa_customer_invoice_count = len(rec.product_allocation_customer_invoice_id)


    @api.multi
    def btn_view_trucker_picking(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Trucker Bill'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.product_allocation_trucker_bill_id])],
            #'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            #'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('product_allocation_trucker_bill_id')
    def _compute_pa_trucker_count(self):
        for rec in self :
            rec.pa_trucker_bill_count = len(rec.product_allocation_trucker_bill_id)


    picking_shortage_id = fields.Many2one('stock.picking', string='Shortage Picking')
    picking_shortage_count = fields.Integer(compute="_compute_shortage_picking_count", string='# of Shortage Pickings',
                                            copy=False, default=0)

    product_allocation_customer_invoice_id = fields.Many2one('stock.picking',string='Product Distribution Customer Invoice')
    pa_customer_invoice_count = fields.Integer(compute="_compute_pa_customer_count", string='# of Customer Pickings',
                                            copy=False, default=0)

    product_allocation_trucker_bill_id = fields.Many2one('stock.picking',string='Product Distribution Trucker Bill')
    pa_trucker_bill_count = fields.Integer(compute="_compute_pa_trucker_count", string='# of Vendor Pickings',
                                       copy=False, default=0)
    is_duty_free = fields.Boolean('Is Duty Free')



class AccountInvoiceLineLifting(models.Model):
    _inherit = 'account.invoice.line'

    is_duty_free = fields.Boolean('Is Duty Free')


class ResCompanyReport(models.Model):
    _inherit = "res.company"

    header_data_inventory = fields.Html(string='Instant Delivery Header Data')



