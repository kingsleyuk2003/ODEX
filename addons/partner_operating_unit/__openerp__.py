# -*- coding: utf-8 -*-
# © 2015-17 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# @ 2017 Kinsolve Solutions - Kingsley Okonkwo - kingsley@kinsolve.com
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Operating Unit for Partner",
    "summary": "An operating unit (OU) is an organizational entity part of a "
               "company",
    "version": "9.0.1.0.0",
    "author": "Eficent, "
              "Serpent Consulting Services Pvt. Ltd.,"
                "Kinsolve Solutions,"
              "Odoo Community Association (OCA)",
    "website": "http://www.kinsolve.com",
    "category": "Payment",
    "depends": ["base"],
    "license": "LGPL-3",
    "data": [
        "security/res_partner_security.xml",
        "views/res_partner_view.xml",
    ],
    "demo": [
    ],
    "installable": True,
}
