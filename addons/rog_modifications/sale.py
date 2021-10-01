# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
import  time


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def create_customer_transfer_invoice(self,recipient_id):
        tran_inv,tran_so = super(SaleOrder,self).create_customer_transfer_invoice(recipient_id)
        tran_inv.is_ssd_sbu = self.is_ssd_sbu
        tran_inv.hr_department_id = self.hr_department_id.id
        tran_inv.sbu_id = self.sbu_id.id
        tran_inv.is_ssa_allow_split = True
        return tran_inv, tran_so


    def post_customer_credit_transfer_journal_entry(self, journal, from_customer, to_customer, amt, product):

        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(SaleOrder,self.with_context(ctx)).post_customer_credit_transfer_journal_entry(journal, from_customer, to_customer, amt, product)
        return res


    @api.multi
    def action_confirm_main_sale(self):

        if self.is_discount_changed and not self.user_has_groups('rog_modifications.group_discount_approve_rog'):
            raise UserError(_('Sorry, You cannot Confirm this Sale Order, because the discount fields was changed. Please contact your superior to confirm the sale'))
        elif self.is_discount_changed and self.user_has_groups('rog_modifications.group_discount_approve_rog'):
            self.is_discount_approved = True
            self.discount_approved_by = self.env.user
        parent_so = self.env.context.get('parent_so',False)
        if parent_so :
            self.is_ssd_sbu = parent_so.is_ssd_sbu
            self.hr_department_id = parent_so.hr_department_id.id
            self.sbu_id = parent_so.sbu_id.id
            self.is_ssa_allow_split = True

        if not self.is_ssd_sbu :
            raise UserError(_('Please select a category'))
        res = super(SaleOrder, self).action_confirm_main_sale()

        return res

    def action_create_advance_invoice(self):
        inv = super(SaleOrder, self).action_create_advance_invoice()
        inv.is_ssd_sbu = self.is_ssd_sbu
        inv.hr_department_id = self.hr_department_id.id
        inv.sbu_id = self.sbu_id.id
        inv.is_ssa_allow_split = True
        return inv

    def create_customer_refund_invoice(self,is_cancel_unloaded_unticketed_qty):
        inv = super(SaleOrder, self).create_customer_refund_invoice(is_cancel_unloaded_unticketed_qty)
        inv.is_ssd_sbu = self.is_ssd_sbu
        inv.hr_department_id = self.hr_department_id.id
        inv.sbu_id = self.sbu_id.id
        inv.is_ssa_allow_split = True
        return inv




    hr_department_id = fields.Many2one('hr.department', string='Shared Service',track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU',track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ],  string='Category',track_visibility='onchange')
    is_discount_changed = fields.Boolean('Discount Changed')
    is_discount_approved = fields.Boolean('Discount Approved')
    discount_changed_by = fields.Many2one('res.users',string="Discount Changed User")
    discount_approved_by = fields.Many2one('res.users', string="Discount Approved User")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        discount_amt = vals.get('discount_amt', False)
        discount = vals.get('discount', False)

        # Check if product sales price has been approved
        product_id = vals.get('product_id', False)
        if product_id :
            product_obj = self.env['product.template'].browse(product_id)
            if product_obj.is_sale_price_changed and not product_obj.is_sale_price_approved :
                raise UserError(_('Please Contact the Sales Manager to Approve the New Sales Price (%s), for the Product (%s)') % (product_obj.list_price,product_obj.name))

        res = super(SaleOrderLine, self).create(vals)

        if discount_amt or discount :
            res.order_id.is_discount_changed = True
            res.order_id.is_discount_approved = False
            res.order_id.discount_changed_by = self.env.user

            #notify superior for discount change
            user_ids = []
            group_obj = self.env.ref('rog_modifications.group_discount_approve_rog')
            user_names = ''
            for user in group_obj.users:
                user_names += user.name + ", "
                user_ids.append(user.id)
            res.order_id.message_subscribe_users(user_ids=user_ids)
            res.order_id.message_post(
                _(
                    'The discount field has been changed by %s, for the order %s') % (
                     self.env.user.name,res.order_id.name),
                subject='Discount Field Changed on Sales Order', subtype='mail.mt_comment')
            res.env.user.notify_info('%s Will Be Notified by Email for the change in discount field' % (user_names))




        return res


    @api.multi
    def write(self, vals):
        discount_amt = vals.get('discount_amt',False)
        discount = vals.get('discount',False)
        price_unit = vals.get('price_unit',False)
        if price_unit:
            raise UserError(_('Sorry, price field value is fixed'))

        if discount_amt or discount :
            self.order_id.is_discount_changed = True
            self.order_id.is_discount_approved = False
            self.order_id.discount_changed_by = self.env.user

            #notify superior for discount change
            user_ids = []
            group_obj = self.env.ref('rog_modifications.group_discount_approve_rog')
            user_names = ''
            for user in group_obj.users:
                user_names += user.name + ", "
                user_ids.append(user.id)
            self.order_id.message_subscribe_users(user_ids=user_ids)
            self.order_id.message_post(
                _(
                    'The discount field has been changed by %s, for the order %s') % (
                     self.env.user.name,self.order_id.name),
                subject='Discount Field Changed on Sales Order', subtype='mail.mt_comment')
            self.env.user.notify_info('%s Will Be Notified by Email for the change in discount field' % (user_names))


        res = super(SaleOrderLine, self).write(vals)

        return res

