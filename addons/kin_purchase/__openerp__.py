# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Purchase Modifications',
    'version': '0.1',
    'category': 'Purchase',
    'description': """
Purchase Modifications
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','purchase','purchase_request','purchase_request_department','product','web_duplicate_visibility'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'purchase_view.xml',
        'mail_template.xml',
        'report/report_purchasequotation.xml',
        'report/report_purchaseorder.xml',
        'sequence.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}