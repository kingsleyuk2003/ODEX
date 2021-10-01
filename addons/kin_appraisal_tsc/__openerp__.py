# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'HR Appraisal for TSC',
    'version': '0.1',
    'category': 'HR',
    'description': """
Human Resources Appraisal for TSC
=======================================================================================
""",
    'author': 'Kinsolve Solutions',
    'website': 'http://kinsolve.com',
    'depends': ['base','hr','appraisal'],
    'data': [
        'security/ir.model.access.csv',
        'appraisal_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}