# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_is_zero, float_compare
from urllib import urlencode
from urlparse import urljoin
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, Warning
from openerp.tools import amount_to_text
from datetime import *

class InternalUse(models.Model):
    _inherit = 'kin.internal.use'

    def create_internal_use_sales_order(self):
        order = super(InternalUse, self).create_internal_use_sales_order()
        order.is_ssd_sbu = self.is_ssd_sbu
        order.hr_department_id = self.hr_department_id.id
        order.sbu_id = self.sbu_id.id
        order.is_ssa_allow_split = True
        return order

    @api.multi
    def action_validate(self):
        if not self.is_ssd_sbu :
            raise UserError(_('Please select a category'))
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(InternalUse, self.with_context(ctx)).action_validate()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')


class ThroughputReceipt(models.Model):
    _inherit = 'kin.throughput.receipt'

    def create_throughput_sales_order(self):
        order = super(ThroughputReceipt, self).create_throughput_sales_order()
        order.is_ssd_sbu = self.is_ssd_sbu
        order.hr_department_id = self.hr_department_id.id
        order.sbu_id = self.sbu_id.id
        order.is_ssa_allow_split = True
        return order

    @api.multi
    def action_validate(self):
        if not self.is_ssd_sbu :
            raise UserError(_('Please select a category'))
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(ThroughputReceipt, self.with_context(ctx)).action_validate()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')



