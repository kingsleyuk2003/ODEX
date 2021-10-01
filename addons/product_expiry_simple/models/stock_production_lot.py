# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from datetime import datetime, timedelta


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    _rec_name = 'display_name'

    expiry_date = fields.Date(string='Expiry Date')
    display_name = fields.Char(
        compute='compute_display_name_field',string='Lot/Serial Number Display', store=True, readonly=True)

    @api.multi
    @api.depends('name', 'expiry_date')
    def compute_display_name_field(self):
        for lot in self:
            dname = lot.name
            # if lot.expiry_date:
            #     exp_date = datetime.strptime(lot.expiry_date,'%Y-%m-%d').strftime('%d/%m/%Y')
            #     dname = '[%s] %s' % (exp_date, dname)
            lot.display_name = dname
