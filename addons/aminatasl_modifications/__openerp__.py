# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Aminata SL Modifications',
    'version': '0.1',
    'description': """
Aminata SL Modifications.
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','sale','kin_sales','kin_sales_double_validation','stock','kin_account_payment_group','aminata_modifications','kin_report',],
    'data': [
         'stock_view.xml',
        'aminata_view.xml',
        'report/custom_report_layouts_aminatasl.xml',
        'report/custom_receipt_aminata.xml',
        'report/custom_sales_quotation.xml',
        'report/custom_delivery_note_aminata.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}