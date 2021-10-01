# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Aviation Station Process',
    'version': '0.1',
    'category': 'Sales',
    'description': """
 Aviation Station activities
=======================================================================================

image from openclip http://openclipart.org/
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','product','account','account_asset','account_cancel','mail'],
    'data': [
        'kin_report.xml',
        'report/delivery_receipt.xml',
        'security/security.xml',
        'security/rules.xml',
        'security/ir.model.access.csv',
        'wizard/product_received_register_resolution.xml',
        'wizard/discharged_discrepancy_confirmation.xml',
        'wizard/aviation_record_disapproval_reason.xml',
        'wizard/change_destination.xml',
        'wizard/change_price.xml',
        'wizard/change_totalizer.xml',
        'data/data.xml',
        'sequence.xml',
        'aviation_station_view.xml',
        'cron_data.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}