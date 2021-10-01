# -*- coding: utf-8 -*-
{
    'name': "File Manager",

    'summary': """
        Keep your data safe and maintained.""",

    'description': """
        This module helps user to keep the files/data safe and maintained well in subordinate system. This acts as 
        an internal drive for the users of the system. 
    """,

    'author': "Mr Module",
    'website':'opensys',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Document',
    'version': '9.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
    # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}