class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    @api.multi
    def button_validate(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(StockLandedCost, self.with_context(ctx)).button_validate()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.multi
    def action_done(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(StockInventory, self.with_context(ctx)).action_done()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')




class StockQuant(models.Model):
    _inherit = "stock.quant"


    def _create_account_move_line(self, cr, uid, quants, move, credit_account_id, debit_account_id, journal_id, context=None):
        # group quants by cost
        quant_cost_qty = {}
        for quant in quants:
            if quant_cost_qty.get(quant.cost):
                quant_cost_qty[quant.cost] += quant.qty
            else:
                quant_cost_qty[quant.cost] = quant.qty
        move_obj = self.pool.get('account.move')
        for cost, qty in quant_cost_qty.items():
            move_lines = self._prepare_account_move_line(cr, uid, move, qty, cost, credit_account_id, debit_account_id,
                                                         context=context)
            date = context.get('force_period_date', datetime.today().strftime('%Y-%m-%d'))
            ctx = dict(context)
            is_ssd_sbu = ctx.get('is_ssd_sbu',False)
            hr_department_id = ctx.get('hr_department_id', False)
            sbu_id = ctx.get('sbu_id', False)

            if not is_ssd_sbu :
                is_ssd_sbu = move.picking_id.is_ssd_sbu
            if not hr_department_id :
                hr_department_id = move.picking_id.hr_department_id
            if not sbu_id :
                sbu_id = move.picking_id.sbu_id

            ctx['is_ssd_sbu'] = is_ssd_sbu
            ctx['hr_department_id'] = hr_department_id
            ctx['sbu_id'] = sbu_id
            ctx['is_ssa_allow_split'] = True
            new_move = move_obj.create(cr, uid, {'journal_id': journal_id,
                                                 'line_ids': move_lines,
                                                 'date': date,
                                                 'ref': move.picking_id.name,
                                                 'picking_id': move.picking_id.id }, context=ctx)

            move_obj.post(cr, uid, [new_move], context=context)


class StockPicking(models.Model):
    _inherit = "stock.picking"


    @api.model
    def create(self, vals):
        res = super(StockPicking,self).create(vals)
        res.is_ssd_sbu = self.env.context.get('is_ssd_sbu', False)
        res.hr_department_id = self.env.context.get('hr_department_id', False)
        res.sbu_id = self.env.context.get('sbu_id', False)
        res.is_ssa_allow_split = self.env.context.get('is_ssa_allow_split', True)

        return res


    def create_customer_invoice_loading_ticket(self,inv_refund=False):
        inv = super(StockPicking,self).create_customer_invoice_loading_ticket(inv_refund)
        inv.is_ssd_sbu = self.is_ssd_sbu
        inv.hr_department_id = self.hr_department_id.id
        inv.sbu_id = self.sbu_id.id
        inv.is_ssa_allow_split = True
        return inv

    def update_shore_recipt_sts(self):
        qty_done = self.pack_operation_ids[0].qty_done
        picking_type_code = self.picking_type_code
        purchase_order = self.purchase_id
        if picking_type_code == "incoming" and purchase_order:
            ship_to_ship_id = purchase_order.ship_to_ship_id
            if ship_to_ship_id:
                shore_tank = qty_done / purchase_order.conv_rate
                ullage_bdischarge_mt = self.ullage_bdischarge_mt
                ullage_bdischarge_ltrs = self.ullage_bdischarge_ltrs
                ullage_report_ltrs = self.ullage_report_ltrs
                ship_to_ship_id.shore_receipt = qty_done
                ship_to_ship_id.shore_tank = shore_tank
                if not ullage_bdischarge_mt :
                    raise UserError('Please enter the Ullage b/4 DISCH(MT)')
                ship_to_ship_id.ullage_bdischarge_mt = ullage_bdischarge_mt

                if not ullage_bdischarge_ltrs :
                    raise UserError('Please enter the Ullage b/4 DISCH(ltrs)')
                ship_to_ship_id.ullage_bdischarge_ltrs = ullage_bdischarge_ltrs

                if not ullage_report_ltrs :
                    raise UserError('Please enter the Ullage report (ltr)')
                ship_to_ship_id.ullage_report_ltrs = ullage_report_ltrs


    @api.multi
    def do_transfer(self):
        self.update_shore_recipt_sts()
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True

        if self.is_loading_ticket or self.is_exdepot_ticket or self.is_throughput_ticket or self.is_internal_use_ticket:
            self.waybill_no = self.env['ir.sequence'].next_by_code('waybill_id')

            if self.is_throughput_ticket :
                self.waybill_no  = self.env['ir.sequence'].next_by_code('thru_delv_code')

            if self.is_internal_use_ticket :
                self.waybill_no  = self.env['ir.sequence'].next_by_code('intu_delv_code')

            if self.is_block_ticket:
                raise UserError(_("Sorry, Ticket is currently blocked and cannot be Dispatched"))

            if not self.is_correct_truck_no:
                raise UserError(_("Sorry, Truck No. is not correct."))

            if not self.is_exdepot_ticket and self.picking_type_code == 'outgoing' and self.sale_id and self.ticket_load_qty != self.total_dispatch_qty:
                raise UserError(_(
                    'The Total Dispatched Qty. Must be Equal the Requested Ticket Load Qty. Please Check your Compartment Qty.'))

            res = self.do_transfer_load()

            # The Shipment Date Set after Validation
            self.shipment_date = fields.Datetime.now()

            # Send email to QC for
            if self.picking_type_id.is_send_quality_control_notification:
                self.transfer_to_quality_control()

            is_create_invoice = self.picking_type_id.is_create_invoice
            if is_create_invoice and not self.is_throughput_ticket and not self.is_internal_use_ticket:

                sale_order = self.sale_id
                picking_type_code = self.picking_type_code
                invoic_obj = self.invoice_id or False
                if picking_type_code == "incoming" and sale_order and invoic_obj:  # Create a Customer refund invoice
                    self.transfer_create_refund_invoice()  # return inwards

                is_delivery_invoicing_policy = False
                backorder = self.backorder_id

                for picking_line in self.pack_operation_ids:
                    if picking_line.product_id.invoice_policy == "delivery":
                        is_delivery_invoicing_policy = True  # if at least one picking line product invoicing policy is based on delivered quantity

                if backorder and not is_delivery_invoicing_policy:  # Don't create the invoice, if it is a backorder and the invoicing policy is based on ordered quantity
                    return res

                if picking_type_code == "outgoing" and sale_order:  # Create a Customer Invoice
                    self.transfer_create_invoice_loading_ticket()

                    ############################################################################################
                    ######   FOR PURCHASES VENDOR BILLS AND PURCHASE RETURNS

                is_received_purchase_method = False
                backorder = self.backorder_id

                for picking_line in self.pack_operation_ids:
                    if picking_line.product_id.purchase_method == "receive":
                        is_received_purchase_method = True

                if backorder and not is_received_purchase_method:  # Don't create the invoice, if it is a backorder and the purchase method is based on ordered quantity
                    return res

                purchase_order = self.purchase_id
                if picking_type_code == "incoming" and purchase_order and purchase_order.purchase_type != 'foreign_purchase' :  # Create a Vendor Bill
                    self.transfer_create_bill()


                # Create purchase refund bill to supplier
                prev_picking_obj = self.previous_picking_id
                if prev_picking_obj:
                    prev_purchase_order = prev_picking_obj.purchase_id or False
                    prev_invoice_id = prev_picking_obj.invoice_id or False
                    if picking_type_code == "outgoing" and prev_purchase_order and prev_invoice_id:  # Create a Return goods Invoice
                        self.transfer_create_refund_bill()
        else:
            res = super(StockPicking, self).do_transfer()

        return res



    @api.multi
    def button_bank_inspection_on_discharged_product(self):
        self.env.cr.execute("update stock_picking set state = 'bank_inspection_on_discharged_product' where id = %s" % (self.id))
        user_ids = []
        group_obj = self.env.ref('rog_modifications.group_receive_bank_inspection_on_discharged_product_email_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
            'Bank Inspection on Discharged Product for (%s), has been initiated by %s.') % (
            self.name, self.env.user.name),
               subject='Bank Inspection on Discharged Product Initiated',
                subtype='mail.mt_comment')
        self.env.user.notify_info('Responsible Persons Will Be Notified by Email')


    @api.multi
    def button_bank_monitoring_stock(self):
        self.env.cr.execute(
            "update stock_picking set state = 'bank_monitoring_stock' where id = %s" % (self.id))
        user_ids = []
        group_obj = self.env.ref('rog_modifications.group_receive_bank_monitoring_stock_email_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
            'Bank Monitoring of Stock for (%s), has been initiated by %s.') % (
            self.name, self.env.user.name),
               subject='Bank Monitoring of Stock Initiated',
                subtype='mail.mt_comment')
        self.env.user.notify_info('Responsible Persons Will Be Notified by Email')

    ullage_bdischarge_mt = fields.Float(string="Ullage b/4 DISCH(MT)")
    ullage_bdischarge_ltrs = fields.Float(string="Ullage b/4 DISCH(ltrs)")
    ullage_report_ltrs = fields.Float(string="Ullage Report (ltrs)")
    state = fields.Selection(selection_add=[
        ('bank_inspection_on_discharged_product', 'Bank Inspection on Discharged Product'),
        ('bank_monitoring_stock', 'Bank Monitoring of Stock')])
    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')