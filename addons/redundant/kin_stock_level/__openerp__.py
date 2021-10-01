# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Stock Level Excel Report',
    'version': '0.1',
    'category': 'Inventory',
    'description': """
Export Current Stock Level Inventory (Quants) reports to Excel. \n
Check the Inventory Module Reporting for the Menu. \n
Incase of any issue: Contact Kingsley at kingsley@kinsolve.com or Call: +2348030412562 \n
Maintainer: \n
Kingsley Okonkwo (CEO Kinsolve Solutions) \n
Address: Suite 212, ACN Towers, off CIPM ROAD Ikeja Lagos, Nigeria.
""",
    'author': 'Kingsley Okonkwo',
    'website': 'http://kinsolve.com',
    'depends': ['base','stock','report_xlsx'],
    'data': [
        'wizard/stock_level_wizard_view.xml',
        'kin_report.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}