# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'kincotech',
    'version': '0.1',
    'category': 'Tools',
    'description': """
Kincotech Customization
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','account','purchase','calendar','web','mail','utm'],
    'data': [
         'security/security.xml',
        'kinco_view.xml',
        #'account_bank_statement.xml',
        #'wizard/bank_statement_import_view.xml',
        'change_css_code.xml',
        'static/src/xml/webclient_templates.xml',
    ],   
    'test':[],
    'installable': True,
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
