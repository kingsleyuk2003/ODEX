# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime,date, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError,ValidationError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
import  time
from openerp.tools import amount_to_text

#Fixing Table Lines
class FixingTable(models.Model):
    _name = 'fixing.table'

    @api.onchange('platt_price','premium_price')
    def _compute_line_price(self):
        for rec in self:
            rec.line_price = rec.platt_price + rec.premium_price

    @api.onchange('mt_qty','line_price')
    def _compute_line_amount(self):
        for rec in self:
            rec.line_amount = rec.mt_qty * rec.line_price

    @api.depends('ago_purchase_contract_id','pms_purchase_contract_id')
    def _compute_product(self):
        ago_product_id = self.env.user.company_id.ago_product_id
        pms_product_id = self.env.user.company_id.pms_product_id

        if not ago_product_id:
            raise UserError(_("Please set the AGO product for the Fixing Table on the Companies settings page"))

        if not pms_product_id:
            raise UserError(_("Please set the PMS product for the Fixing Table on the Companies settings page"))

        for rec in self:
            if rec.ago_purchase_contract_id:
                rec.product_id = ago_product_id
            elif rec.pms_purchase_contract_id:
                rec.product_id = pms_product_id


    def _compute_premium(self):
        for rec in self:
            if rec.ago_purchase_contract_id:
                rec.premium_price = rec.ago_purchase_contract_id.premium_freight_insurance_mt_ago
            elif rec.pms_purchase_contract_id:
                rec.premium_price = rec.pms_purchase_contract_id.premium_freight_insurance_mt_pms



    fixing_date = fields.Date(string='Fixing Date')
    product_id = fields.Many2one('product.product',string='Product',compute='_compute_product',store=True)
    mt_qty = fields.Float(string='MT Qty.', digits=dp.get_precision('Product Unit of Measure'))
    platt_price = fields.Float(string='Platt')
    premium_price = fields.Float(string='Premium',compute='_compute_premium')
    line_price = fields.Float(string='Price',compute='_compute_line_price')
    line_amount = fields.Float(string='Amount',compute='_compute_line_amount')
    pms_purchase_contract_id = fields.Many2one('purchase.contract', string='PMS Purchase Contract')
    ago_purchase_contract_id = fields.Many2one('purchase.contract',string='AGO Purchase Contract')
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('fixing.table'))

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner(self):
        for rec in self:
            if rec.partner_id.warehouse_id :
                rec.warehouse_id = rec.partner_id.warehouse_id
            else:
                company = self.env.user.company_id.id
                warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
                rec.warehouse_id = warehouse_ids

    is_station_sales = fields.Boolean(string='Is from Service Station Sales')
    is_shortage_order = fields.Boolean(string='Is Shortage Order')





class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    @api.onchange('price_unit')
    def _onchange_price(self):
        for line in self:
            if line.product_id.is_invert_sign :
                line.price_unit = -line.price_unit

    @api.model
    def create(self,vals):
        allow_group_obj_users = self.env.ref('aminata_modifications.group_price_unit_allow').users
        if not self.env.user in allow_group_obj_users and self.product_id.type == 'product' and vals.get('price_unit',False) :
            raise UserError(_('You are not allowed to edit the price unit field for stockable product'))

        return super(SaleOrderLine,self).create(vals)


    @api.multi
    def write(self,vals):
        allow_group_obj_users = self.env.ref('aminata_modifications.group_price_unit_allow').users
        if not self.env.user in allow_group_obj_users and self.product_id.type == 'product' and vals.get('price_unit',False) :
            raise UserError(_('You are not allowed to edit the price unit field for stockable product'))

        return super(SaleOrderLine,self).write(vals)

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product' and not self.order_partner_id.warehouse_id:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product_qty = self.env['product.uom']._compute_qty_obj(self.product_uom, self.product_uom_qty,
                                                                   self.product_id.uom_id)

            if float_compare(self.product_id.virtual_available, product_qty, precision_digits=precision) == -1:

                sale_stock_loc_ids = self.order_id.team_id.sale_stock_location_ids
                res = self.check_order_line_qty_location(sale_stock_loc_ids)
                if res:
                    qty_available = res[self.product_id.id][0]
                    order_line_qty = res[self.product_id.id][1]
                    stck_list = ""
                    for stock_location in sale_stock_loc_ids:
                        stck_list += stock_location.name + ", "
                    stck_list = stck_list.rstrip(', ')
                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message': _(
                            'You plan to sell %.2f %s of %s, but you only have %.2f %s available in the assigned stock location(s) (%s) \n The total stock on hand in the stock location(s) (%s) for %s is %.2f %s.') % \
                                   (order_line_qty, self.product_uom.name, self.product_id.name, qty_available,
                                    self.product_id.uom_id.name, stck_list, stck_list, self.product_id.name,
                                    qty_available, self.product_id.uom_id.name)
                    }

                    return {'warning': warning_mess}
        return {}


