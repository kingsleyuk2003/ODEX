# -*- coding: utf-8 -*-
# Copyright 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Card Aeroo Report",
    "version": "8.0.2.0.0",
    "category": "Stock",
    "website": "https://opensynergy-indonesia.com/",
    "author": "Andhitia Rama, OpenSynergy Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["base",
        "report_aeroo",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "reports/stock_card_reports.xml",
        "wizards/print_stock_card_views.xml",
    ],
}
