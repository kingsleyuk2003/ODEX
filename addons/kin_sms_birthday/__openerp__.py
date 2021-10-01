# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'SMS Birthday',
    'version': '0.1',
    'category': 'Tools',
    'description': """
Send Birthday SMS
=======================================================================================
""",
    'website': 'http://kinsolve.com',
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'depends': ['base','kin_sms'],
    'data': [
        'cron_data.xml',
        'kin_sms_birthday.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
