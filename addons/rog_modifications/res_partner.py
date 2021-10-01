# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def run_sot_send_mass_mail(self):
        res_partner = self.env['res.partner']
        customers = res_partner.search([('customer','=',True)])
        customers.send_mass_email_sot()
        return True

    @api.model
    def create(self, vals):
        vals['ref'] = self.env['ir.sequence'].next_by_code('rog_code')
        res = super(ResPartner, self).create(vals)

        #customer_location = self.env.ref("stock.stock_location_customers")
        # Create customer location and set it
        # stock_location_obj = self.env['stock.location']
        # stock_loc_vals = {
        #     'name': "%s (%s)" % (res.name , vals['ref']),
        #     'location_id': customer_location.id,
        #     'is_dont_show_location': True,
        #     'usage': 'customer',
        # }
        # res.property_stock_customer = stock_location_obj.create(stock_loc_vals).id


        return res

    is_enforce_credit_limit_so = fields.Boolean(string='Activate Credit Limit', default=True,readonly=True)
    rc_number = fields.Char(string='RC Number')
    tin_number = fields.Char(string='TIN/VAT No.')
    product_service_type = fields.Char(string='Product / Service Type')
    contracted =  fields.Selection([
        ('nill', ' '),
        ('yes', 'YES'),
        ('no', 'NO')])
    registration_status = fields.Selection([
        ('nill', ' '),
        ('yes', 'YES'),
        ('no', 'NO')])
    evaluation_status = fields.Char(string='Evaluation Status')
    control = fields.Char(string='Control')
    others = fields.Char(string='Others')

