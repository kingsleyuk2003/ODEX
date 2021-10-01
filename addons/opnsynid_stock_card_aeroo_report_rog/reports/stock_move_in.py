# -*- coding: utf-8 -*-
# Copyright 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields
from openerp.tools import drop_view_if_exists


class StockMoveIn(models.Model):
    _name = "stock.stock_move_in"
    _description = "Stock Move In"
    _auto = False

    name = fields.Char(
        string="Description",
    )
    move_id = fields.Many2one(
        string="Move",
        comodel_name="stock.move",
    )
    date = fields.Datetime(
        string="Date",
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    location_id = fields.Many2one(
        string="Location",
        comodel_name="stock.location",
    )
    picking_id = fields.Many2one(
        string="Picking",
        comodel_name="stock.picking",
    )
    picking_type_id = fields.Many2one(
        string="Picking Type",
        comodel_name="stock.picking.type",
    )
    product_qty = fields.Float(
        string="Product Qty",
    )
    product_uom_id = fields.Many2one(
        string="Product UoM",
        comodel_name="product.uom",
    )
    move_qty = fields.Float(
        string="Move Qty",
    )
    move_uom_id = fields.Many2one(
        string="Move UoM",
        comodel_name="product.uom",
    )

    def init(self, cr):
        drop_view_if_exists(cr, "stock_stock_move_in")
        strSQL = """
                    CREATE OR REPLACE VIEW stock_stock_move_in AS (
                        SELECT
                                row_number() OVER() as id,
                                a.id AS move_id,
                                a.date AS date,
                                a.name AS name,
                                a.company_id AS company_id,
                                a.product_id AS product_id,
                                a.location_dest_id AS location_id,
                                a.picking_id AS picking_id,
                                a.picking_type_id AS picking_type_id,
                                a.product_qty AS product_qty,
                                d.uom_id AS product_uom_id,
                                a.product_uom_qty AS move_qty,
                                a.product_uom AS move_uom_id
                        FROM    stock_move AS a
                        LEFT JOIN   stock_picking AS b ON a.picking_id = b.id
                        JOIN product_product AS c ON a.product_id = c.id
                        JOIN product_template AS d ON c.product_tmpl_id = d.id
                        WHERE   a.state = 'done'
                    )
                    """
        cr.execute(strSQL)
