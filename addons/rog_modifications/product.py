# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from datetime import datetime, time, timedelta
from openerp import api, fields, models, _
from urllib import urlencode
from urlparse import urljoin
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import UserError





class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'


    @api.model
    def create(self, vals):
        # Check if product sales price has been approved
        list_price = vals.get('list_price', False)
        if list_price :
            vals.update({'is_sale_price_changed' : True,'is_sale_price_changed_by' : self.env.user.id,'is_sale_price_approved' : False, 'is_sale_price_approved_by' : False})
        res = super(ProductTemplateExtend, self).create(vals)
        return res


    @api.multi
    def write(self, vals):
        sale_price = vals.get('list_price',False)

        if sale_price :
            self.is_sale_price_changed = True
            self.is_sale_price_changed_by = self.env.user
            self.is_sale_price_approved = False
            self.is_sale_price_approved_by = False

            #notify superior for price change
            user_ids = []
            group_obj = self.env.ref('rog_modifications.group_product_sales_price_approve_rog')
            user_names = ''
            for user in group_obj.users:
                user_names += user.name + ", "
                user_ids.append(user.id)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(
                _(
                    'The sales price field has been changed by %s, for the product %s') % (
                     self.env.user.name,self.name),
                subject='Sales Price Field Changed for Product', subtype='mail.mt_comment')
            self.env.user.notify_info('%s Will Be Notified by Email for the change in sales price field' % (user_names))


        res = super(ProductTemplateExtend, self).write(vals)

        return res

    @api.multi
    def btn_approve_sale_price(self):
        self.is_sale_price_approved = True
        self.is_sale_price_last_approved_by = self.env.user
        user_ids = []

        group_obj = self.env.ref('rog_modifications.group_product_sales_price_approve_rog')
        user_names = ''
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(
            _(
                'The sales price field has been approved by %s, for the product %s') % (
                self.env.user.name, self.name),
            subject='Sales Price Field Approved for Product', subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for the approval of the sales price' % (user_names))


    is_sale_price_changed = fields.Boolean(string="Is Sale Price Changed",track_visibility='onchange')
    is_sale_price_changed_by = fields.Many2one('res.users', string='Sale Price Changed User')
    is_sale_price_approved = fields.Boolean(string="Is Sale Price Approved",track_visibility='onchange')
    is_sale_price_last_approved_by = fields.Many2one('res.users',string='Sale Price Last Approved User')
    white_product = fields.Selection([
        ('pms', 'PMS'),
        ('ago', 'AGO'),
        ('kero', 'DPK'),
        ('atk', 'ATK'),
        ('lpfo', 'L.P.F.O')
    ], string='White Product')