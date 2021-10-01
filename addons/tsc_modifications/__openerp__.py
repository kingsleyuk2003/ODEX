{
    'name': 'TSC Modifications',
    'version': '0.1',
    'description': """
TSC Modifications
=======================================================================================
""",
    'author': 'Kingsley',
    'depends': ['base','purchase','kin_helpdesk','kin_purchase','sale','kin_sales_double_validation','kin_report','kin_account','kin_hr'],
    'data': [
        'sequence.xml',
        'security.xml',
        # 'mail_template.xml',
        #  'wizard/sales_order_disapprove_markup.xml',
        'report/custom_sales_order_tsc.xml',
        'res_partner_view.xml',
        'helpdesk.xml',
        'hr_view.xml',
        # 'sale_double_validation.xml',

        # 'report/report_purchaseorder.xml',
        'report/custom_waybill_tsc.xml',
        'report/custom_invoice.xml',
       'sale_double_validation_view.xml',
    ],
    'installable': True,
    'images': [],
}