class PurchaseContract(models.Model):
    _name = "purchase.contract"
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    @api.multi
    def action_create_po_fixing(self,ago_qty,pms_qty):
        ago_product_id = self.env.user.company_id.ago_product_id
        pms_product_id = self.env.user.company_id.pms_product_id

        if not ago_product_id :
            raise UserError(_("Please set the AGO product for the Fixing Table on the Companies settings page"))

        if not pms_product_id :
            raise UserError(_("Please set the PMS product for the Fixing Table on the Companies settings page"))

        if self.purchase_order_ids.filtered(lambda po: po.state == 'draft') :
            raise UserError('Please confirm/delete all draft PO for this purchase contract, before creating a new one')

        # if ago_qty > self.balance_to_fix_ago :
        #     raise UserError(_('The AGO ordered qty (%s) is more than the Balance yet to be fixed (%s)') % (ago_qty,self.balance_to_fix_ago ))
        #
        # if pms_qty > self.balance_to_fix_pms :
        #     raise UserError(_('The PMS ordered qty (%s) is more than the Balance yet to be fixed (%s)') % (pms_qty,self.balance_to_fix_pms ))

        #AGO Fixing Calculation
        list_po_ago = []
        if ago_qty > 0 :
            target_fixing_lines_ago = []
            mt_ago_qty_cuml = 0
            fl_target = 0
            fl_index = 0
            qty_released_ago = self.qty_released_ago
            target_qty_released_ago = qty_released_ago + ago_qty
            for ago_fix_line in self.ago_fixing_table_ids :
                mt_ago_qty_cuml += ago_fix_line.mt_qty
                if mt_ago_qty_cuml > qty_released_ago :
                    if target_qty_released_ago > mt_ago_qty_cuml :
                        target_fixing_lines_ago.append(ago_fix_line)
                        if fl_index == 0:
                            fl_target = mt_ago_qty_cuml - ago_fix_line.mt_qty
                            fl_index += 1
                    else:
                        target_fixing_lines_ago.append(ago_fix_line)
                        break

            if target_qty_released_ago > mt_ago_qty_cuml :
                allowed_qty_order = target_qty_released_ago - mt_ago_qty_cuml
                raise UserError(_("You are ordering more AGO than required. Please add more fixing lines with qty >= %s or re-adjust the released qty") % (allowed_qty_order + ago_qty))

            #Remove this block code later after confirmation things are fine
            # rm_ago_qty = ago_qty
            # offset_target_count = 0
            # for tfl_ago in target_fixing_lines_ago :
            #     offset_target = qty_released_ago - fl_target
            #     if tfl_ago.mt_qty > offset_target and offset_target_count == 0:
            #         offset_target_count += 1
            #         offset_bal = tfl_ago.mt_qty - offset_target
            #         rm_ago_qty = ago_qty - offset_bal
            #         list_po_ago.append({offset_bal:tfl_ago.line_price})
            #         continue
            #
            #     if rm_ago_qty > tfl_ago.mt_qty:
            #         rm_ago_qty = rm_ago_qty - tfl_ago.mt_qty
            #         list_po_ago.append({tfl_ago.mt_qty: tfl_ago.line_price})
            #     else:
            #         list_po_ago.append({rm_ago_qty: tfl_ago.line_price})

            #Second part for the Fixing proper
            ago_qty_released = qty_released_ago
            for tfl_ago in target_fixing_lines_ago:
                if mt_ago_qty_cuml > ago_qty_released:  # if offset_target
                    offset_bal = mt_ago_qty_cuml - ago_qty_released  # what is left to be fixed for the specific fixing line
                    current_cuml_opening_qty = tfl_ago.mt_qty + fl_target
                    bal_current_fl = current_cuml_opening_qty - ago_qty_released
                    bal_current_fl = round(bal_current_fl, 2)
                    ago_qty = round(ago_qty, 2)
                    if ago_qty <= offset_bal and not fl_target:  # quanity is small to fix on a FL line
                        list_po_ago.append({ago_qty: tfl_ago.line_price})
                        break
                    elif ago_qty < bal_current_fl:
                        list_po_ago.append({ago_qty: tfl_ago.line_price})
                        break
                    elif ago_qty >= bal_current_fl:
                        list_po_ago.append({bal_current_fl: tfl_ago.line_price})
                        ago_qty = ago_qty - bal_current_fl
                        ago_qty_released = ago_qty_released + bal_current_fl
                        fl_target = fl_target + tfl_ago.mt_qty

            #PMS Fixing Lines
        #First Part for Getting the Specific Fixing Lines
        list_po_pms = []
        if pms_qty > 0:
            target_fixing_lines_pms = []
            mt_pms_qty_cuml = 0
            fl_target = 0
            fl_index = 0
            qty_released_pms = self.qty_released_pms
            target_qty_released_pms = qty_released_pms + pms_qty
            for pms_fix_line in self.pms_fixing_table_ids:
                mt_pms_qty_cuml += pms_fix_line.mt_qty
                if mt_pms_qty_cuml > qty_released_pms:
                    if target_qty_released_pms > mt_pms_qty_cuml:
                        target_fixing_lines_pms.append(pms_fix_line)
                        if fl_index == 0:
                            fl_target = mt_pms_qty_cuml - pms_fix_line.mt_qty
                            fl_index += 1
                    else:
                        target_fixing_lines_pms.append(pms_fix_line)
                        break

            if target_qty_released_pms > mt_pms_qty_cuml:
                allowed_qty_order = target_qty_released_pms - mt_pms_qty_cuml
                raise UserError(_(
                    "You are ordering more PMS than required. Please add more fixing lines with qty >= %s or re-adjust the released qty") % (allowed_qty_order + pms_qty))

            # Remove this block code later after confirmation things are fine
            # rm_pms_qty = pms_qty
            # offset_target_count = 0
            # for tfl_pms in target_fixing_lines_pms:
            #     offset_target = qty_released_pms - fl_target #The qty that has been fixed on the specific fixing line
            #     if tfl_pms.mt_qty > offset_target and offset_target_count == 0: #if offset_target
            #         offset_target_count += 1
            #         offset_bal = tfl_pms.mt_qty - offset_target #what is left to be fixed for the specific fixing line
            #         rm_pms_qty = pms_qty - offset_bal
            #         list_po_pms.append({offset_bal: tfl_pms.line_price})
            #         continue
            #
            #     if rm_pms_qty > tfl_pms.mt_qty:
            #         rm_pms_qty = rm_pms_qty - tfl_pms.mt_qty
            #         list_po_pms.append({tfl_pms.mt_qty: tfl_pms.line_price})
            #     else:
            #         list_po_pms.append({rm_pms_qty: tfl_pms.line_price})

            #Second Part for the mapping.
            pms_qty_released = qty_released_pms
            for tfl_pms in target_fixing_lines_pms:
                #The qty that has been fixed on the specific fixing line
                if mt_pms_qty_cuml > pms_qty_released : #if offset_target
                    offset_bal = mt_pms_qty_cuml - pms_qty_released #what is left to be fixed for the specific fixing line
                    current_cuml_opening_qty = tfl_pms.mt_qty + fl_target
                    bal_current_fl = current_cuml_opening_qty - pms_qty_released
                    bal_current_fl = round(bal_current_fl,2)
                    pms_qty = round(pms_qty,2)
                    if pms_qty <= offset_bal and not fl_target: # quanity is small to fix on a FL line
                        list_po_pms.append({pms_qty: tfl_pms.line_price})
                        break
                    elif pms_qty < bal_current_fl:
                        list_po_pms.append({pms_qty: tfl_pms.line_price})
                        break
                    elif pms_qty >= bal_current_fl:
                        list_po_pms.append({bal_current_fl: tfl_pms.line_price})
                        pms_qty = pms_qty - bal_current_fl
                        pms_qty_released = pms_qty_released + bal_current_fl
                        fl_target = fl_target + tfl_pms.mt_qty




        # Create the PO
        po_obj = self.env['purchase.order']
        partner_id = self.partner_id
        if not partner_id:
            raise UserError(_("No Vendor set for this Purchase Contract"))

        po_vals = {
            'purchase_contract_id': self.id,
            'partner_id': partner_id.id,
            'user_id': self.env.user.id,
        }

        po = False
        if len(list_po_ago) > 0 or len(list_po_pms) > 0:
            po = po_obj.create(po_vals)

        for lp in list_po_ago:
            po_line = {
                'price_unit': lp.values()[0],
                'product_qty': lp.keys()[0],
                'product_uom': ago_product_id.uom_po_id.id,
                'product_id': ago_product_id.id or False,
                'order_id': po.id,
                'date_planned': datetime.today(),
            }
            self.env['purchase.order.line'].create(po_line)

        for lp in list_po_pms:
            po_line = {
                'price_unit': lp.values()[0],
                'product_qty': lp.keys()[0],
                'product_uom': pms_product_id.uom_po_id.id,
                'product_id': pms_product_id.id or False,
                'order_id': po.id,
                'date_planned': datetime.today(),
            }
            self.env['purchase.order.line'].create(po_line)

        return


    @api.multi
    def action_create_po(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('purchase.purchase_form_action')
        form_view_id = model_data_obj.xmlid_to_res_id('purchase.purchase_order_form')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'domain': action.domain,
            'context': {'search_default_todo':1,'show_purchase':True,'default_partner_id':self.partner_id.id,'default_purchase_contract_id':self.id},
            'res_model': action.res_model,
            'target': 'new'
        }


    # @api.model
    # def create(self, vals):
    #     vals['name'] = self.env['ir.sequence'].next_by_code('pcontract_code') or 'New'
    #     return super(PurchaseContract, self).create(vals)

    @api.multi
    def btn_view_purchase_order(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Purchase Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.purchase_order_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    @api.depends('purchase_order_ids')
    def _compute_qty_released_ago(self):
        for rec in self:
            total = 0
            total_price = 0
            for po in rec.purchase_order_ids:
                if po.state == 'purchase':
                    for pl in po.order_line:
                        if pl.product_id.white_product == 'ago':
                            total += pl.product_qty
                            total_price += pl.price_subtotal
            rec.qty_released_ago = total
            rec.total_amount_ago = total_price


    @api.depends('qty_released_ago')
    def _compute_qty_bal_ago(self):
        for rec in self:
            rec.qty_bal_ago = rec.qty_contract_ago - rec.qty_released_ago

    @api.depends('purchase_order_ids')
    def _compute_qty_released_pms(self):
        for rec in self:
            total = 0
            total_price = 0
            for po in rec.purchase_order_ids:
                if po.state == 'purchase':
                    for pl in po.order_line:
                        if pl.product_id.white_product == 'pms':
                            total += pl.product_qty
                            total_price += pl.price_subtotal
            rec.qty_released_pms = total
            rec.total_amount_pms = total_price


    @api.depends('qty_released_pms')
    def _compute_qty_bal_pms(self):
        for rec in self:
            rec.qty_bal_pms = rec.qty_contract_pms - rec.qty_released_pms

    @api.depends('ago_fixing_table_ids')
    def _compute_fix_ago(self):
        for rec in self:
            sum_ago_fix = 0
            sum_ago_amt_fix = 0
            total_line_price = 0
            for aft in rec.ago_fixing_table_ids:
                sum_ago_fix += aft.mt_qty
                sum_ago_amt_fix += aft.line_amount
                total_line_price += aft.line_price
            rec.total_fixed_ago = sum_ago_fix
            rec.balance_to_fix_ago = rec.qty_contract_ago - sum_ago_fix
            rec.amount_fixed_ago = sum_ago_amt_fix
            if len(rec.ago_fixing_table_ids) == 0:
                rec.average_price_ago = total_line_price
            else:
                rec.average_price_ago = total_line_price / len(rec.ago_fixing_table_ids)


    @api.depends('pms_fixing_table_ids')
    def _compute_fix_pms(self):
        for rec in self:
            sum_pms_fix = 0
            sum_pms_amt_fix = 0
            total_line_price = 0
            for pft in rec.pms_fixing_table_ids:
                sum_pms_fix += pft.mt_qty
                sum_pms_amt_fix += pft.line_amount
                total_line_price += pft.line_price
            rec.total_fixed_pms = sum_pms_fix
            rec.balance_to_fix_pms = rec.qty_contract_pms - sum_pms_fix
            rec.amount_fixed_pms = sum_pms_amt_fix
            if len(rec.pms_fixing_table_ids) == 0:
                rec.average_price_pms = total_line_price
            else:
                rec.average_price_pms = total_line_price / len(rec.pms_fixing_table_ids)


    name = fields.Char(string='Name',track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True,track_visibility='always')
    date_contract = fields.Date(string='Contract Date')
    date_expiry = fields.Date(string='Expiry Date')
    interest_charge = fields.Float(string='Interest Charge (%)')
    premium_freight_insurance_mt_ago = fields.Float(string='PFI/MT AGO (USD)', digits=dp.get_precision('Product Unit of Measure'), default=0.0)
    premium_freight_insurance_mt_pms = fields.Float(string='PFI/MT PMS (USD)', digits=dp.get_precision('Product Unit of Measure'),
                                                default=0.0)
    qty_contract_ago = fields.Float('AGO Bill of laden Qty. (MT)', digits=dp.get_precision('Product Unit of Measure'),track_visibility='onchange')
    qty_released_ago = fields.Float('AGO Qty. Stock Released (MT)' ,digits=dp.get_precision('Product Unit of Measure'),track_visibility='onchange',compute="_compute_qty_released_ago",store=True)
    qty_bal_ago = fields.Float('AGO Qty. Remaining Balance (MT)', digits=dp.get_precision('Product Unit of Measure'), track_visibility='onchange', compute="_compute_qty_bal_ago",store=True)
    total_fixed_ago = fields.Float('AGO Total Fixed (MT)', track_visibility='onchange', compute="_compute_fix_ago",store=True)
    balance_to_fix_ago = fields.Float('AGO Balance to be Fixed (MT)', track_visibility='onchange',
                                    compute="_compute_fix_ago",store=True)
    amount_fixed_ago = fields.Float('AGO Amount Fixed (USD)', track_visibility='onchange', compute="_compute_fix_ago",store=True)
    total_amount_ago = fields.Float('AGO Total Amount (USD)', track_visibility='onchange',
                                    compute="_compute_qty_released_ago",store=True)
    average_price_ago = fields.Float('AGO Average Price', track_visibility='onchange', compute="_compute_fix_ago",store=True)
    qty_contract_pms = fields.Float('PMS Bill of laden Qty. (MT)', digits=dp.get_precision('Product Unit of Measure'), track_visibility='onchange')
    qty_released_pms = fields.Float('PMS Qty. Stock Released (MT)', digits=dp.get_precision('Product Unit of Measure'), track_visibility='onchange', compute="_compute_qty_released_pms",store=True)
    qty_bal_pms = fields.Float('PMS Qty. Remaining Balance (MT)', digits=dp.get_precision('Product Unit of Measure'),track_visibility='onchange', compute="_compute_qty_bal_pms",store=True)
    total_amount_pms = fields.Float('PMS Total Amount (USD)', track_visibility='onchange',compute="_compute_qty_released_pms",store=True)
    total_fixed_pms = fields.Float('PMS Total Fixed (MT)', track_visibility='onchange', compute="_compute_fix_pms",store=True)
    balance_to_fix_pms = fields.Float('PMS Balance to be Fixed (MT)', track_visibility='onchange',
                                    compute="_compute_fix_pms",store=True)
    average_price_pms = fields.Float('PMS Average Price', track_visibility='onchange', compute="_compute_fix_pms",store=True)
    amount_fixed_pms = fields.Float('PMS Amount Fixed (USD)', track_visibility='onchange', compute="_compute_fix_pms",store=True)
    purchase_order_count = fields.Integer(compute="_compute_purchase_order_count", string='# of Purchase Orders', copy=False,default=0)
    purchase_order_ids = fields.One2many('purchase.order', 'purchase_contract_id', string='Purchase Order Entry(s)')
    # state = fields.Selection( [('draft', 'Draft'), ('validate', 'Done'), ('cancel', 'Cancel')],  default='draft', track_visibility='onchange')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True,
                              ondelete='restrict')
    pms_purchase_order_line_ids = fields.One2many('purchase.order.line', 'pms_purchase_contract_id', string='PMS Purchase Order Line(s)')
    ago_purchase_order_line_ids = fields.One2many('purchase.order.line', 'ago_purchase_contract_id', string='AGO Purchase Order Line(s)')

    pms_fixing_table_ids = fields.One2many('fixing.table','pms_purchase_contract_id',string='PMS Fixing Table')
    ago_fixing_table_ids = fields.One2many('fixing.table', 'ago_purchase_contract_id', string='AGO Fixing Table')
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('purchase.contract'))

class PurchaseOrderLineExtend(models.Model):
    _inherit = 'purchase.order.line'

    pms_purchase_contract_id = fields.Many2one('purchase.contract', string='PMS Purchase Contract')
    ago_purchase_contract_id = fields.Many2one('purchase.contract',  string='AGO Purchase Contract')
    conv_rate = fields.Float(related='product_uom.factor_inv',string='Conv. Rate')


class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'

    purchase_contract_id = fields.Many2one('purchase.contract', string='Purchase Contract')

    @api.multi
    def _create_picking(self):
        if self.purchase_contract_id :
            for order in self:
                if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):

                    for line in order.order_line :
                        res = order._prepare_picking()
                        res.update({'vend_ref': order.partner_ref})
                        picking = self.env['stock.picking'].create(res)
                        move = line.filtered(lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
                        move_ids = move.action_confirm()
                        move = self.env['stock.move'].browse(move_ids)
                        move.force_assign()
        else:
            return super(PurchaseOrderExtend,self)._create_picking()
        return True



    @api.multi
    def button_cancel(self):
        res = super(PurchaseOrderExtend, self).button_cancel()
        if self.purchase_contract_id:
            self.purchase_contract_id._compute_qty_released_pms()
            self.purchase_contract_id._compute_qty_released_ago()

            for po_line in self.order_line:
                if po_line.product_id.white_product == 'pms':
                    po_line.env.cr.execute(
                        "update purchase_order_line set pms_purchase_contract_id = %s where id = %s" % ('NULL',po_line.id))
                if po_line.product_id.white_product == 'ago':
                    po_line.env.cr.execute(
                        "update purchase_order_line set ago_purchase_contract_id = %s where id = %s" % (
                            'NULL', po_line.id))
        return res

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrderExtend, self).button_confirm()
        if self.purchase_contract_id:
            self.purchase_contract_id._compute_qty_released_pms()
            self.purchase_contract_id._compute_qty_released_ago()
            for po_line in self.order_line:
                if po_line.product_id.white_product == 'pms':
                    po_line.env.cr.execute(
                        "update purchase_order_line set pms_purchase_contract_id = %s where id = %s" % (self.purchase_contract_id.id,po_line.id))
                if po_line.product_id.white_product == 'ago':
                    po_line.env.cr.execute(
                        "update purchase_order_line set ago_purchase_contract_id = %s where id = %s" % (
                            self.purchase_contract_id.id, po_line.id))
        return res

    @api.multi
    def button_draft(self):
        res = super(PurchaseOrderExtend, self).button_draft()
        if self.purchase_contract_id:
            self.purchase_contract_id._compute_qty_released_pms()
            self.purchase_contract_id._compute_qty_released_ago()
            for po_line in self.order_line:
                po_line.pms_purchase_contract_id = False
                po_line.ago_purchase_contract_id = False
                if po_line.product_id.white_product == 'pms':
                    po_line.env.cr.execute(
                        "update purchase_order_line set pms_purchase_contract_id = %s where id = %s" % ('NULL',po_line.id))
                if po_line.product_id.white_product == 'ago':
                    po_line.env.cr.execute(
                        "update purchase_order_line set ago_purchase_contract_id = %s where id = %s" % (
                            'NULL', po_line.id))
        return res


