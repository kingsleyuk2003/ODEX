# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api

class StockLevelReportParser(models.TransientModel):

    _name = 'stock.level.parser'

    def _get_stock_level_data(self,form):
        stock_loc_ids = form['stock_location_ids']

        sql_statement = """
                SELECT
                  stock_quant.location_id,
                  sum(stock_quant.qty),
                  stock_quant.product_id,
                  product_template.categ_id,
                  product_template.name
                FROM
                  public.product_product,
                  public.stock_quant,
                  public.product_category,
                  public.product_template
                WHERE
                  product_product.product_tmpl_id = product_template.id AND
                  stock_quant.product_id = product_product.id AND
                  product_template.categ_id = product_category.id AND
                  stock_quant.location_id in %s
                GROUP BY
                  product_template.categ_id,stock_quant.location_id,stock_quant.product_id,product_template.name
                ORDER BY
                  product_template.name;"""

        args = (tuple(stock_loc_ids),)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll






