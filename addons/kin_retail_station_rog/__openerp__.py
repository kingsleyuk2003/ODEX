# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Fuel Retail Station Process for ROG',
    'version': '0.1',
    'category': 'Sales',
    'description': """
 Retail Station activities

Configurations:
-Create product and specify as a white product in the product page
-Create retail station customer and link to retail station
-Create retail station route that is similar to delivery order route by duplicating the "Stock: Ship Only", then edit the procurement location in the procurement rules to match the retail station location

image from openclip http://openclipart.org/
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','stock','product','account','account_asset','account_cancel','mail','report_xlsx'],
    'data': [

        'security/security.xml',
        'security/rules.xml',
'security/ir.model.access.csv',
        'wizard/product_received_register_resolution.xml',
        'wizard/stock_control_disapproval_reason.xml',
        'wizard/discharged_discrepancy_confirmation.xml',
        'wizard/net_difference_confirmation.xml',
        'wizard/change_price.xml',
        'wizard/change_totalizer.xml',
        'wizard/net_difference_approval.xml',
        'wizard/retail_sale_disapproval_reason.xml',
        'wizard/change_destination.xml',
        'wizard/retail_sale_merge.xml',
        'data/data.xml',
        'sequence.xml',
        'retail_station_view.xml',
        'retail_sale_view.xml',
        'cron_data.xml',
        'report.xml',
        'wizard/kin_stock_control_report_wizard_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}