class ResPartnerAminata(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        customer_category = self.env['customer.category']
        cc_id = vals.get('customer_category_id', False)
        if cc_id :
            cc = customer_category.browse(cc_id)
            sequence_id = cc.sequence_id
            vals['ref'] = sequence_id.next_by_id()
            vals['property_account_receivable_id'] = cc.account_id
        rec = super(ResPartnerAminata, self).create(vals)
        return rec



    is_enforce_credit_limit_so = fields.Boolean(string='Activate Credit Limit',default=True)
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')
    is_aminata_retail_reserve = fields.Boolean(string='Is Aminata Retail Reserve')
    is_aminata_sons = fields.Boolean(string='Is Aminata and Sons')
    is_service_station = fields.Boolean(string='Is Service Station')
    internal_location_id = fields.Many2one('stock.location', string='Internal Location')
    is_service_station_mgr = fields.Boolean(string='Is Service Station Manager')
    station_mgr_location_id = fields.Many2one('stock.location', string='Retail Station Location')
    customer_category_id = fields.Many2one('customer.category', string='Customer Category')


class DeliveryRegisterExtend(models.Model):
    _inherit = 'kin.delivery.register'

    is_duty_free = fields.Boolean(string='Duty Free')



class ProductTemplateAminataExtend(models.Model):
    _inherit = 'product.template'


    @api.multi
    def write(self,vals):
        allow_group_obj_users = self.env.ref('aminata_modifications.group_price_unit_allow').users
        if not self.env.user in allow_group_obj_users and self.type == 'product' and vals.get('list_price', False):
            raise UserError(_('You are not allowed to edit the sales price field for the stockable product'))
        elif not self.env.user in allow_group_obj_users and self.type == 'product' and vals.get('sales_price_transport_charge',False):
            raise UserError(_('You are not allowed to edit the sales price transport charge field for the stockable product'))

        return  super(ProductTemplateAminataExtend, self).write(vals)

    is_invert_sign = fields.Boolean('Invert the Sign', help='Reverse the sign of this product/service when selected on the sales order lines')
    station_sales_price_ids = fields.One2many('station.sales.price','product_id',string='Station Sales Price')



class StockPickingAminata(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def do_new_transfer(self):
        if self.pack_operation_product_ids[0].qty_done != self.pack_operation_product_ids[0].product_qty  and self.company_id.id == 3 :
            raise UserError(_('Sorry, The To Do Qty must be the same as the Done Qty'))
        res = super(StockPickingAminata,self).do_new_transfer()
        return res

    @api.model
    def run_check_unreserve_stock_aminata(self):
        target_recs = self.search([('state','in',['confirmed','partially_available','assigned']), ('picking_type_code','=','outgoing')])
        for target_rec in target_recs:
            target_rec.do_unreserve()
        return True

    @api.multi
    def amount_to_text(self, amt, currency=False):
        amount_text = amount_to_text(amt).replace('euro', '').replace('Cent', '')
        return str.upper( amount_text + ' ')


    ref_do = fields.Char(string='Reference. DO #')
    ref_tlo = fields.Char(string='Reference TLO #')
    attn = fields.Text(string='Attn',related='company_id.attn')
    transfer_no = fields.Char(string='Transfer Serial Number')
    lprc_manager_name = fields.Char(string='LPRC Manager',related='company_id.lprc_manager_name')
    lprc_manager_designation = fields.Char(string="LPRC Managers' Designation",related='company_id.lprc_manager_designation')
    transfer_date = fields.Date('Date',default=fields.Datetime.now)
    distributor_id = fields.Many2one('res.partner',string='Distributor',related='company_id.distributor_id')
    document_copy_type = fields.Char(string='Document Copy Type', default='Original Copy')
    cc_internal_transfer = fields.Text(string='CC Internal transfer',related='company_id.cc_internal_transfer')
    document_copy_type = fields.Char(string='Document Copy Type', related='company_id.document_copy_type')
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('stock.picking'))
    driver_name = fields.Char(string="Driver's Name")
    internal_picking_id = fields.Many2one('', string="Internal Stock Picking", track_visibility='onchange', readonly=True)
    station_product_dist_id = fields.Many2one('station.product.distribution', string="Station Product Distribution", track_visibility='onchange', readonly=True)
    station_dist_id = fields.Many2one('station.distribution', string="Station Distribution", track_visibility='onchange', readonly=True)
    station_sales_id = fields.Many2one('station.sales', string="Station Sales", track_visibility='onchange', readonly=True)
    is_station_sales = fields.Boolean(string='Is from Service Station Sales')

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        if self.type == 'out_invoice' and self.partner_id.is_enforce_credit_limit_so and self.partner_id.is_credit_limit_changed :
            raise UserError(_('Please contact the respective persons to approve the credit limit changes for this customer, before you may proceed with the invoice validation'))
        # if self.type == 'out_invoice' and self.partner_id.is_enforce_credit_limit_so and self.amount_total > (self.amount_total - self.partner_id.credit + self.partner_id.credit_limit)  :
        #     raise UserError(_('The Total amount %s of this invoice has exceeded the Credit of %s plus Credit Limit of %s. i.e %s > %s '  % (self.amount_total,self.amount_total - self.partner_id.credit,self.partner_id.credit_limit,self.amount_total,self.amount_total - self.partner_id.credit + self.partner_id.credit_limit)))
        res = []
        #source: ../addons/account/models/account_invoice.py:829
        for invoice in self:
            #refuse to validate a vendor bill/refund if there already exists one with the same reference for the same partner,
            #because it's probably a double encoding of the same bill/refund
            if invoice.type in ('in_invoice', 'in_refund') and invoice.reference :
                if self.search([('type', '=', invoice.type), ('reference', '=', invoice.reference), ('company_id', '=', invoice.company_id.id), ('commercial_partner_id', '=', invoice.commercial_partner_id.id), ('id', '!=', invoice.id)]):
                    raise UserError(_("Duplicated vendor reference detected. You probably encoded twice the same vendor bill/refund for Aminata"))
        res = self.write({'state': 'open'})


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


    @api.constrains('date_invoice')
    def check_date(self):
        for rec in self:
            set_date = rec.date_invoice
            restrict_users = self.env.ref('aminata_modifications.group_restrict_transaction_by_date').users
            if self.env.user in restrict_users:
                dayback = self.env.user.company_id.restrict_days
                selected_date = datetime.strptime(set_date, "%Y-%m-%d")
                allowed_date = datetime.strptime(str(date.today()), "%Y-%m-%d") - timedelta(days=+dayback)
                if selected_date < allowed_date:
                    raise ValidationError('Backdating is not allowed, before %s ' % (datetime.strftime(allowed_date,'%d-%m-%Y')))

                today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
                if selected_date > today_date :
                    raise ValidationError('Date forwarding is not allowed, after %s ' % (datetime.strftime(today_date,'%d-%m-%Y')))


    ref_do = fields.Char(string='Reference. DO #')
    ref_tlo = fields.Char(string='Reference TLO #')
    note = fields.Char(string='Note')
    delivery_location_id = fields.Many2one('kin.product.location', string='Delivery Location')
    station_sales_id = fields.Many2one('station.sales', string='Station Sales')
    is_station_sales = fields.Boolean(string='Is from Service Station Sales')

class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'


    # def _onchange_product_id(self):
    #     # self.name = ''
    #     res = super(AccountInvoiceLine,self)._onchange_product_id()
    #
    #     return res


class ProductLifting(models.Model):
    _inherit = 'product.lifting'

    def create_retail_station_po(self,price_unit,product_qty,product_uom,product_id,origin):
        # Create the PO
        po_obj = self.env['purchase.order']
        partner_id = self.env['res.partner'].search([('is_aminata_sons','=',True)])
        company_id = self.env['res.company'].browse(3)
        if not partner_id:
            raise UserError(_("No Vendor set for this the Service Station Purchase Order"))

        po_vals = {
            'partner_id': partner_id.id,
            'partner_ref': origin,
            'company_id': company_id.id,
            'picking_type_id' : 24
           # 'user_id': self.env.user.id,
        }

        po = po_obj.create(po_vals)
        po_line = {
                'price_unit': price_unit,
                'product_qty': product_qty,
                'product_uom': product_uom,
                'product_id': product_id,
                'order_id': po.id,
                'date_planned': datetime.today(),
            }
        self.env['purchase.order.line'].create(po_line)
        po.button_approve()
        po.invoice_ids[0].journal_id = 62
        po.invoice_ids[0].account_id = 2523
        po.invoice_ids[0].reference = self.name
        po.invoice_ids[0].invoice_line_ids[0].account_id = 2513
        po.invoice_ids[0].signal_workflow('invoice_open')

        for picking_id in po.picking_ids:
            picking_id.action_confirm()
            picking_id.action_assign()
            if picking_id.state != 'assigned':
                raise UserError(_('Sorry, Stock qty is not enough for the delivery order operation'))
            picking_id.do_prepare_partial()
            picking_id.pack_operation_product_ids[0].qty_done = picking_id.pack_operation_product_ids[0].product_qty
            picking_id.do_new_transfer()
        return po


    # def create_retail_station_order(self,product_qty,product_id):
    #
    #     so_obj = self.env['station.order']
    #     company_id = self.env['res.company'].browse(3)
    #
    #     so_vals = {
    #         'product_id': product_id,
    #         'product_qty': product_qty,
    #         'company_id' : company_id.id,
    #         'ref_do' : self.picking_id.ref_do,
    #         'ref_tlo' : self.picking_id.ref_tlo
    #     }
    #     so = so_obj.create(so_vals)
    #     return so

    def send_email(self, grp_name, msg):
        # send email
        partn_ids = []
        group_obj = self.env.ref(grp_name)
        user_names = ''
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=partn_ids)

        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return


    def create_customer_invoice(self):
        inv = super(ProductLifting,self).create_customer_invoice()
        inv.ref_do = self.picking_id.ref_do
        inv.ref_tlo = self.picking_id.ref_tlo

        #create retail po if it is aminata retail reserve company
        if self.partner_id.is_aminata_retail_reserve :
            product_qty = self.delivered_qty
            product_uom = self.product_uom.id
            product_id = self.product_id.id

            orderline = self.picking_id.sale_id.order_line.filtered(lambda line: line.product_id == self.product_id)
            if not orderline:
                raise UserError(_('No Sales Order Line for this Product: %s' % (self.product_id.name)))

            # price_unit = total_price_unit / len(move_ids)
            po = self.sudo().create_retail_station_po(orderline.price_unit, product_qty, product_uom, product_id,
                                                      orderline.order_id.name)
            self.po_id = po

            # send email to the Retail Head
            group_name = 'aminata_modifications.group_receive_email_retail_warehouse_receipt'
            msg = 'FYI, Goods have been Transferred from Aminata Warehouse to Retail Warehouse, being Initiated by %s for I.D.O  %s' % (
                self.user_id.name, self.picking_id.name)
            self.send_email(group_name, msg)

        return inv


    def create_shortage_invoice(self, rate=0, qty=0, inv_type='out_invoice'):
        inv = super(ProductLifting,self).create_shortage_invoice(rate=rate, qty=qty, inv_type=inv_type)
        inv.ref_do = self.picking_id.ref_do
        inv.ref_tlo = self.picking_id.ref_tlo
        return inv

    def create_trucker_bill(self, rate=0, qty=0, inv_type='out_invoice'):
        inv = super(ProductLifting, self).create_trucker_bill(rate=rate, qty=qty, inv_type=inv_type)
        inv.ref_do = self.picking_id.ref_do
        inv.ref_tlo = self.picking_id.ref_tlo
        return inv

    @api.multi
    def action_mark_transit(self):
        res = super(ProductLifting, self).action_mark_transit()

        # create the product received register if the company is a retail station
        if self.env.user.company_id.is_enable_product_received_register_ido and self.partner_id and self.partner_id.is_company_station and self.partner_id.retail_station_id:
            # create the product received register
            prr = self.env['product.received.register']
            vals = {
                'product_id': self.product_id.id,
                'quantity_loaded': self.ordered_qty,
                'from_stock_location_id': self.picking_id.location_dest_id.id,
                'to_stock_location_id': self.partner_id.retail_station_id.id,
                'is_company_product': True,
                'waybill_no': self.picking_id.name,
                'ticket_ref': self.ido_number,
                'loading_ticket_id': self.picking_id.id,
                'state': 'transit',
                'truck_no': self.truck_id.name,
                'loading_date': self.lift_date,
                'receiving_date': self.lift_date,
            }
            prr_obj = prr.create(vals)
            self.prr_id = prr_obj

            # Notify the Retail Manager
            retail_station = self.partner_id  # the retail station
            retail_manager = retail_station.retail_station_id and retail_station.retail_station_id.retail_station_manager_id or False

            if not retail_manager:
                raise UserError(_(
                    'Please contact your admin, to create a retail manager and attach to the retail station. Then the retail station should be linked to the respective partner'))

            prr_obj.user_id = retail_manager

            if retail_manager.email:
                user_ids = []
                user_ids.append(retail_manager.id)
                prr_obj.message_unsubscribe_users(user_ids=user_ids)
                prr_obj.message_subscribe_users(user_ids=user_ids)
                prr_obj.message_post(_(
                    'This is to notify you that some products will be coming into your retail station from %s, and a Product Received Register with ID (%s) has been Created.') % (
                                         self.from_product_location_id.name, prr_obj.name),
                                     subject='A Product Received register in transit has been Created ',
                                     subtype='mail.mt_comment')

        return res

    @api.multi
    def action_validate(self):
        res = super(ProductLifting, self).action_validate()
        # Create the stock location moves
        if self.env.user.company_id.is_enable_product_received_register_ido and self.partner_id and self.partner_id.is_company_station and self.partner_id.retail_station_id:
            stock_move_obj = self.env['stock.move']
            customer_location_id = self.partner_id.property_stock_customer or False

            if not customer_location_id:
                raise UserError(_('Please Contact the Admin to Create a Partner and Link it to the Retail Station'))

            vals = {
                'name': self.ido_number,
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'date': self.lift_date,
                'location_id': self.picking_id.location_dest_id.id,
                'location_dest_id': self.partner_id.property_stock_customer.id,
                'product_uom_qty': self.delivered_qty,
                'origin': self.picking_id.name
            }

            move_id = stock_move_obj.create(vals)
            move_id.action_confirm()
            move_id.force_assign()
            move_id.action_done()
            move_id.lift_id = self.id
            self.move_id = move_id

        return res

    @api.multi
    def action_cancel_reset(self):
        res = super(ProductLifting, self).action_cancel_reset()
        self.prr_id.unlink()
        self.po_id.unlink()
        self.so_id.unlink()

        # Reverse Stock moves because the system cannot allow cancellation of done stock moves
        # create the reverse stock move
        stock_move_obj = self.env['stock.move']
        stock_move = self.move_id
        if stock_move:
            vals = {
                'name': 'Reversal for: ' + stock_move.origin,
                'product_id': stock_move.product_id.id,
                'product_uom': stock_move.product_uom.id,
                'date': datetime.today(),
                'location_id': stock_move.location_dest_id.id,
                'location_dest_id': stock_move.location_id.id,
                'product_uom_qty': stock_move.product_uom_qty,
                'origin': stock_move.origin
            }
            move_id = stock_move_obj.create(vals)
            move_id.action_confirm()
            move_id.force_assign()
            move_id.action_done()

    prr_id = fields.Many2one('product.received.register', string='Product Received Register')
    move_id = fields.Many2one('stock.move', string='Stock Move')
    po_id = fields.Many2one('purchase.order', string='Purchase Order')
    so_id = fields.Many2one('station.distribution', string='Station Distribution')


