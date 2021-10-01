# -*- encoding: utf-8 -*-
# Baamtu, 2017
# GNU Affero General Public License <http://www.gnu.org/licenses/>
{
    "name" : "Holidays multi levels approval",
    "version" : "9.2",
    'license': 'AGPL-3',
    "author" : "Baamtu Senegal",
    "category": "Human Resources",
    'website': 'http://www.baamtu.com/',
    'images': ['static/description/banner.jpg'],
    'depends' : ['base', 'hr', 'hr_holidays'],
    'data': [
        'security/security.xml',
        'security/rules.xml',
        'security/ir.model.access.csv',
        'wizard/leave_request_disapprove.xml',
        'views/mail_template.xml',
        'views/employee.xml',
        'views/holidays.xml'
        ],
    'demo': [],
    'qweb': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
