# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _



class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    @api.onchange('is_deferred_revenue')
    def onchange_is_deferred_revenue(self):
        self.sale_ok = False
        self.purchase_ok = False

    disc_acct_analytic_purchase_id = fields.Many2one('account.analytic.account',string="Purchase Discount Analytic Account")
    disc_acct_analytic_sale_id = fields.Many2one('account.analytic.account',string="Sales Discount Analytic Account")
    account_advance_id = fields.Many2one('account.account',string='Unearned Revenue Account' )
    is_deferred_revenue = fields.Boolean(string='Is Deferred Revenue')
    product_deferred_revenue_id = fields.Many2one('product.template',string='Product Deferred Revenue')
    # disc_acct_sale_id = fields.Many2one('account.account',string='Sales Discount Account',help="Records sales discount transactions for this product")
    # disc_acct_purchase_id = fields.Many2one('account.account',string='Purchase Discount Account',help="Records purchase discount transactions for this product")
    # purchase_acc_id = fields.Many2one('account.account',string='Purchase Income Account',help="Records expenses transactions for this product")
    # income_acc_id = fields.Many2one('account.account',string='Purchase Income Account',help="Records income transactions for this product")

class ProductCategoryExtend(models.Model):
    _inherit = "product.category"

    disc_acct_analytic_purchase_id = fields.Many2one('account.analytic.account',string="Purchase Discount Analytic Account",track_visibility='onchange')
    disc_acct_analytic_sale_id = fields.Many2one('account.analytic.account',string="Sales Discount Analytic Account",track_visibility='onchange')
    account_advance_id = fields.Many2one('account.account', string='Unearned Revenue Account')

    # disc_acct_purchase_id = fields.Many2one('account.account',string='Purchase Discount Account',help="Records purchase discount transactions for this product")
    # disc_acct_sale_id = fields.Many2one('account.account',string='Sales Discount Account',help="Records sales discount transactions for this product")
    # purchase_acc_id = fields.Many2one('account.account',string='Purchase Expense Account',help="Records expenses transactions for this product")
    # income_acc_id = fields.Many2one('account.account',string='Purchase Income Account',help="Records income transactions for this product")

