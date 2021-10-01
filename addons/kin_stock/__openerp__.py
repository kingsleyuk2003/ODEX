# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Stock Modifications',
    'version': '0.1',
    'category': 'Warehouse',
    'description': """
Kincotech Customization
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','stock','sale_stock','account','stock_account','mail','purchase','kin_purchase','kin_account','kin_sales','account_analytic_default','stock_landed_costs','account_payment_group'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/picking_rejected.xml',
        'wizard/stock_backorder_confirmation.xml',
        'stock_view.xml',
        'mail_template.xml',
        'report/report_deliveryslip.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'images': [],
}