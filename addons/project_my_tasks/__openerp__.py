# -*- coding: utf-8 -*-
{
    'name': "Project My Tasks Menu",

    'summary': """
        Add menuitem 'My Tasks' to project menu
    """,
    'author': 'Management and Accounting Online',
    'license': 'LGPL-3',
    'website': 'https://maao.com.ua',

    'category': 'Project',
    'version': '9.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['project'],

    'data': [
        'views.xml',
    ],
}