class ResCompanyAminata(models.Model):
    _inherit = "res.company"

    attn = fields.Text(string='Attn')
    lprc_manager_name = fields.Char(string='LPRC Manager')
    lprc_manager_designation = fields.Char(string="LPRC Managers' Designation")
    distributor_id = fields.Many2one('res.partner',string='Distributor')
    cc_internal_transfer = fields.Text(string='CC Internal transfer')
    document_copy_type = fields.Char(string='Document Copy Type',default='Original Copy')
    is_enable_product_received_register_ido = fields.Boolean(
        string='Enable Creation of Product Received Record from I.D.O')
    ago_product_id = fields.Many2one('product.product',string='AGO Product for Purchase Fixing Table')
    pms_product_id = fields.Many2one('product.product', string='PMS Product for Purchase Fixing Table')
    restrict_days = fields.Integer(string='Restrict Transaction Day',default=1)
    overage_stock_location_id = fields.Many2one('stock.location',string='Overage Stock Location')

   # comment this line below before uploading on Aminata server. it is not necessary, but required by localhost
    #accountant_group_id = fields.Many2one('emp.expense.group', string='Accountant Group')

class HRExtend(models.Model):
    _inherit = 'hr.employee'

    bank_account_number_lrd = fields.Char(string='Bank Account Number (LRD)')
    bank_account_number_usd = fields.Char(string='Bank Account Number (USD)')


class HRPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    lrd_rate = fields.Float('LRD Rate')


class HRContract(models.Model):
    _inherit = 'hr.contract'

    lrd_rate = fields.Float(string='Uniform LRD Rate for all Salary Structure',related='struct_id.lrd_rate')
    hourly_rate = fields.Float(string='Hourly Rate')


class StockMove(models.Model):
    _inherit = 'stock.move'

    lift_id = fields.Many2one('product.lifting', string="Lifting Record", track_visibility='onchange',readonly=True)



class AccountMoveExtendAminata(models.Model):
    _inherit = 'account.move'

    @api.multi
    def button_first_approval(self):
        self.state = 'second_approval'

        user_ids = []
        group_obj = self.env.ref('aminata_modifications.group_acoms_second_approver')
        for user in group_obj.users:
            user_ids.append(user.id)

        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                'For your information, An ACOMS journal Entry needs your Second approval. Click the following link to see the Entry'),
                              subject='ACOMS Journal Entry requires Second Approval',
                              subtype='mail.mt_comment')


    @api.multi
    def button_second_approval(self):
        self.state = 'draft'


    state = fields.Selection(selection_add=[
        ('first_approval', 'Awaiting First Approval'),
        ('second_approval', 'Awaiting Second Approval')
    ])


class AccountMoveLineExtend(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _update_check(self):
        """ Raise Warning to cause rollback if the move is posted, some entries are reconciled or the move is older than the lock date"""
        move_ids = set()
        for line in self:
            err_msg = _('Move name (id): %s (%s)') % (line.move_id.name, str(line.move_id.id))
            # if line.move_id.state not in ('draft','first_approval','second_approval'):
            #     raise UserError(_('You cannot do this modification on a posted journal entry, you can just change some non legal fields. You must revert the journal entry to cancel it.\n%s.') % err_msg)
            # if line.reconciled and not (line.debit == 0 and line.credit == 0):
            #     raise UserError(_('You cannot do this modification on a reconciled entry. You can just change some non legal fields or you must unreconcile first.\n%s.') % err_msg)
            if line.move_id.id not in move_ids:
                move_ids.add(line.move_id.id)
            self.env['account.move'].browse(list(move_ids))._check_lock_date()
        return True


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.constrains('payment_date')
    def check_date(self):
        for rec in self:
            set_date = rec.payment_date
            restrict_users = self.env.ref('aminata_modifications.group_restrict_transaction_by_date').users
            if self.env.user in restrict_users:
                dayback = self.env.user.company_id.restrict_days
                selected_date = datetime.strptime(set_date, "%Y-%m-%d")
                allowed_date = datetime.strptime(str(date.today()), "%Y-%m-%d") - timedelta(days=+dayback)
                if selected_date < allowed_date:
                    raise ValidationError('Backdating is not allowed, before %s ' % (datetime.strftime(allowed_date,'%d-%m-%Y')))



    #Why this will not work for now: https://www.odoo.com/forum/help-1/question/why-sql-constraints-not-working-39549
    _sql_constraints = [
                ('ref_no_uniq', 'unique (ref_no)', "Reference No. already exists !"),
        ]

    @api.constrains('ref_no')
    def check_uniq_ref_no(self):
        for rec in self:
            ref_no = rec.ref_no
            if ref_no :
                is_present = self.search([('ref_no','=',ref_no)])
                if len(is_present) > 1 :
                    raise ValidationError(
                        'Reference No. %s Already used' % (ref_no))



class AccountPaymentGroupExtend(models.Model):
    _inherit = 'account.payment.group'

    @api.constrains('payment_date')
    def check_date(self):
        for rec in self:
            set_date = rec.payment_date
            restrict_users = self.env.ref('aminata_modifications.group_restrict_transaction_by_date').users
            if self.env.user in restrict_users:
                dayback = self.env.user.company_id.restrict_days
                selected_date = datetime.strptime(set_date, "%Y-%m-%d")
                allowed_date = datetime.strptime(str(date.today()), "%Y-%m-%d") - timedelta(days=+dayback)
                if selected_date < allowed_date:
                    raise ValidationError('Backdating is not allowed, before %s ' % (datetime.strftime(allowed_date,'%d-%m-%Y')))

                today_date = datetime.strptime(str(date.today()), "%Y-%m-%d")
                if selected_date > today_date :
                    raise ValidationError('Date forwarding is not allowed, after %s ' % (datetime.strftime(today_date,'%d-%m-%Y')))

    @api.constrains('payment_voucher_no')
    def check_uniq_payment_voucher_no(self):
        for rec in self:
            payment_voucher_no = rec.payment_voucher_no
            if payment_voucher_no:
                is_present = self.search([('payment_voucher_no','=',payment_voucher_no)])
                if len(is_present) > 1 :
                    raise ValidationError(
                        'Payment Voucher No. %s Already used' % (payment_voucher_no))


    @api.multi
    def post(self):
        if self.env.user == self.create_uid:
            raise UserError('Sorry, you can not post a payment created by you')
        return super(AccountPaymentGroupExtend,self).post()

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.constrains('name')
    def check_uniq_name(self):
        for rec in self:
            name = rec.name
            if name:
                is_present = self.search([('name', '=', name)])
                if len(is_present) > 1:
                    raise ValidationError(
                        'Cash/Bank Payment Ref. %s Already used' % (name))


class StationLiftingOrder(models.Model):
    _name = 'station.lifting.order'
    _inherit = ['mail.thread']
    _order = 'name desc'

    @api.multi
    def action_create_station_distribution(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('aminata_modifications.action_station_distribution_form')
        form_view_id = model_data_obj.xmlid_to_res_id('aminata_modifications.station_distribution_form_view')
        partns = [x.partner_id.id for x in self.lifting_order_line_ids]
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'domain': action.domain,
            'context': {'default_product_id': self.product_id.id , 'default_station_lifting_order_id': self.id,'default_lifting_order_partner_ids':partns},
            'res_model': action.res_model,
        }

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('station_lifting_order_code') or 'New'
        rec = super(StationLiftingOrder, self).create(vals)
        return rec

    # @api.multi
    # def action_done(self):
    #     lifted_qty_sum = 0
    #     for rec in self.station_product_dist_ids:
    #         lifted_qty_sum += rec.qty
    #     if self.product_qty > lifted_qty_sum :
    #         raise UserError('Sorry, You cannot complete the station order until all the products have been lifted')
    #     self.state == 'done'

    def do_checks(self):
        # Finding duplicated in a list
        l = []
        for order_line in self.lifting_order_line_ids:
            l.append(order_line.partner_id.id)
        if set([x for x in l if l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
            raise UserError(('Duplicate Service Station detected. Only One Service Station is allowed at a time for each Station Delivery Order'))

        # Check total qty
        if self.total_product_qty != sum(self.lifting_order_line_ids.mapped('requested_qty')):
            raise UserError(_(
                'Please The Total Product Qty to be Approved must be equal to the Sum of all Requested Qtys in the Lines below'))

    @api.multi
    def action_draft(self):
        self.state = 'draft'
        #send email to the initiator
        partn_ids = []
        user_name = self.user_id.name
        partn_ids.append(self.user_id.partner_id.id)

        if self.user_id.partner_id.email and partn_ids:
            msg = 'The Lifting Order %s has been Reset by %s. Please edit and re-submit' % (self.name,self.env.user.name)
            self.message_post(_(msg), subject='The Lifting Order %s has been Reset by %s' % (self.name,self.env.user.name), partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))


    @api.multi
    def action_confirm(self):
        self.do_checks()
        self.state = 'confirm'
        #send email to the approver
        group_name = 'aminata_modifications.group_receive_email_station_lifting_order_approver'
        msg = 'A Station Delivery Order (%s) has been Initiated and Submitted by %s' % (
            self.name, self.env.user.name)
        self.send_email(group_name, msg)

    @api.multi
    def action_approve(self):
        self.do_checks()
        self.state = 'approve'
        # Send email to the distributor
        group_name = 'aminata_modifications.group_receive_email_station_lifting_order_distribution'
        msg = 'A Station Lifting Order (%s) has been Approved by %s and is ready for Distribution' % (self.name, self.env.user.name)
        self.send_email(group_name, msg)

    def send_email(self, grp_name, msg):
        # send email
        partn_ids = []
        group_obj = self.env.ref(grp_name)
        user_names = ''
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(_(msg),subject='%s' % msg, partner_ids=partn_ids)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return


    @api.multi
    def btn_view_station_distribution(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Mother Delivery Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'station.distribution',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.station_distribution_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),

        }

    @api.depends('station_distribution_ids')
    def _compute_station_distr_count(self):
        for rec in self:
            rec.station_distr_count = len(rec.station_distribution_ids)

    @api.depends('product_id')
    def _get_pump_price(self):
        for rec in self:
            rec.current_pump_price = rec.product_id.sales_price_transport_charge


    name = fields.Char(string='Name')
    date = fields.Date(string='Date', default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    current_pump_price = fields.Float(string='Current Pump Price',compute=_get_pump_price,store=True)
    total_product_qty = fields.Float(string='Total Requested Qty.')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id,  ondelete='restrict', readonly=True)
    company_id = fields.Many2one('res.company', string='Company' ,default=lambda self: self.env['res.company']._company_default_get('station.lifting.order'))
    lifting_order_line_ids = fields.One2many('station.lifting.order.lines', 'station_lifting_order_id', string='Station Lifting Order Lines')
    station_distribution_ids = fields.One2many('station.distribution', 'station_lifting_order_id', string='Station Distributions')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),('approve', 'Approved')], default='draft', track_visibility='onchange')
    station_distr_count = fields.Integer(compute="_compute_station_distr_count", string='# of Station Distribution', copy=False, default=0)


