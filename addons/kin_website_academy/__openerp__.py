# -*- coding: utf-8 -*-


{
    'name': 'Academy Training Odoo Web',
    'version': '0.1',
    'category': 'Training',
    'description': """

""",
    'depends': ['website'],
    'data': [
'data/data.xml',
        'security/ir.model.access.csv',
        'views/main_template.xml',
        'views/views.xml',


    ],
    'test':[],
    'installable': True,
    'images': [],
}