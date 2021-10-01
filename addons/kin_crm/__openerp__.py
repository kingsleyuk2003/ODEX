# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'CRM Extensions',
    'version': '0.1',
    'category': 'Sales',
    'description': """
CRM Extensions
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','crm','sale','web_notify','sale_crm'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/crm_wizard_view.xml',
        'crm_view.xml',
        'mail_template.xml'
    ],
    'test':[],
    'installable': True,
    'images': [],
}