class StationLiftingOrderLines(models.Model):
    _name = 'station.lifting.order.lines'

    # @api.one
    # @api.depends('station_lifting_order_id.station_distribution_ids.station_product_dist_ids.qty')
    # def _compute_lifting_qty(self):
    #     self.lifted_qty = sum(self.station_lifting_order_id.station_distribution_ids.station_product_dist_ids.filtered(lambda line: line.partner_id == self.partner_id and line.state != 'draft').mapped('qty'))

    @api.depends('requested_qty','lifted_qty')
    def _compute_balance_qty(self):
        for rec in self:
            rec.balance_qty = rec.requested_qty - rec.lifted_qty

    station_lifting_order_id = fields.Many2one('station.lifting.order', string='Station Delivery Order')
    partner_id = fields.Many2one('res.partner', string='Service Station')
    request_date = fields.Date(string='Date', related='station_lifting_order_id.date', store=True)
    product_id = fields.Many2one('product.product', related='station_lifting_order_id.product_id', store=True, string='Product', ondelete='restrict', track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    requested_qty = fields.Float(string='Requested Qty.', track_visibility='onchange')
    lifted_qty = fields.Float(string='Lifted Qty.')
    balance_qty = fields.Float(string='Balance Qty.',compute=_compute_balance_qty,store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('station.lifting.order.lines'))


#MOTHER D.O
class StationDistribution(models.Model):
    _name = 'station.distribution'
    _inherit = ['mail.thread']
    _order = 'name desc'

    @api.multi
    def action_print_mdo(self):
        return self.env['report'].get_action(self, 'aminata_modifications.report_mother_delivery_order_stations')


    @api.multi
    def amount_to_text(self, amt):
        amount_text = amount_to_text(amt).replace('euro', '').replace('Cent', '')
        return str.upper(amount_text + ' ')

    @api.multi
    def unlink(self):
        for rec in self:
            for spd in rec.station_product_dist_ids:
                if spd.state != 'draft':
                    raise UserError(_('Sorry, the Mother D.O cannot be deleted. Delete all I.D.Os below before attempting to delete the Mother D.O '))
        return super(StationDistribution, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('station_distr_code') or 'New'
        rec = super(StationDistribution, self).create(vals)
        return rec


    def create_shortage_sales_order(self):
        lines = []
        for rec in self:
            line = (0, 0, {
                'name': rec.product_id.name,
                'product_id': rec.product_id.id,
                'product_uom_qty': rec.total_shortage_qty,
                'product_uom': rec.product_uom.id,
                'price_unit': rec.sales_price,
            })
            lines.append(line)

        partner_id = self.partner_truck_id
        sale_order_id = self.env['sale.order'].create({
            'partner_id': partner_id.id,
            'partner_invoice_id': partner_id.id,
            'partner_shipping_id': partner_id.id,
            'pricelist_id': partner_id.property_product_pricelist.id,
            'client_order_ref': self.name,
            'order_line': lines,
            'is_shortage_order': True
        })
        return sale_order_id


    def create_shortage_invoice(self,order):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        company = self.env.user.company_id
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        partner_id = self.partner_truck_id
        if not partner_id:
            raise UserError(_("No Trucker Company Set for the Truck. Please check truck configuration page"))

        lines = []
        for sale_order_line_id in order.order_line:
            if not float_is_zero(1, precision_digits=precision):
                account = sale_order_line_id.product_id.property_account_income_id or sale_order_line_id.product_id.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(
                        _('Please define income account for the product: "%s" (id:%d) - or for its category: "%s".') % (
                            sale_order_line_id.product_id.name, sale_order_line_id.product_id.id,
                            sale_order_line_id.product_id.categ_id.name))


                default_analytic_account = order.env['account.analytic.default'].account_get(partner_id=partner_id.id)

                line = (0, 0, {
                    'name': 'Shortage invoice for %s for %s at rate of %s' % (partner_id.name, sale_order_line_id.product_uom_qty, sale_order_line_id.price_unit),
                    'sequence': sale_order_line_id.sequence,
                    'origin': sale_order_line_id.order_id.name,
                    'account_id': account.id,
                    'price_unit': sale_order_line_id.price_unit,
                    'quantity': sale_order_line_id.product_uom_qty,
                    'discount': sale_order_line_id.discount,
                    'product_id': sale_order_line_id.product_id.id,
                    'uom_id': sale_order_line_id.product_uom.id,
                    'invoice_line_tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
                    'account_analytic_id': sale_order_line_id.order_id.project_id.id or default_analytic_account and default_analytic_account.analytic_id.id,
                   # 'invoice_id': invoice.id,
                    'sale_line_ids': [(6, 0, [sale_order_line_id.id])]

                })
                lines.append(line)

        invoice_vals = {
            'origin': self.name,
            'type': 'out_invoice',
            'reference': self.name,
            'account_id': partner_id.property_account_receivable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id,
            'is_shortage_invoice': True,
            'is_from_inventory' : True,
            'invoice_line_ids': lines ,
            'user_id': self.env.user.id
        }
        invoice = inv_obj.create(invoice_vals)
        # self.env['account.invoice.line'].create(inv_line)

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
        group_obj = self.env.ref('aminata_modifications.group_station_accountant_aminata')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New Station Shortage Invoice has been created from %s by %s') % (
                                     self.name,  self.env.user.name),
                                 subject='A New Station Shortage Invoice has been created', subtype='mail.mt_comment')
        return invoice


    def action_done(self):
        total_lifted_qty = 0
        any_not_done = False
        for rec in self.station_product_dist_ids:
            if rec.state != 'validate':
                any_not_done = True
            total_lifted_qty += rec.qty
        if any_not_done :
            raise UserError('Sorry, You cannot mark this Mother D.O as done without validating the I.D.Os below')
        if total_lifted_qty != self.product_qty:
            raise UserError('Sorry, The Truck Lifted Qty. for the Mother D.O, must be equal to the Total sum of all I.D.Os lifted Qty.')

        if self.total_shortage_qty > 0:
            self.is_shortage = True
            if self.sales_price <= 0 :
                raise UserError('Please set the Pump price for this station on the product page')

            # create shortage sales order
            order = self.create_shortage_sales_order()
            order.approve_credit_limit_bypass()
            self.order_shortage_id = order

            for pick_id in order.picking_ids:
                pick_id.action_assign()
                if pick_id.state != 'assigned':
                    raise UserError(_('Sorry, Stock qty is not enough for the shortage operation'))
                pick_id.do_prepare_partial()
                pick_id.pack_operation_product_ids[0].qty_done = pick_id.pack_operation_product_ids[0].product_qty
                pick_id.do_new_transfer()
                pick_id.station_dist_id = self.id

            # Create shortage sales invoice and validate
            invoice = self.create_shortage_invoice(order)
            self.shortage_invoice_id = invoice
            invoice.signal_workflow('invoice_open')

        self.state = 'done'



    @api.depends('station_product_dist_ids.qty')
    def _compute_total_lifted_qty(self):
        for rec in self.station_product_dist_ids:
            self.total_lifted_qty += rec.qty

    @api.depends('station_product_dist_ids.delivered_qty')
    def _compute_total_delivered_qty(self):
        for rec in self.station_product_dist_ids:
            self.total_delivered_qty += rec.delivered_qty

    @api.depends('total_lifted_qty','total_delivered_qty')
    def _compute_total_shortage_qty(self):
        for rec in self:
            rec.total_shortage_qty = rec.total_lifted_qty - rec.total_delivered_qty

    @api.multi
    def btn_view_stock_pick(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Picking'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_pick_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_pick_ids')
    def _compute_stock_pick_count(self):
        for rec in self:
            rec.stock_pick_count = len(rec.stock_pick_ids)




    name = fields.Char(string='Name')
    date = fields.Date(string='Date', default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    product_qty = fields.Float(string='Truck Lifted Qty.')
    trucker_id = fields.Many2one('kin.trucker',string='Trucker')
    driver_name = fields.Char(string="Driver's Name")
    partner_truck_id = fields.Many2one('res.partner', related='trucker_id.partner_id', string="Trucker's Owner",store=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id,  ondelete='restrict', readonly=True)
    company_id = fields.Many2one('res.company', string='Company' ,default=lambda self: self.env['res.company']._company_default_get('station.distribution'))
    station_product_dist_ids = fields.One2many('station.product.distribution','station_distribution_id', string='Station Product Distributions')
    state = fields.Selection([('progress', 'In Progress'), ('done', 'Done'),], default='progress', track_visibility='onchange')

    total_lifted_qty = fields.Float(string='Total Lifted Qty',compute=_compute_total_lifted_qty,store=True)
    total_delivered_qty = fields.Float(string='Total Delivered Qty',compute=_compute_total_delivered_qty,store=True)
    total_shortage_qty = fields.Float(string='Total Shortage Qty',compute=_compute_total_shortage_qty,store=True)

    shortage_invoice_id = fields.Many2one('account.invoice', string='Shortage Invoice')
    is_shortage = fields.Boolean('Is Shortage')
    order_shortage_id = fields.Many2one('sale.order', string='Shortage Sales Order')
    stock_pick_count = fields.Integer(compute="_compute_stock_pick_count", string='# of Stock Picking', copy=False,default=0)
    stock_pick_ids = fields.One2many('stock.picking', 'station_dist_id', string='Stock Picking Entry(s)')
    is_duty_free = fields.Boolean('Is Duty Free')
    sales_price = fields.Float('Pump price', related='station_lifting_order_id.current_pump_price',store=True)
    station_lifting_order_id = fields.Many2one('station.lifting.order', ondelete='restrict', string='Station Lifting Order')
    lifting_order_partner_ids = fields.Many2many('res.partner', string='Lifting Order Service Stations')

# I.D.O
class StationProductDistribution(models.Model):
    _name = 'station.product.distribution'
    _inherit = ['mail.thread']
    _order = 'date_move desc'


    @api.multi
    def amount_to_text(self, amt):
        amount_text = amount_to_text(amt).replace('euro', '').replace('Cent', '')
        return str.upper(amount_text + ' ')


    def create_trucker_bill(self,rate=0,qty=0,inv_type='in_invoice'):
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

        partner_id = self.station_distribution_id.trucker_id.partner_id
        if not partner_id :
            raise UserError(_("No Trucker Person Set"))

        invoice_vals = {
            'origin': self.name,
            'type': inv_type,
            'reference':self.name,
            'account_id': partner_id.property_account_payable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id.id,
            'is_delivery_invoice': True,
          #  'product_allocation_trucker_bill_id': self.picking_id.id,
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


            inv_line = {
                'name': 'Trucker Bill for %s (%s), for qty of %s at rate of %s' % (partner_id.name,self.station_distribution_id.trucker_id.name,qty,rate),
                'origin': self.name,
                'account_id': 2994,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': company.product_id.uom_id.id,
                'product_id': company.product_id.id or False,
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
                'A New Station Trucker Invoice has been created from  %s by %s') % (
                                   self.name,self.env.user.name),
                              subject='A New Station Trucker Invoice has been created', subtype='mail.mt_comment')
        return invoice

    @api.multi
    def create_station_delivery_order(self, date_move, product_id,uom,qty, source_location_id, dest_location_id,partner_id,ref):
        # create the stock picking
        stock_picking_obj = self.env['stock.picking']
        vals = {
            'partner_id' : partner_id,
            'location_id': source_location_id,
            'location_dest_id': dest_location_id,
            'min_date': date_move,
            'move_type': 'one',
            'picking_type_id': 25,
            'origin': ref,
            'move_lines': [(0, 0, {
                # 'name': self.product_id.name,
                'product_id': product_id,
                'product_uom_qty': qty,
                'product_uom': uom,
                #  'location_id': self.source_location_id.id,
                # 'location_dest_id': self.destination_location_id.id,
            })],
            'pack_operation_product_ids': [(0, 0, {
                'product_id': product_id,
                'qty_done': qty,
                'product_qty': qty,
                'product_uom_id': uom,
                'location_id': source_location_id,
                'location_dest_id': dest_location_id,
            })],
        }

        pick_id = stock_picking_obj.create(vals)
        pick_id.action_confirm()
        pick_id.action_assign()
        if pick_id.state != 'assigned':
            raise UserError(_('Sorry, Stock qty is not enough for the delivery order operation'))
        pick_id.do_prepare_partial()
        pick_id.pack_operation_product_ids[0].qty_done = pick_id.pack_operation_product_ids[0].product_qty
        pick_id.do_new_transfer()
        pick_id.station_product_dist_id = self.id
        return pick_id



    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft' :
                # Don't allow deletion of stock moves
                raise UserError(_('Sorry, I.D.O cannot deleted. Reset to Draft before attempting to Delete an I.D.O'))
        return super(StationProductDistribution, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('station_prod_distr_code') or 'New'
        rec = super(StationProductDistribution, self).create(vals)
        if not rec.partner_id.internal_location_id :
            rec.partner_id.internal_location_id = rec.destination_location_id
        return rec


    @api.multi
    def write(self, vals):
        partner_id = vals.get('partner_id', False)
        destination_location_id = vals.get('destination_location_id', False)
        if partner_id and destination_location_id :
            self.env['res.partner'].browse(partner_id).internal_location_id = destination_location_id

        res = super(StationProductDistribution, self).write(vals)
        return res

    @api.multi
    def action_confirm(self):

        if self.state == 'confirm':
            raise UserError(_('This record has been previously confirmed. Please refresh your browser'))

        return self.write({'state': 'confirm', 'user_id' : self.env.user.id,
                           'user_confirmed_date': datetime.today()})


    def check_bal_qty_update_lifted_qty(self):
        # check not to over lift the balance qty
        lifting_order_line_id = self.station_distribution_id.station_lifting_order_id.lifting_order_line_ids.filtered(lambda line: line.partner_id == self.partner_id)
        balance_qty = lifting_order_line_id.mapped('balance_qty')
        if self.qty > balance_qty[0]:
            raise UserError('Sorry, you cannot lift more than the balance qty (%s) on the station lifting order (%s)  for %s' % (balance_qty[0], self.station_distribution_id.station_lifting_order_id.name, self.partner_id.name))
        #update lifted qty
        lifting_order_line_id.lifted_qty += self.qty

    def reduce_lifted_qty(self):
        lifting_order_line_id = self.station_distribution_id.station_lifting_order_id.lifting_order_line_ids.filtered(lambda line: line.partner_id == self.partner_id)
        lifted_qty = lifting_order_line_id.mapped('lifted_qty')
        if lifted_qty < 0:
            raise UserError('Sorry, Lifted Qty. in the Lifting Order Line is less than 0 ')
        #update lifted qty
        lifting_order_line_id.lifted_qty -= self.qty


    def do_checks(self):
        #allow only approved service station
        approved_service_station = self.station_distribution_id.station_lifting_order_id.lifting_order_line_ids.filtered(lambda line: line.partner_id == self.partner_id)
        if not approved_service_station :
            raise UserError('Sorry, %s is not approved for this distribution' % (self.partner_id.name))

        is_lifting_order_approved = self.station_distribution_id.station_lifting_order_id.state
        if is_lifting_order_approved != 'approve':
            raise UserError('Sorry, You cannot proceed without an approved Lifting Order')

    @api.multi
    def action_transit(self):
        if self.state == 'transit':
            raise UserError(_('This record has been previously confirmed. Please refresh your browser'))
        self.do_checks()
        self.check_bal_qty_update_lifted_qty()
        return self.write({'state': 'transit', 'user_id': self.env.user.id,
                           'user_confirmed_date': datetime.today()})
    @api.multi
    def action_cancel(self):
        #delete the invoices
        self.shortage_invoice_id.unlink()
        self.trucker_invoice_id.unlink()

        #cancel the shortage sales order
        self.order_shortage_id.unlink()

        #reverse the transfer
        stock_picking_obj = self.env['stock.picking']
        vals = {
            'location_id': self.destination_location_id.id,
            'location_dest_id':  self.source_location_id.id,
            'min_date': datetime.today(),
            'move_type': 'one',
            'picking_type_id': 24,
            'origin': self.name,
            'shipment_ref': 'Cancellation and Reversal of ' + self.name,
            'move_lines': [(0, 0, {
                # 'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_uom_qty': self.delivered_qty,
                'product_uom': self.product_id.uom_id.id,
                #  'location_id': self.source_location_id.id,
                # 'location_dest_id': self.destination_location_id.id,
            })],
            'pack_operation_product_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'qty_done': self.delivered_qty,
                'product_qty': self.delivered_qty,
                'product_uom_id': self.product_id.uom_id.id,
                'location_id': self.destination_location_id.id,
                'location_dest_id': self.source_location_id.id,
            })],
        }

        pick_id = stock_picking_obj.create(vals)
        pick_id.action_confirm()
        pick_id.action_assign()
        if pick_id.state != 'assigned':
            raise UserError(_('Sorry, Stock qty is not enough for the operation'))
        pick_id.do_prepare_partial()
        pick_id.pack_operation_product_ids[0].qty_done = pick_id.pack_operation_product_ids[0].product_qty
        pick_id.do_new_transfer()
        pick_id.station_product_dist_id = self.id
        self.state = 'cancel'

    # def  create_overage_picking(self,overage_qty):
    #     stock_picking_obj = self.env['stock.picking']
    #     vals = {
    #         'partner_id': self.partner_id.id,
    #         'location_id': self.company_id.overage_stock_location_id.id,
    #         'location_dest_id': self.destination_location_id.id,
    #         'min_date': self.date_move,
    #         'move_type': 'one',
    #         'picking_type_id': 26,
    #         'move_lines': [(0, 0, {
    #             # 'name': self.product_id.name,
    #             'product_id': self.product_id.id,
    #             'product_uom_qty': overage_qty,
    #             'product_uom': self.product_id.uom_id.id,
    #             #  'location_id': self.source_location_id.id,
    #             # 'location_dest_id': self.destination_location_id.id,
    #         })],
    #         'pack_operation_product_ids': [(0, 0, {
    #             'product_id': self.product_id.id,
    #             'qty_done': overage_qty,
    #             'product_qty': overage_qty,
    #             'product_uom_id': self.product_id.uom_id.id,
    #             'location_id':  self.company_id.overage_stock_location_id.id,
    #             'location_dest_id': self.destination_location_id.id,
    #         })],
    #     }
    #
    #     pick_id = stock_picking_obj.create(vals)
    #     pick_id.action_confirm()
    #     pick_id.action_assign()
    #     if pick_id.state != 'assigned':
    #         raise UserError(_('Sorry, Stock qty is not enough for the operation'))
    #     pick_id.do_prepare_partial()
    #     pick_id.pack_operation_product_ids[0].qty_done = pick_id.pack_operation_product_ids[0].product_qty
    #     pick_id.do_new_transfer()
    #     pick_id.station_product_dist_id = self.id

    @api.multi
    def action_validate(self):
        if self.state == 'validate':
            raise UserError(_('This record has been previously validated. Please refresh your browser'))
        self.do_checks()
        if self.qty <= 0 or self.delivered_qty <= 0 :
            raise UserError(_('Sorry, please check your Lifted Qty. or Delivered Qty. field'))

        # create the stock picking
        stock_picking_obj = self.env['stock.picking']
        vals = {
            'name' : self.name,
            'partner_id' : self.partner_id.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'min_date': self.date_move,
            'move_type' : 'one',
            'picking_type_id' : 26,
            'move_lines': [(0, 0, {
               # 'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_uom_qty': self.delivered_qty,
                'product_uom':self.product_id.uom_id.id,
               #  'location_id': self.source_location_id.id,
               # 'location_dest_id': self.destination_location_id.id,
            })],
           'pack_operation_product_ids': [(0, 0, {
                    'product_id': self.product_id.id,
                    'qty_done' : self.delivered_qty,
                    'product_qty': self.delivered_qty,
                   'product_uom_id': self.product_id.uom_id.id,
                    'location_id': self.source_location_id.id,
                    'location_dest_id': self.destination_location_id.id,
                })],
        }

        pick_id = stock_picking_obj.create(vals)
        pick_id.action_confirm()
        pick_id.action_assign()
        if pick_id.state != 'assigned':
            raise UserError(_('Sorry, Stock qty is not enough for the operation'))
        pick_id.do_prepare_partial()
        pick_id.pack_operation_product_ids[0].qty_done = pick_id.pack_operation_product_ids[0].product_qty
        pick_id.do_new_transfer()
        pick_id.station_product_dist_id = self.id


        # create overage picking if it exist
        # if self.delivered_qty > self.qty:
        #     overage_qty = self.delivered_qty - self.qty
        #     self.create_overage_picking(overage_qty)

        #create trucker bill
        self.trucker_invoice_id = self.create_trucker_bill(self.delivery_rate , self.delivered_qty)
        self.trucker_invoice_id.signal_workflow('invoice_open')
        self.state = 'validate'

        #Mark the Mother D.O as done if all i.d.os are done
        if all(rec.state == 'validate' for rec in self.station_distribution_id.station_product_dist_ids):
            total_lifted_qty = 0
            for rec in self.station_distribution_id.station_product_dist_ids:
                total_lifted_qty += rec.qty
            if total_lifted_qty == self.station_distribution_id.product_qty:
                self.station_distribution_id.action_done()

        return self.write({'user_validate_id' : self.env.user.id, 'user_validated_date': datetime.today()})


    @api.multi
    def action_print_ido(self):
        self.do_checks()
        return self.env['report'].get_action(self, 'aminata_modifications.report_instant_delivery_order_stations')


    @api.multi
    def action_draft(self):
        self.reduce_lifted_qty()
        self.state = 'draft'


    @api.multi
    def btn_view_stock_pick(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Picking'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_pick_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_pick_ids')
    def _compute_stock_pick_count(self):
        for rec in self:
            rec.stock_pick_count = len(rec.stock_pick_ids)


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        partner_id = self.partner_id

        internal_location = partner_id.internal_location_id
        if partner_id and not internal_location :
            stock_location = self.env['stock.location']
            parent_id = self.env['stock.location'].search([('is_internal_parent_view', '=', True),('usage', '=', 'view')],limit=1)
            if not parent_id:
                raise UserError(_('Please contact the Administrator to set a location as Is Internal Parent View'))
            vals = {
                'name': partner_id.name,
                'usage': 'internal',
                'location_id': parent_id.id,
                'is_internal': True,
            }
            stock_location_obj = stock_location.create(vals)
            internal_location = stock_location_obj
            #partner_id.internal_location_id = internal_location  # this does not tend to save into partner id, which results to creation of duplicates location as you onchange the partner field
            partner_id.write({'internal_location_id': internal_location.id})

        self.destination_location_id = internal_location



    def send_email(self, grp_name, msg):
        # send email
        partn_ids = []
        group_obj = self.env.ref(grp_name)
        user_names = ''
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)

        if partn_ids:
            self.message_post(
                _(msg),
                subject='%s' % msg, partner_ids=partn_ids)

        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return


    def get_default_internal_source_location(self):
        res = self.env['stock.location'].search([('is_internal_source_location', '=', True)],limit=1)
        return res


    @api.depends('to_product_location_id')
    def _compute_delivery_rate(self):
        delivery_rate_obj = self.env['kin.delivery.rate']
        for rec in self:
            if rec.from_product_location_id and  rec.to_product_location_id:
                search_rec = delivery_rate_obj.search(
                    [('from_product_location_id', '=', rec.from_product_location_id.id),
                     ('to_product_location_id', '=', rec.to_product_location_id.id)])
                if search_rec :
                    rec.delivery_rate = search_rec[0].delivery_rate



    # def _compute_pump_price(self):
    #     for rec in self:
    #         rec.sales_price = rec.station_distribution_id.station_lifting_order_id.current_pump_price

    # @api.one
    # def _compute_requested_qty(self):
    #     self.requested_qty = sum(self.station_distribution_id.station_lifting_order_id.lifting_order_line_ids.filtered(lambda line: line.partner_id == self.partner_id).mapped('requested_qty'))
    #
    # @api.one
    # def _compute_bal_lifting_qty(self):
    #     self.bal_lifted_qty = sum(
    #             self.station_distribution_id.station_lifting_order_id.lifting_order_line_ids.filtered(
    #                 lambda line: line.partner_id == self.partner_id).mapped('lifted_qty'))
    #
    # @api.one
    # def _compute_balance_qty(self):
    #     self.balance_qty = sum(
    #             self.station_distribution_id.station_lifting_order_id.lifting_order_line_ids.filtered(
    #                 lambda line: line.partner_id == self.partner_id).mapped('balance_qty'))

    def default_product_location(self):
        prod_loc = self.env['kin.product.location']
        loc = prod_loc.search([('is_default_source_location', '=', True)])
        return loc and loc[0]

    name = fields.Char(string='Name')
    station_distribution_id = fields.Many2one('station.distribution',string='Station Distribution')
    partner_id = fields.Many2one('res.partner',string='Service Station')
    date_move = fields.Date(string='Date',related='station_distribution_id.date',store=True)
    source_location_id = fields.Many2one('stock.location', string='Source Location', ondelete='restrict',track_visibility='onchange',default=get_default_internal_source_location)
    destination_location_id = fields.Many2one('stock.location', string='Destination Location',  ondelete='restrict',track_visibility='onchange')

    product_id = fields.Many2one('product.product', related='station_distribution_id.product_id',store=True, string='Product', ondelete='restrict',track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    qty = fields.Float(string='Lifted Qty.', track_visibility='onchange')
    stock_pick_count = fields.Integer(compute="_compute_stock_pick_count", string='# of Stock Picking', copy=False,default=0)
    stock_pick_ids = fields.One2many('stock.picking', 'station_product_dist_id', string='Stock Picking Entry(s)')

    state = fields.Selection( [('draft', 'Draft'), ('confirm', 'Confirm'),('transit', 'In Transit'),('validate', 'Done'), ('cancel', 'Cancel')],  default='draft', track_visibility='onchange')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id,
                              ondelete='restrict',readonly=True)
    user_confirmed_date = fields.Datetime('Confirmed Date')
    user_validate_id = fields.Many2one('res.users', string='User', ondelete='restrict')
    user_validated_date = fields.Datetime('Validated Date')

    delivered_qty = fields.Float(string='Delivered Qty.')
    delivery_rate = fields.Float('Delivery Rate', compute='_compute_delivery_rate')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('station.product.distribution'))

    trucker_invoice_id = fields.Many2one('account.invoice', string='Trucker Bill')
    from_product_location_id = fields.Many2one('kin.product.location', string='Source Product Location',default=default_product_location)
    to_product_location_id = fields.Many2one('kin.product.location', string='Delivery Location')


