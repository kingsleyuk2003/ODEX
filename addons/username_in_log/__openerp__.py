# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Username in Log',
    'summary': 'Add the usernames in odoo logs',
    'version': '10.0.1.0.0',
    'author': 'Niboo',
    'category': 'Logs',
    'description': '''
This module adds the current active user login into the logfile of Odoo
    ''',
    'license': 'AGPL-3',
    'website': 'https://www.niboo.be/',
    'images': [
    ],
    'depends': [
        'bus'
    ],
    'installable': True,
    'auto_install': False,
}
