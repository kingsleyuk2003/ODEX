{
    'name': 'POS SMS',
    'version': '0.1',
    'category': 'Tools',
    'description': """
Send SMS on validating the POS order
=======================================================================================
""",
    'website': 'http://kinsolve.com',
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'depends': ['base','point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'pos_sms_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