class AminataInternalTransfer(models.Model):
    _name = 'aminata.internal.transfer'
    _inherit = ['mail.thread']
    _order = 'name desc'

    @api.multi
    def action_print_sts(self):
        return self.env['report'].get_action(self, 'aminata_modifications.report_station_to_station_transfer')


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                # Don't allow deletion of stock moves
                raise UserError(_('Sorry, Non-Draft Stock Movement cannot be deleted.'))
        return super(AminataInternalTransfer, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('int_stock_move_code') or 'New'
        rec = super(AminataInternalTransfer, self).create(vals)
        if not rec.partner_to_id.internal_location_id:
            rec.partner_to_id.internal_location_id = rec.destination_location_id
        if not rec.partner_from_id.internal_location_id:
            rec.partner_from_id.internal_location_id = rec.location_id
        return rec

    @api.multi
    def write(self, vals):
        partner_to_id = vals.get('partner_id', False)
        partner_from_id = vals.get('partner_from_id', False)
        destination_location_id = vals.get('destination_location_id', False)
        location_id = vals.get('location_id', False)
        if partner_to_id and destination_location_id:
            self.env['res.partner'].browse(partner_to_id).internal_location_id = destination_location_id
        if partner_from_id and location_id:
            self.env['res.partner'].browse(partner_from_id).internal_location_id = location_id
        res = super(AminataInternalTransfer, self).write(vals)
        return res

    def send_email(self, grp_name, msg):
        # send email
        partn_ids = []
        group_obj = self.env.ref(grp_name)
        user_names = ''
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            self.message_post(_(msg),
                subject='%s' % msg, partner_ids=partn_ids)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return

    @api.multi
    def action_confirm(self):

        if self.state == 'confirm':
            raise UserError(_('This record has been previously confirmed. Please refresh your browser'))

        # send email to the approver
        group_name = 'aminata_modifications.group_internal_transfer_aminata_validate_btn'
        msg = 'A Station to Station transfer (%s) has been Initiated and Submitted by %s' % (
            self.name, self.env.user.name)
        self.send_email(group_name, msg)
        return self.write({'state': 'confirm', 'user_id': self.env.user.id,
                           'user_confirmed_date': datetime.today()})



    @api.multi
    def action_validate(self):
        if self.state == 'validate':
            raise UserError(_('This record has been previously validated. Please refresh your browser'))

        if self.qty <= 0:
            raise UserError(_('Sorry, you cannot receive qty that is less than  or equal to zero'))

        # create the stock picking
        stock_picking_obj = self.env['stock.picking']
        vals = {
            'name' : self.name,
            'location_id': self.location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'min_date': self.date_move,
            'move_type': 'one',
            'picking_type_id': 26,
            'move_lines': [(0, 0, {
                # 'name': self.product_id.name,
                'product_id': self.product_id.id,
                'product_uom_qty': self.qty,
                'product_uom': self.product_id.uom_id.id,
                #  'location_id': self.location_id.id,
                # 'location_dest_id': self.destination_location_id.id,
            })],
            'pack_operation_product_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'qty_done': self.qty,
                'product_qty': self.qty,
                'product_uom_id': self.product_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.destination_location_id.id,
            })],
        }

        pick_id = stock_picking_obj.create(vals)
        pick_id.action_confirm()
        pick_id.action_assign()
        if pick_id.state != 'assigned':
            raise UserError(_('Sorry, Stock qty is not enough for the operation'))
        pick_id.do_prepare_partial()
        pick_id.pack_operation_product_ids[0].qty_done = pick_id.pack_operation_product_ids[0].product_qty
        pick_id.do_new_transfer()
        pick_id.internal_picking_id = self.id

        return self.write(
            {'state': 'validate', 'user_validate_id': self.env.user.id, 'user_validated_date': datetime.today()})

    @api.multi
    def action_draft(self):
        self.state = 'draft'

        # send email to the initiator
        partn_ids = []
        user_name = self.user_id.name
        partn_ids.append(self.user_id.partner_id.id)

        if self.user_id.partner_id.email and partn_ids:
            msg = 'The Station to Station Transfer %s has been Reset by %s. Please edit and re-submit' % (
                self.name, self.env.user.name)
            self.message_post(_(msg),
                              subject='The Station to Station Transfer %s has been Reset by %s' % (self.name, self.env.user.name),
                              partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))

    @api.multi
    def btn_view_stock_pick(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Picking'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_pick_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_pick_ids')
    def _compute_stock_pick_count(self):
        for rec in self:
            rec.stock_pick_count = len(rec.stock_pick_ids)


    @api.onchange('partner_from_id','partner_to_id')
    def _onchange_partner_id(self):
        partner_from_id = self.partner_from_id
        partner_to_id = self.partner_to_id
        from_internal_location = partner_from_id.internal_location_id
        to_internal_location = partner_to_id.internal_location_id

        if partner_from_id and not from_internal_location :
            stock_location = self.env['stock.location']
            parent_id = self.env['stock.location'].search([('is_internal_parent_view', '=', True),('usage', '=', 'view')],limit=1)
            if not parent_id:
                raise UserError(_('Please contact the Administrator to set a location as Is Internal Parent View'))
            vals = {
                'name': partner_from_id.name,
                'usage': 'internal',
                'location_id': parent_id.id,
                'is_internal': True,
            }
            stock_location_obj = stock_location.create(vals)
            from_internal_location = stock_location_obj
            #partner_id.internal_location_id = internal_location  # this does not tend to save into partner id, which results to creation of duplicates location as you onchange the partner field
            partner_from_id.write({'internal_location_id': from_internal_location.id})
        self.location_id = from_internal_location

        if partner_to_id and not to_internal_location :
            stock_location = self.env['stock.location']
            parent_id = self.env['stock.location'].search([('is_internal_parent_view', '=', True),('usage', '=', 'view')],limit=1)
            if not parent_id:
                raise UserError(_('Please contact the Administrator to set a location as Is Internal Parent View'))
            vals = {
                'name': partner_to_id.name,
                'usage': 'internal',
                'location_id': parent_id.id,
                'is_internal': True,
            }
            stock_location_obj = stock_location.create(vals)
            to_internal_location = stock_location_obj
            #partner_id.internal_location_id = internal_location  # this does not tend to save into partner id, which results to creation of duplicates location as you onchange the partner field
            partner_to_id.write({'internal_location_id': to_internal_location.id})
        self.destination_location_id = to_internal_location


    name = fields.Char(string='Name',track_visibility='onchange')
    partner_from_id = fields.Many2one('res.partner', string='From Service Station')
    partner_to_id = fields.Many2one('res.partner', string='To Service Station')
    date_move = fields.Date(string='Date', default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    location_id = fields.Many2one('stock.location', string='Source Location', ondelete='restrict',track_visibility='onchange')
    destination_location_id = fields.Many2one('stock.location', string='Destination Location', ondelete='restrict', track_visibility='onchange')

    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')

    qty = fields.Float(string='Qty.', track_visibility='onchange')
    stock_pick_count = fields.Integer(compute="_compute_stock_pick_count", string='# of Stock Picking', copy=False, default=0)
    stock_pick_ids = fields.One2many('stock.picking', 'internal_picking_id', string='Stock Picking Entry(s)')

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Done'), ('cancel', 'Cancel')], default='draft', track_visibility='onchange')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict', readonly=True)
    user_confirmed_date = fields.Datetime('Confirmed Date')
    user_validate_id = fields.Many2one('res.users', string='User', ondelete='restrict')
    user_validated_date = fields.Datetime('Validated Date')

    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('aminata.internal.transfer'))



