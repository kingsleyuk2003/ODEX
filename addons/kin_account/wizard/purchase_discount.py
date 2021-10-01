# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from openerp.exceptions import Warning, except_orm



class po_import(models.TransientModel):
    _name = 'po.import.wizard'
    _description = "PO Import"

    input_file = fields.Binary('Import File', required=True)

