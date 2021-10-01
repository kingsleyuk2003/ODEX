# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _

class StockPickingAgary(models.Model):
    _inherit = "stock.picking"

    grn_no = fields.Char(related='name')
    date_grn = fields.Date(string='GRN Date')
    order_no_waybill = fields.Integer(string='Order No. / Way Bill No')
    invoice_no = fields.Integer(string='Invoice No')
    po_no = fields.Char(related='origin',string='PO No',readonly=True)


    agent_id = fields.Many2one('res.partner',string='Name of Agent')
    driver_id = fields.Many2one('res.partner',string='Name of Driver')
    tel_mobile = fields.Char(string='Tel./Mobile No.')
    container_no = fields.Char(string='Container No.')
    vehicle_no = fields.Char(string='Vehicle No.')


class StockQuant(models.Model):
    _inherit = "stock.quant"


    product_code = fields.Char(related='product_id.default_code',string='Product Code',store=True)


# class ProductTemplateExtend(models.Model):
#     _inherit = 'product.template'
#
#     @api.multi
#     @api.depends('name', 'default_code')
#     def name_get(self):
#         return [(r.id, (r.default_code or r.name)) for r in self]
#
#
# class ProductProductExtend(models.Model):
#     _inherit = 'product.product'
#
#     @api.multi
#     @api.depends('name', 'default_code')
#     def name_get(self):
#         return [(r.id, (r.default_code or r.name)) for r in self]
