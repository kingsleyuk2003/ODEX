# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Help Desk',
    'version': '0.1',
    'category': 'Sales',
    'description': """
HelpDesk
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','mail','stock','analytic','base_suspend_security'],
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'helpdesk_view.xml',
        'sequence.xml',
        'mail_template.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}