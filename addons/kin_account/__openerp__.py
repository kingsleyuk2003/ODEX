# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Account Modifications',
    'version': '0.1',
    'category': 'Accounting',
    'description': """
Account Modifications
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','account','account_cancel','account_voucher_extend','account_asset','purchase','analytic','report','hr','kin_others','mis_builder'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
'auditor/ir.model.access.csv',
        'account_view.xml',
        'account_invoice_view.xml',
        'account_payment_view.xml',
        'product_view.xml',
        'wizard/account_report_partner_ledger_view.xml',
        'wizard/account_report_general_ledger_view.xml',
        'wizard/account_report_aged_partner_balance_view.xml',
        'report/report_trialbalance.xml',
        'report/custom_report_layouts.xml',
        'report/custom_invoice.xml',
        'report/account_invoice.xml',
        'sequence.xml',
         'mail_template.xml',

    ],
    'test':[],
    'installable': True,
    'images': [],
}