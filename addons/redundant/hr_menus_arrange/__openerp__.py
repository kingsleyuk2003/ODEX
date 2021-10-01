# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'HR Menu Arrange',
    'version': '0.1',
    'category': 'Tools',
    'description': """
Consolidate HR menus into a single HR module.
Need Help:
Email: kingsley@kinsolve.com or call: +2348030412562
=======================================================================================
""",
    'author': 'Kingsley Okonkwo',
    'website': 'http://kinsolve.com',
    'depends': ['base','hr','hr_payroll','hr_expense','hr_attendance','hr_holidays'],
    'data': [
        'security/security.xml',
        'menus_arrange.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
