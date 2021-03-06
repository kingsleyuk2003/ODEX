.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

======================
Luxembourg MIS reports
======================

This modules provides MIS Builder Report templates for the Luxembourg
P&L and Balance Sheet according to the official full and abbreviated models.

Installation
============

The normal Odoo module installation procedure applies.

This module depends on the mis_builder module which can
be found on apps.odoo.com or the OCA/mis-builder
github repository.

Configuration
=============

To configure this module, you need to go to 
Accounting > Reporting > MIS Reports and create report instance
according to the desired time periods and using one of the following
templates provided by this module:

* Luxembourg Profit & Loss
* Luxembourg Balance Sheet
* Luxembourg Profit & Loss (abbreviated)
* Luxembourg Balance Sheet (abbreviated)

To obtain correct results, the account codes prefixes must match the official
Luxembourg chart of account.

Usage
=====

To use this module, you need to go to 
Accounting > Reporting > MIS Reports and use the buttons
available on the previously configured reports such as preview,
export, add to dashboard.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/123/9.0

Known issues / Roadmap
======================

N/A

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-belgium/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-luxemburg/issues/new?body=module:%20l10n_lu_mis_reports%0Aversion:%209.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Stéphane Bidoul at ACSONE <stephane.bidoul@acsone.eu>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
