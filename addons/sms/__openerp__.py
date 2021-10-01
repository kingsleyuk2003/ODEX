# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'SMS',
    'version': '0.1',
    'category': 'Tools',
    'description': """
Send SMS from any sms gateway that supports Weservice API over HTTP
=======================================================================================
""",
    'website': 'http://kinsolve.com',
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'depends': ['base','point_of_sale'],
    'data': [
        'sms_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
