# -*- coding: utf-8 -*-
# © 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from openerp.report import report_sxw


class Parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.list_location = []
        self.list_product = []
        self.list_move = []
        self.dict_total = {}
        self.localcontext.update({
            "time": time,
            "get_company": self._get_company,
            "get_location": self._get_location,
            "get_product": self._get_product,
            "get_move": self._get_move,
            "get_beginning_balance": self._get_beginning_balance,
        })

    def set_context(self, objects, data, ids, report_type=None):
        self.form = data["form"]
        self.date_start = self.form["date_start"]
        self.date_end = self.form["date_end"]
        self.product_ids = self.form["product_ids"]
        self.location_ids = self.form["location_ids"]
        self.company_id = self.form["company_id"]
        return super(Parser, self).set_context(objects, data, ids, report_type)

    def _get_company(self):
        data = self.localcontext['data']['form']
        company_name = data['company_id'] and data['company_id'][1] or False

        return company_name

    def _get_location(self):
        obj_location = self.pool.get("stock.location")

        for location in obj_location.browse(
                self.cr, self.uid, self.location_ids):
            res = {
                "id": location.id,
                "name": location.display_name,
            }
            self.list_location.append(res)

        return self.list_location

    def _get_product(self):
        obj_product = self.pool.get("product.product")
        self.list_product = []
        for product in obj_product.browse(
                self.cr, self.uid, self.product_ids):
            res = {
                "id": product.id,
                "name": product.name,
                "uom": product.uom_id.name,
            }
            self.list_product.append(res)

        return self.list_product

    def _get_move(self, location_id, product_id):
        self.list_move = []
        obj_move = self.pool.get("stock.stock_move_history")
        criteria = [
            ("location_id", "=", location_id),
            ("product_id", "=", product_id),
        ]

        if self.date_start:
            criteria = [
                ("date", ">=", self.date_start),
            ] + criteria

        if self.date_end:
            criteria = [
                ("date", "<=", self.date_end),
            ] + criteria

        move_ids = obj_move.search(
            self.cr, self.uid, criteria, order="date asc, id")

        product = self.pool.get("product.product")
        beg_bal = self._get_beginning_balance(location_id, product_id),
        move_in = move_out = end_bal = 0

        obj_prod = product.browse(self.cr,self.uid,product_id)
        prod_name = obj_prod.name
        product_code = obj_prod.code
        uom = obj_prod.uom_id.name

        for move in obj_move.browse(
                self.cr, self.uid, move_ids):
            self.dict_total[location_id][product_id] += move.product_qty

            if move.move_qty > 0 :
                move_in += move.move_qty
            elif move.move_qty < 0 :
                move_out += abs(move.move_qty)

        res = {
                "beg_bal" : beg_bal,
                "product_name" :  prod_name,
                "product_code":product_code,
                "unit" : uom,
                "move_in" : move_in,
                "move_out" : move_out,
                "end_bal": self._get_total(location_id, product_id),
        }
        self.list_move.append(res)
        return self.list_move

    def _get_beginning_balance(self, location_id, product_id):
        obj_move = self.pool.get("stock.stock_move_history")
        result = 0.0
        if not self.dict_total.get(location_id, False):
            self.dict_total[location_id] = {}

        if not self.dict_total[location_id].get(location_id, False):
            self.dict_total[location_id][product_id] = 0.0

        if self.date_start:
            criteria = [
                ("location_id", "=", location_id),
                ("product_id", "=", product_id),
                ("date", "<", self.date_start),
            ]
            move_ids = obj_move.search(
                self.cr, self.uid, criteria)
            if move_ids:
                for move in obj_move.browse(
                        self.cr, self.uid, move_ids):
                    result += move.product_qty
        self.dict_total[location_id][product_id] = result
        return result

    def _get_total(self, location_id, product_id):
        return self.dict_total[location_id][product_id]