class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_internal_parent_view = fields.Boolean(string="Is Internal Parent View", help='Only One Location Should be Selected')
    is_internal_source_location = fields.Boolean(string="Internal Source Location", help='Only One Location Should be Selected')


class StationSalesRecord(models.Model):
    _name = 'station.sales'
    _inherit = ['mail.thread']
    _order = 'name desc'

    @api.multi
    def action_print_invoice(self):
        invoice = self.invoice_ids[0]
        return self.env['report'].get_action(invoice, 'aminata_modifications.report_invoice_aminata')


    def _get_user_partner(self):
        user = self.env.user
        user_obj = self.env['res.users']
        partner_id = user_obj.browse(user.id).partner_id
        return partner_id and partner_id[0].id


    def create_station_invoice(self,order):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        company = self.env.user.company_id
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        partner_id = self.partner_id
        if not partner_id:
            raise UserError(_("No Station Manager Set on this record"))


        lines = []
        for sale_order_line_id in order.order_line:
            if not float_is_zero(1, precision_digits=precision):
                account = sale_order_line_id.product_id.property_account_income_id or sale_order_line_id.product_id.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(
                        _('Please define income account for the product: "%s" (id:%d) - or for its category: "%s".') % (
                            sale_order_line_id.product_id.name, sale_order_line_id.product_id.id,
                            sale_order_line_id.product_id.categ_id.name))

                default_analytic_account = order.env['account.analytic.default'].account_get(partner_id = partner_id.id)

                line = (0, 0, {
                    'name': sale_order_line_id.name,
                    'sequence': sale_order_line_id.sequence,
                    'origin': sale_order_line_id.order_id.name,
                    'account_id': account.id,
                    'price_unit': sale_order_line_id.price_unit,
                    'quantity': sale_order_line_id.product_uom_qty,
                    'discount': sale_order_line_id.discount,
                    'uom_id': sale_order_line_id.product_uom.id,
                    'product_id': sale_order_line_id.product_id.id or False,
                    'invoice_line_tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
                    'account_analytic_id': sale_order_line_id.order_id.project_id.id or default_analytic_account and default_analytic_account.analytic_id.id,
                   # 'invoice_id': invoice.id,
                    'sale_line_ids': [(6, 0, [sale_order_line_id.id])]

                })
                lines.append(line)

        invoice_vals = {
            'name': self.name,
            'origin': self.name,
            'comment': self.note,
            'type': 'out_invoice',
            'reference': self.name,
            'account_id': partner_id.property_account_receivable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id,
            'is_station_sales': True,
            'invoice_line_ids': lines ,
            'user_id': self.env.user.id
        }
        invoice = inv_obj.create(invoice_vals)
        # self.env['account.invoice.line'].create(inv_line)

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
        group_obj = self.env.ref('aminata_modifications.group_station_accountant_aminata')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New Station Sales Invoice has been created from %s by %s') % (
                                     self.name,  self.env.user.name),
                                 subject='A New Station Sales Invoice has been created', subtype='mail.mt_comment')
        return invoice


    def create_station_sales_order(self):
        lines = []

        for rec in self.station_sales_line_ids:
            line = (0, 0, {
                'name': rec.product_id.name,
                'product_id': rec.product_id.id,
                'product_uom_qty': rec.qty,
                'product_uom': rec.product_uom.id,
                'price_unit': rec.pump_price,
            })
            lines.append(line)

        partner_id = self.partner_id
        sale_order_id = self.env['sale.order'].create({
            'partner_id': partner_id.id,
            'partner_invoice_id': partner_id.id,
            'partner_shipping_id': partner_id.id,
            'pricelist_id': partner_id.property_product_pricelist.id,
            'client_order_ref': self.name,
            'order_line': lines,
            'is_station_sales': True
        })
        return sale_order_id

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                # Don't allow deletion of stock moves
                raise UserError(_('Sorry, Non-Draft record cannot be deleted.'))
        return super(StationSalesRecord, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('station_sales_code') or 'New'
        rec = super(StationSalesRecord, self).create(vals)
        return rec

    @api.multi
    def write(self, vals):
        res = super(StationSalesRecord, self).write(vals)
        if self.pms_coupon < 0:
            raise UserError(_('PMS Coupon cannot be negative'))
        if self.ago_coupon < 0:
            raise UserError(_('AGO Coupon cannot be negative'))
        if self.cash_coupon < 0:
            raise UserError(_('Cash Coupon cannot be negative'))
        return res


    def send_email(self, grp_name, msg):
        # send email
        partn_ids = []
        group_obj = self.env.ref(grp_name)
        user_names = ''
        for user in group_obj.users:
            user_names += user.name + ", "
            partn_ids.append(user.partner_id.id)
        if partn_ids:
            self.message_post(_(msg),
                subject='%s' % msg, partner_ids=partn_ids)
        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))
        return

    @api.multi
    def action_confirm(self):

        if self.state == 'confirm':
            raise UserError(_('This record has been previously confirmed. Please refresh your browser'))

        # send email to the approver
        group_name = 'aminata_modifications.group_station_sales_aminata_validate_btn'
        msg = 'A Station Sales Order (%s) has been Initiated and Submitted by %s' % (
            self.name, self.env.user.name)
        self.send_email(group_name, msg)
        return self.write({'state': 'confirm', 'user_id': self.env.user.id,
                           'user_confirmed_date': datetime.today()})



    def set_validation_credentials(self):
        # check if the dipping is negative
        for line in self.station_sales_line_ids:
            if line.closing_dip < 0 :
                raise UserError('Closing Dip cannot be negative')
            if line.closing_dip < 0 :
                raise UserError('Qty. Supplied cannot be negative')
            if line.product_received < 0 :
                raise UserError('Qty. Supplied cannot be negative')
            if line.qty < 0 :
                raise UserError('Qty. Sold cannot be negative')
            if line.closing_dip == 0 :
                raise UserError('Closing Dip cannot be zero')

            # check if the opening balance is the same as the closing balance of the previous sales line
            query = """ SELECT id, closing_dip,validation_date FROM station_sales_lines WHERE station_mgr_location_id = %s and product_id =  %s  and state = 'validate' and validation_date = (SELECT  max(validation_date) from station_sales_lines  WHERE  station_mgr_location_id = %s and product_id =  %s  and state = 'validate') """ % (
            line.station_mgr_location_id.id, line.product_id.id, line.station_mgr_location_id.id,line.product_id.id,)
            self.env.cr.execute(query)
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get('closing_dip'):
                prev_closing_dip = query_results[0].get('closing_dip')
                prev_id = query_results[0].get('id')
                if line.opening_dip != prev_closing_dip:
                    raise UserError('Sorry, Opening Dip must be equal to the Previous Closing Dip')
                line.previous_retail_sale_line_id = prev_id

        #if ok, then set values , else raise error
        self.user_validate_id = self.env.user
        self.user_validated_date = datetime.today()

        return

    @api.multi
    def action_validate(self):
        if self.state == 'validate':
            raise UserError(_('This record has been previously validated. Please refresh your browser'))

        self.set_validation_credentials()

        #create sales order
        order = self.create_station_sales_order()
        order.approve_credit_limit_bypass()
        self.order_id = order

        for pick_id in order.picking_ids:
            pick_id.location_id = self.station_mgr_location_id
            pick_id.action_assign()
            if pick_id.state != 'assigned':
                raise UserError(_('Sorry, Stock qty in %s is not enough for the operation' % (self.station_mgr_location_id.name)))
            pick_id.do_prepare_partial()
            for pack_operation in pick_id.pack_operation_product_ids:
                pack_operation.qty_done = pack_operation.product_qty
            pick_id.do_new_transfer()
            pick_id.station_sales_id = self.id
            pick_id.is_station_sales = True
            pick_id.name = self.name

        #Create sales invoice and validate
        invoice = self.create_station_invoice(order)
        invoice.is_station_sales = True
        invoice.station_sales_id = self.id
        invoice.note = self.note
        invoice.signal_workflow('invoice_open')


        #Send email to the debtor
        partn_ids = []
        user_name = self.user_id.name
        partn_ids.append(self.partner_id.id)

        if self.user_id.partner_id.email and partn_ids:
            msg = 'The Station Sales Invoice %s has been Approved by %s for %s. You may request from the Retail Office for your Invoice' % (
                self.name, self.env.user.name,self.partner_id.name)
            self.message_post(_(msg),
                              subject='A Station Sales Invoice %s has been Approved by %s' % (self.name, self.env.user.name),
                              partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))

        #Send Email to the Accountants
        group_name = 'aminata_modifications.group_station_accountant_aminata'
        msg = 'The Station Sales Invoice %s has been Approved by %s for %s.' % (
                self.name, self.env.user.name,self.partner_id.name)
        self.send_email(group_name, msg)

        return self.write({'state': 'validate', 'user_validate_id': self.env.user.id, 'user_validated_date': datetime.today()})

    @api.multi
    def action_draft(self):
        self.state = 'draft'

        # send email to the initiator
        partn_ids = []
        user_name = self.user_id.name
        partn_ids.append(self.user_id.partner_id.id)

        if self.user_id.partner_id.email and partn_ids:
            msg = 'The Sales Order %s has been Reset by %s. Please edit and re-submit' % (
                self.name, self.env.user.name)
            self.message_post(_(msg),
                              subject='The Sales Order %s has been Reset by %s' % (self.name, self.env.user.name),
                              partner_ids=partn_ids)
            self.env.user.notify_info('%s Will Be Notified by Email' % (user_name))

    @api.multi
    def btn_view_invoices(self):
        invoice_ids = self.mapped('invoice_ids')
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
                'target': 'new',
        }
        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_ids.ids
        elif len(invoice_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.multi
    def btn_view_stock_pick(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Picking'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_pick_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_pick_ids')
    def _compute_stock_pick_count(self):
        for rec in self:
            rec.stock_pick_count = len(rec.stock_pick_ids)


    @api.depends('station_sales_line_ids')
    def _compute_amount_total(self):
        for order in self:
            amount_total = 0
            for line in order.station_sales_line_ids:
                amount_total += line.line_amount
            order.update({
                    'amount_total': amount_total
            })

    @api.depends('partner_id','partner_head_id')
    def _compute_location(self):
        for order in self:
            order.station_mgr_location_id = order.partner_head_id.station_mgr_location_id
            order.station_sales_line_ids = False


    name = fields.Char(string='Name', track_visibility='onchange')
    date = fields.Date(string='Date',default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='Station Manager',default=_get_user_partner)
    partner_head_id = fields.Many2one(related='partner_id', string='Station Manager (Editable)')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('validate', 'Done'), ('cancel', 'Cancel')], default='draft', track_visibility='onchange')
    note = fields.Char('Note')
    stock_pick_count = fields.Integer(compute="_compute_stock_pick_count", string='# of Stock Picking', copy=False, default=0)
    stock_pick_ids = fields.One2many('stock.picking', 'station_sales_id', string='Stock Picking Entry(s)')

    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)
    invoice_ids = fields.One2many('account.invoice', 'station_sales_id', string='Invoice(s)')

    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('station.sales'))
    station_sales_line_ids = fields.One2many('station.sales.lines','station_sale_id',string='Station Sales Lines')
    amount_total = fields.Monetary(string='Total Amount', store=True, readonly=True, compute='_compute_amount_total', track_visibility='always')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True, default=lambda self: self.env.user.company_id.currency_id, ondelete='restrict')

    station_mgr_location_id = fields.Many2one('stock.location', string='Retail Station Location',compute=_compute_location,store=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict', readonly=True)
    user_confirmed_date = fields.Datetime('Confirmed Date')
    user_validate_id = fields.Many2one('res.users', string='Validated By', ondelete='restrict')
    user_validated_date = fields.Datetime('Validated Date')
    order_id = fields.Many2one('sale.order',string='Sales Order')
    pms_coupon = fields.Float(string='PMS Coupon')
    ago_coupon = fields.Float(string='AGO Coupon')
    cash_coupon = fields.Float(string='Cash Coupon')
    station_product_received_line_ids = fields.One2many('station.product.received.lines', 'station_sale_id', string='Product Received Lines')



class StationSalesRecordLines(models.Model):
    _name = 'station.sales.lines'

    @api.depends('qty', 'pump_price')
    def _compute_amount(self):
        for line in self:
            price = line.pump_price * line.qty
            line.update({
                'line_amount': price
            })


    @api.depends('opening_dip','product_received','closing_dip','coupon_sales_gals')
    def _compute_values(self):
        for rec in self:
            rec.qty = rec.opening_dip + rec.product_received - rec.closing_dip
            rec.cash_sales_gals = rec.qty - rec.coupon_sales_gals
            rec.total_cash_amt = rec.cash_sales_gals * rec.pump_price
        self._compute_product_received()
        self._compute_coupon()

    @api.onchange('product_id')
    def on_change_product(self):
        if self.product_id :
            sales_price = self.product_id.station_sales_price_ids.filtered(lambda line: line.product_id == self.product_id and line.stock_location_id == self.station_sale_id.station_mgr_location_id)
            if sales_price:
                self.pump_price = sales_price.mapped('sale_price')[0]

            # search for all retails sales lines that are done and have validation date for the selected product
            query = """ SELECT id, closing_dip,validation_date FROM station_sales_lines WHERE station_mgr_location_id = %s and  product_id =  %s  and state = 'validate' and validation_date = (SELECT  max(validation_date) from station_sales_lines  WHERE station_mgr_location_id = %s and product_id =  %s  and state = 'validate') """ % (self.station_mgr_location_id.id, self.product_id.id,self.station_mgr_location_id.id,self.product_id.id,)
            self.env.cr.execute(query)
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get('closing_dip'):
                self.opening_dip = query_results[0].get('closing_dip')
                self.previous_retail_sale_line_id = query_results[0].get('id')




    @api.depends('station_sale_id.station_product_received_line_ids.qty_received')
    def _compute_product_received(self):
        for line in self:
            total_qty_received = 0
            stp_lines = line.station_sale_id.station_product_received_line_ids.filtered(lambda l: l.product_id.id == line.product_id.id)
            for received_line_id in stp_lines:
                total_qty_received += received_line_id.qty_received
            line.product_received = total_qty_received


    @api.depends('station_sale_id','station_sale_id.pms_coupon','station_sale_id.ago_coupon')
    def _compute_coupon(self):
        for line in self:
            if line.product_id.white_product == 'ago' :
                ago_coupon = line.station_sale_id.ago_coupon
                ago_line = line.station_sale_id.station_sales_line_ids.filtered(lambda l: l.product_id.id == line.product_id.id) and line.station_sale_id.station_sales_line_ids.filtered(lambda l: l.product_id.id == line.product_id.id)[0]
                if ago_line:
                    ago_line.coupon_sales_gals = ago_coupon
            if line.product_id.white_product == 'pms' :
                pms_coupon = line.station_sale_id.pms_coupon
                pms_line = line.station_sale_id.station_sales_line_ids.filtered(
                    lambda l: l.product_id.id == line.product_id.id) and line.station_sale_id.station_sales_line_ids.filtered(
                    lambda l: l.product_id.id == line.product_id.id)[0]
                if pms_line:
                    pms_line.coupon_sales_gals = pms_coupon


    station_sale_id = fields.Many2one('station.sales',string='Station Sales')
    partner_id = fields.Many2one('res.partner', related='station_sale_id.partner_id' , string='Station Manager', store=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    opening_dip = fields.Float(string='Opening')
    product_received = fields.Float(string='Qty. Supplied',compute='_compute_product_received', store=True)
    closing_dip = fields.Float(string='Dipping')
    qty = fields.Float(string='Product Sales (gals)', track_visibility='onchange', compute='_compute_values', store=True)
    pump_price = fields.Float(string='Pump Price')
    line_amount = fields.Monetary(string='Total Sales Amt.', store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    coupon_sales_gals = fields.Float(string='Coupon Sales (gals)',compute='_compute_coupon', store=True)
    cash_sales_gals = fields.Float(string='Gal. Sales in Cash', compute='_compute_values', store=True)
    total_cash_amt = fields.Monetary(string='Total Cash Amt.' ,compute='_compute_values', store=True)

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.user.company_id.currency_id, related='station_sale_id.currency_id', store=True, ondelete='restrict')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict', readonly=True)
    validation_date = fields.Datetime(related='station_sale_id.user_validated_date',string='Validation Date', store=True)
    validated_by = fields.Many2one('res.users', related='station_sale_id.user_validate_id', string='Validated By')
    previous_retail_sale_line_id = fields.Many2one('station.sales.lines', string='Previous Sales Line')
    company_id = fields.Many2one('res.company', related='station_sale_id.company_id', string='Company')
    station_mgr_location_id = fields.Many2one('stock.location',related='station_sale_id.station_mgr_location_id' , string='Retail Station Location', store=True)
    state = fields.Selection(related='station_sale_id.state',string='State',store=True)


class StationProductReceivedLines(models.Model):
    _name = 'station.product.received.lines'

    @api.multi
    def write(self, vals):
        res = super(StationProductReceivedLines, self).write(vals)
        if self.qty_received < 0:
            raise UserError(_('Qty. Received cannot be negative'))
        return res


    station_sale_id = fields.Many2one('station.sales', string='Station Sales')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    do_number = fields.Char(string='DO Number(s)')
    qty_received = fields.Float(string='Qty. Received')


class StationSalesPrice(models.Model):
    _name = 'station.sales.price'
    _rec_name = 'stock_location_id'

    stock_location_id = fields.Many2one('stock.location',string='Service Station')
    product_id = fields.Many2one('product.product',string='Product')
    sale_price = fields.Monetary(string='Sales Price')
    currency_id = fields.Many2one("res.currency", string="Currency",default=lambda self: self.env.user.company_id.currency_id, ondelete='restrict')
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('station.sales.price'))


class CustomerCategory(models.Model):
    _name = "customer.category"
    _description = 'Customer Category'

    @api.model
    def create(self, vals):
        prefix = vals.get('prefix',False)
        if prefix :
            IrSequence = self.env['ir.sequence'].sudo()
            val = {
                'name': _('%s Sequence' % vals['name']),
                'padding': 4,
                'number_next': 1,
                'number_increment': 1,
                'prefix': "%s" % vals['prefix'],
                'code': '%s-code' % (vals['prefix']),
                'company_id': vals['company_id'],
            }
            vals['sequence_id'] = IrSequence.create(val).id
        return super(CustomerCategory, self).create(vals)


    name = fields.Char(string='Category')
    prefix = fields.Char(string='Prefix')
    account_id = fields.Many2one('account.account',domain="[('internal_type', '=', 'receivable')]" ,string='Account')
    sequence_id = fields.Many2one('ir.sequence', string="Sequence",ondelete="restrict")
    company_id = fields.Many2one('res.company', string='Company')