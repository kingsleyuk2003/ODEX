{
    'name': 'Agary Modifications',
    'version': '0.1',
    'description': """
Agary Modifications
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'depends': ['base','kin_report','kin_account','kin_sales','sale','crm','stock','sale_margin','kin_hr','kin_purchase','product','purchase','hr_contract'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/custom_report_layouts_agary.xml',
        'report/report_purchaseorder.xml',
        'report/custom_waybill_agary.xml',
        'report/custom_grn_agary.xml',
        'report/custom_invoice.xml',
        'report/custom_receipt.xml',
        'stock_view.xml',
        'account_invoice_view.xml',
        'sale_view.xml',
        'hr_view.xml',
        'kin_report.xml',
    ],
    'installable': True,
    'images': [],
}