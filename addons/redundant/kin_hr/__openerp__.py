# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'HR Extensions',
    'version': '0.1',
    'category': 'HR',
    'description': """
Human Resources Extensions.
Includes Extra Fields for Employee Directory such as Qualifications, Employment Details,
Next of Kin, Emergency Information, Guarantor Information etc
For Help in Customization: Contact Kingsley Okonkwo on +2348030412562 or email at kingsley@kinsolve.com

=======================================================================================
""",
    'author': 'Kinsolve Solutions',
    'website': 'http://kinsolve.com',
    'depends': ['base','hr'],
    'data': [
        'security/ir.model.access.csv',
        'hr_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}