# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _


class PartnerExtend(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def write(self, vals):
        if 'credit_limit' in vals or 'due_amount_receivable' in vals or 'not_due_amount_receivable' in vals or 'allowed_credit' in vals:
            res = super(PartnerExtend, self.sudo()).write(vals)
        else:
            res = super(PartnerExtend, self).write(vals)
        return res


class SaleOrderExtendAgary(models.Model):
    _inherit = "sale.order"

    @api.multi
    @api.onchange('sp_partner_id')
    def onchange_sp_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        if not self.sp_partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.sp_partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.sp_partner_id.property_product_pricelist and self.sp_partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.sp_partner_id.property_payment_term_id and self.sp_partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'note': self.with_context(lang=self.sp_partner_id.lang).env.user.company_id.sale_note,
        }

        if self.sp_partner_id.user_id:
            values['user_id'] = self.sp_partner_id.user_id.id
        if self.sp_partner_id.team_id:
            values['team_id'] = self.sp_partner_id.team_id.id
        self.update(values)


    sale_note = fields.Text(string='Sales Person Note',readonly=True,  states={'draft': [('readonly', False)], 'sent': [('readonly', False)],'to_accept': [('readonly', False)],'waiting': [('readonly', False)],'so_to_approve': [('readonly', False)]}, help="Sales Person can enter his note.")
    account_note = fields.Text(string="Accountant's Note",readonly=True,  states={'draft': [('readonly', False)], 'sent': [('readonly', False)],'to_accept': [('readonly', False)],'waiting': [('readonly', False)],'so_to_approve': [('readonly', False)]}, help="Accountant can enter his note.")
    partner_id = fields.Many2one('res.partner',  string='Customer', readonly=True,
                                    states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                    required=True,
                                    change_default=False, index=True, track_visibility='always')




class SaleOrderLineExtend(models.Model):
    _inherit = 'sale.order.line'

    sp_price = fields.Monetary(string='Sales Person Price',readonly=True,  states={'draft': [('readonly', False)], 'sent': [('readonly', False)],'to_accept': [('readonly', False)],'waiting': [('readonly', False)],'so_to_approve': [('readonly', False)]}, help="Sales Person can enter his note.")