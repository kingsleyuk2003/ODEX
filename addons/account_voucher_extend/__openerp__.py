# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Cash/Bank Expenses Transactions ',
    'version' : '1.0',
    'summary': 'Manage your cash/bank expenses',
    'description': """
TODO

    """,
    'category': 'Accounting & Finance',
    'sequence': 20,
    'depends' : ['account','product'],
    'demo' : [],
    'data' : [
        'security/account_voucher_security.xml',
        'account_voucher_view.xml',
        'voucher_sales_purchase_view.xml',
        'account_voucher_data.xml',
        'security/ir.model.access.csv',
    ],

    'auto_install': False,
    'installable': True,
}
