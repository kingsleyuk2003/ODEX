# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017-2019  Kinsolve Solutions
# Copyright 2017-2019 Kingsley Okonkwo (kingsley@kinsolve.com)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_is_zero, float_compare
from urllib import urlencode
from urlparse import urljoin
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, Warning
from openerp.tools import amount_to_text
from datetime import datetime, time, timedelta


class FormM(models.Model):
    _name = 'form.m'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def email_dispatch(self,msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
                'rog_modifications.group_receive_purchase_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                    '%s for (%s), which is being initiated by %s.') % (msg,
                self.name, self.env.user.name),
                                  subject='%s' % (msg),
                                  subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names,msg))

    @api.multi
    def button_cancel(self):
        for rec in self:
            rec.email_dispatch('Form M Cancelled')
            rec.state = 'cancel'
            for po in rec.purchase_order_ids:
                po.button_cancel()
                po.unlink()
        return

    @api.multi
    def button_draft(self):
        for rec in self:
            rec.email_dispatch('Form M Reset to Draft')
            rec.state = 'draft'
        return

    @api.multi
    def button_form_m_forwarded_scanning_agent(self):
        self.state = 'form_m_forwarded_scanning_agent'
        self.email_dispatch('Form M Forwarded to Scanning Agent ')

    @api.multi
    def button_form_m_forwarded_to_cbn(self):
        self.purchase_type = 'foreign_purchase'
        self.state = 'form_m_forwarded_to_cbn'
        self.email_dispatch('Form M Forwarded to CBN by Bank')


    @api.multi
    def action_create_po(self):
        # Create the PO
        po_obj = self.env['purchase.order']
        partner_id = self.supplier_id
        if not partner_id:
            raise UserError(_("No Supplier set for the form M"))

        po_vals = {
            'form_id': self.id,
            'partner_id': partner_id.id,
            'user_id': self.env.user.id,
            'purchase_type' : 'foreign_purchase',
            'state' : 'foreign_purchase'
        }
        po = po_obj.create(po_vals)

        po_line = {
                'price_unit': self.unit_price_product,
                'product_qty': self.form_m_qty,
                'product_uom': self.product_id.uom_po_id.id,
                'product_id': self.product_id.id,
                'order_id': po.id,
                'date_planned': datetime.today(),
        }
        self.env['purchase.order.line'].create(po_line)
        self.email_dispatch('Purchase Order for the LC BC Created')

        #Open the PO LC BC
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('rog_modifications.action_purchase_order_rog')
        list_view_id = imd.xmlid_to_res_id('rog_modifications.view_form_m_rog_tree')
        form_view_id = imd.xmlid_to_res_id('rog_modifications.purchase_order_rog_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['views'] = [(form_view_id, 'form')]
        result['res_id'] = po.id
        return result

    @api.multi
    def btn_view_purchase_order(self):
        purchase_order_ids = self.mapped('purchase_order_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('rog_modifications.action_purchase_order_rog')
        list_view_id = imd.xmlid_to_res_id('rog_modifications.view_form_m_rog_tree')
        form_view_id = imd.xmlid_to_res_id('rog_modifications.purchase_order_rog_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(purchase_order_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % purchase_order_ids.ids
        elif len(purchase_order_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = purchase_order_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    dpr_import_licence_ref_no = fields.Char(string='DPR Import Licence Ref No.')
    soncap_ref_no = fields.Char(string='SONCAP Ref No.')
    establishment_date = fields.Date(string='Establishment Date')
    bank = fields.Char(string='Bank')
    name = fields.Char(string='Form M No.')
    cb_ba_no = fields.Char(string='CB / BA No.')
    product_id = fields.Many2one('product.product', string='Product')
    form_m_qty = fields.Float(string='Form M Qty. (MT)')
    conv_rate = fields.Float(string='Conversion Rate')
    form_m_qty_ltr = fields.Float(string='Form M Qty. (Ltrs)')
    form_m_value = fields.Float(string='Form M Value')
    trx_type = fields.Selection([('LC', 'LC'), ('BC', 'BC')], string='Trx Type')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    insurance_company_id = fields.Many2one('res.partner', string='Insurance Company')
    insurance_amt = fields.Float(string='Insurance Amount')
    form_m_expiry = fields.Date(string='Form M Expiry Date')
    unit_price_product = fields.Float(string='Product Price')
    purchase_order_ids = fields.One2many('purchase.order', 'form_id', string='Purchase Order Entry(s)')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('form_m_forwarded_scanning_agent', 'Form M Forwarded to Scanning Agent'),
        ('form_m_forwarded_to_cbn', 'Form M Forwarded to CBN by Bank'),
        ('cancel','Cancelled')
    ],string='Status', default='draft', track_visibility='onchange')
    purchase_order_count = fields.Integer(compute="_compute_purchase_order_count", string='# of Purchase Orders',
                                          copy=False, default=0)
    purchase_order_ids = fields.One2many('purchase.order', 'form_id', string='Purchase Order Entry(s)')




class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'


    def email_dispatch(self,msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
                'rog_modifications.group_receive_purchase_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                    '%s for (%s), which is being initiated by %s.') % (msg,
                self.name, self.env.user.name),
                                  subject='%s' % (msg),
                                  subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' % (user_names,msg))




    @api.multi
    def button_cancel(self):
        for order in self:
            order.email_dispatch('Order Cancelled')
        res = super(PurchaseOrderExtend, self).button_cancel()
        if self.is_lc_purchase :
            for inv in self.invoice_ids:
                if inv.name:
                    inv.action_cancel()
                else:
                    inv.unlink()
        return res

    @api.multi
    def button_create_lc_bc_bill(self):
        if self.lc_bc_invoice :
            raise UserError(_('Sorry, LC / BC Bill has been created already'))

        if self.purchase_type == 'local_purchase' :
            raise UserError(_('Sorry, you cannot create LC or BC Bill for Local Purchase'))
        elif not self.final_invoice_value :
            raise UserError(_('Please set the Final Invoice Value'))
        elif self.final_invoice_value  < 0 :
            raise UserError(_('Final Invoice Value is negative'))
        else:
            inv = self.create_lc_bc_bill(abs(self.final_invoice_value/self.form_m_qty), qty=self.form_m_qty,
                                           inv_type='in_invoice')  # Partner is a creditor
            self.lc_bc_invoice = inv
            self.email_dispatch('LC/BC Bill Record')

    @api.multi
    def button_create_pef_bill(self):

        if self.purchase_type == 'local_purchase' :
            raise UserError(_('Sorry, you cannot create PEF Bill for Local Purchase'))
        elif self.pef_invoice :
            raise UserError(_('Sorry, PEF Bill has been created already'))
        if not self.pef_payment :
            raise UserError(_('Please contact the shipping department to set their Shore Receipt (Ltrs)'))
        elif self.pef_payment  < 0 :
            raise UserError(_('Pef Payment is negative'))
        else:
            inv = self.create_pef_bill(abs(self.rate_pef), qty=self.volume,
                                           inv_type='in_invoice')  # Partner is a creditor
            self.pef_invoice = inv
            self.email_dispatch('PEF Bill Record')



    @api.multi
    def button_create_pppra_bill(self):

        if self.purchase_type == 'local_purchase' :
            raise UserError(_('Sorry, you cannot create PPPRA Bill for Local Purchase'))
        elif self.pppra_invoice :
            raise UserError(_('Sorry, PPPRA Bill has been created already'))
        if not self.admin_charge :
            raise UserError(_('Please contact the shipping department to set their Shore Receipt (Ltrs)'))
        elif self.admin_charge  < 0 :
            raise UserError(_('PPPRA Payment is negative'))
        else:
            inv = self.create_pppra_bill(abs(self.rate_pppra), qty=self.volume,
                                           inv_type='in_invoice')  # Partner is a creditor
            self.pppra_invoice = inv
            self.email_dispatch('PPPRA Bill Record')



    @api.multi
    def button_approve_order(self):
        if self.purchase_type == 'foreign_purchase' and self.conv_rate < 1:
            raise UserError('Conversation rate cannot be lesser than 1')
        self.write({'state': 'purchase'})
        self._create_picking()
        return {}

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.purchase_type == 'foreign_purchase' and order.conv_rate < 1 :
                raise UserError('Conversation rate cannot be lesser than 1')

            if order.state not in ['draft', 'sent','local_purchase','letter_of_credit_established']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            # if order.company_id.po_double_validation == 'one_step'\
            #         or (order.company_id.po_double_validation == 'two_step'\
            #             and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id))\
            #         or order.user_has_groups('purchase.group_purchase_manager'):
            #     order.button_approve()
            # else:
            #     order.write({'state': 'to approve'})


            order.write({'state': 'to approve'})
            if order.po_name:
                order.name = order.po_name
            else:
                order.rfq_name = order.name
                order.name = order.env['ir.sequence'].get('po_id_code')
                order.po_name = order.name

            order.email_dispatch('Order Confirmed')
            order.set_approver_list()


        return


    @api.multi
    def button_foreign_purchase(self):
        self.purchase_type = 'foreign_purchase'
        self.state = 'foreign_purchase'
        self.email_dispatch('Foreign Purchase Record')

        # create the ship to ship record
        if not self.ship_to_ship_id :
            ship_id = self.env['ship.to.ship'].create({'purchase_id':self.id})
            self.ship_to_ship_id = ship_id




    @api.multi
    def button_letter_of_credit_established(self):
        self.purchase_type = 'foreign_purchase'
        self.state = 'letter_of_credit_established'
        self.email_dispatch('Letter of Credit Established')


    @api.multi
    def button_local_purchase(self):
        self.purchase_type = 'local_purchase'
        self.state = 'local_purchase'
        self.email_dispatch('Local Purchase Record')

    @api.depends('ship_to_ship_id.discharge_date','dpr_date_interval')
    def _compute_due_date_dpr_submission(self):
        for rec in self:
            if rec.ship_to_ship_id and rec.ship_to_ship_id.discharge_date:
                later_date = datetime.strptime(rec.ship_to_ship_id.discharge_date, "%Y-%m-%d") + timedelta(days=rec.dpr_date_interval)
                rec.due_date_dpr_submission = later_date

    @api.depends('product_id')
    def _compute_rate_pef_pppra(self):
        for rec in self:
            rec.rate_pef = rec.product_id.rate_pef
            rec.rate_pppra = rec.product_id.rate_pppra
            rec.pef_org = rec.product_id.pef_org
            rec.pppra_org = rec.product_id.pppra_org


    @api.depends('ship_to_ship_id.shore_receipt')
    def _compute_pef_pppra_payment(self):
        for rec in self:
            if rec.ship_to_ship_id and rec.ship_to_ship_id.shore_receipt:
                rec.pef_payment = rec.ship_to_ship_id.shore_receipt * rec.rate_pef
                rec.admin_charge = rec.ship_to_ship_id.shore_receipt * rec.rate_pppra


    @api.depends('final_invoice_value','exchange_rate')
    def _compute_naira_value(self):
        for rec in self:
            rec.naira_value = rec.final_invoice_value * rec.exchange_rate


    def create_lc_bc_bill(self,rate=0,qty=0,inv_type='out_invoice'):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        company = self.env.user.company_id
        journal_domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', company.id)
        ]
        journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        if not journal_id:
            raise UserError(_('Please define an accounting purchase journal for this company.'))

        partner_id = self.partner_id
        if not partner_id :
            raise UserError(_("No Partner Set"))

         #Create LC/BC Invoice
        invoice_vals = {
            'name': self.name,
            'origin': self.form_m_no,
            'type': inv_type,
            'reference': self.partner_ref,
            'account_id': partner_id.property_account_payable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id.id,
            'is_lc_bc_invoice': True,
            'user_id': self.env.user.id,
            'currency_id':self.currency_id.id,
        }

        invoice = inv_obj.create(invoice_vals)
        invoice.lc_bc_po = self

        lines = []

        if not float_is_zero(1, precision_digits=precision):
            account = self.product_id.categ_id.property_stock_account_input_categ_id
            if not account:
                raise UserError(
                    _('Please define stock input  account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                        self.product_id.name, self.product_id.id,
                        self.product_id.categ_id.name))


            default_analytic_account = self.env['account.analytic.default'].account_get(
                self.product_id.id, partner_id.id,
                self.env.user.id, datetime.today())



            inv_line = {
                'name': 'LC / BC Bill for %s for qty of %s at rate of %s' % (partner_id.name,qty,rate),
                'origin': self.form_m_no,
                'account_id': account.id,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id or False,
                'account_analytic_id':  default_analytic_account and default_analytic_account.analytic_id.id,
                'invoice_id': invoice.id
            }
            self.env['account.invoice.line'].create(inv_line)


        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if invoice.amount_untaxed < 0:
            invoice.type = 'out_refund'
            for line in invoice.invoice_line_ids:
                line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()

        #Send Email to accountants
        user_ids = []
        group_obj = self.env.ref('rog_modifications.group_receive_form_m_forwarded_to_cbn_email_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New LC / BC Bill has been created for the PO %s by %s') % (
                                   self.name,self.env.user.name),
                              subject='A New LC / BC Bill has been created', subtype='mail.mt_comment')
        return invoice


    def create_pef_bill(self,rate=0,qty=0,inv_type='out_invoice'):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        company = self.env.user.company_id
        journal_domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', company.id)
        ]
        journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        if not journal_id:
            raise UserError(_('Please define an accounting purchase journal for this company.'))

        partner_id = self.product_id.pef_org
        if not partner_id :
            raise UserError(_("No PEF Organization Set on the Product Page"))

         #Create PEF Invoice
        invoice_vals = {
            'name': self.name,
            'origin': self.ship_to_ship_id.name,
            'type': inv_type,
            'reference': self.partner_ref,
            'account_id': partner_id.property_account_payable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id.id,
            'is_pef_invoice': True,
            'user_id': self.env.user.id,
        }

        invoice = inv_obj.create(invoice_vals)
        invoice.pef_po = self

        lines = []

        if not float_is_zero(1, precision_digits=precision):
            account = self.product_id.pef_account
            if not account:
                raise UserError(_('Please define PEF Expense account on the product page'))


            default_analytic_account = self.env['account.analytic.default'].account_get(
                self.product_id.id, partner_id.id,
                self.env.user.id, datetime.today())

            inv_line = {
                'name': 'PEF Bill for %s for qty of %s at rate of %s' % (partner_id.name,qty,rate),
                'origin': self.ship_to_ship_id.name,
                'account_id': account.id,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': self.product_id.uom_id.id,
                'account_analytic_id':  default_analytic_account and default_analytic_account.analytic_id.id,
                'invoice_id': invoice.id
            }
            self.env['account.invoice.line'].create(inv_line)


        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if invoice.amount_untaxed < 0:
            invoice.type = 'out_refund'
            for line in invoice.invoice_line_ids:
                line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()

        #Send Email to accountants
        user_ids = []
        group_obj = self.env.ref('rog_modifications.group_receive_letter_of_credit_established_email_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New PEF Bill has been created for the PO %s by %s') % (
                                   self.name,self.env.user.name),
                              subject='A New PEF Bill has been created', subtype='mail.mt_comment')
        return invoice


    def create_pppra_bill(self,rate=0,qty=0,inv_type='out_invoice'):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        company = self.env.user.company_id
        journal_domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', company.id)
        ]
        journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        if not journal_id:
            raise UserError(_('Please define an accounting purchase journal for this company.'))

        partner_id = self.product_id.pppra_org
        if not partner_id :
            raise UserError(_("No PPPRA Organization Set on the Product Page"))

         #Create PPPRA Invoice
        invoice_vals = {
            'name': self.name,
            'origin': self.ship_to_ship_id.name,
            'type': inv_type,
            'reference': self.partner_ref,
            'account_id': partner_id.property_account_payable_id.id,
            'partner_id': partner_id.id,
            'journal_id': journal_id.id,
            'is_pppra_invoice': True,
            'user_id': self.env.user.id,
        }

        invoice = inv_obj.create(invoice_vals)
        invoice.pppra_po = self

        lines = []

        if not float_is_zero(1, precision_digits=precision):
            account = self.product_id.pppra_account
            if not account:
                raise UserError(_('Please define PPPRA Expense account on the product page'))


            default_analytic_account = self.env['account.analytic.default'].account_get(
                self.product_id.id, partner_id.id,
                self.env.user.id, datetime.today())

            inv_line = {
                'name': 'PPPRA Bill for %s for qty of %s at rate of %s' % (partner_id.name,qty,rate),
                'origin': self.ship_to_ship_id.name,
                'account_id': account.id,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': self.product_id.uom_id.id,
                'account_analytic_id':  default_analytic_account and default_analytic_account.analytic_id.id,
                'invoice_id': invoice.id
            }
            self.env['account.invoice.line'].create(inv_line)


        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if invoice.amount_untaxed < 0:
            invoice.type = 'out_refund'
            for line in invoice.invoice_line_ids:
                line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()

        #Send Email to accountants
        user_ids = []
        group_obj = self.env.ref('rog_modifications.group_receive_local_purchase_email_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
            # invoice.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'A New PPPRA Bill has been created for the PO %s by %s') % (
                                   self.name,self.env.user.name),
                              subject='A New PPPRA Bill has been created', subtype='mail.mt_comment')
        return invoice

    @api.depends('final_invoice_value','form_m_value')
    def _compute_difference_value(self):
        for rec in self:
            rec.difference_value = rec.final_invoice_value - rec.form_m_value




    form_id = fields.Many2one('form.m', string='Form M')

    #Form M Report Details
    dpr_import_licence_ref_no = fields.Char(string='DPR Import Licence Ref No.')
    soncap_ref_no = fields.Char(string='SONCAP Ref No.')
    establishment_date = fields.Date(string='Establishment Date')
    bank = fields.Char(string='Bank')
    form_m_no = fields.Char(string='Form M No.')
    cb_ba_no = fields.Char(string='CB / BA No.')
    product_id = fields.Many2one('product.product',string='Product')
    form_m_qty = fields.Float(string='Form M Qty. (MT)')
    conv_rate = fields.Float(string='Conversion Rate')
    form_m_qty_ltr = fields.Float(string='Form M Qty. (Ltrs)')
    form_m_value = fields.Float(string='Form M Value')
    trx_type = fields.Selection([('LC','LC'),('BC','BC')],string='Trx Type')
    supplier_id = fields.Many2one('res.partner',string='Supplier',related='partner_id',store=True)
    insurance_company_id = fields.Many2one('res.partner',string='Insurance Company')
    insurance_amt = fields.Float(string='Insurance Amount')
    form_m_expiry = fields.Date(string='Form M Expiry Date')
    unit_price_product = fields.Float(string='Product Price')

    #LC and BC Report
    in_house_no = fields.Char(string='In - House No.')
    dpr_import_ref_no = fields.Char(string='DPR Import Licence Ref No.',related='dpr_import_licence_ref_no',store=True)
    pppra_alloc_qty = fields.Float(string='PPRA Allocation QTR')
    lc_bc_establishment_date = fields.Date(string='LC BC Establishment Date')
    form_m_no1 = fields.Char(string='Form M No.',related='form_m_no')
    lc_bc_no = fields.Char(string='LC BC No.')
    bank1 = fields.Char(string='Bank',related='bank')
    supplier_id1 = fields.Many2one('res.partner', string='Supplier',related='supplier_id')
    product_type_id = fields.Many2one('product.product',string='Product Type',related='product_id')
    form_m_qty1 = fields.Float(string='Form M Qty. (MT)',related='form_m_qty')

    form_m_value1 = fields.Float(string='Form M Value',related='form_m_value')
    trx_type1 = fields.Selection([('LC', 'LC'), ('BC', 'BC')],related='trx_type',string='Trx Type')
    mother_vessel_name = fields.Char(string='Name of Mother Vessel',related='ship_to_ship_id.mv_vessel',store=True)
    daughter_vessel_name = fields.Char(string='Name of Daughter Vessel',related='ship_to_ship_id.dv_vessel',store=True)
    bl_qty = fields.Float(string='Bill of Laden Qty. (MT)',related='ship_to_ship_id.dv_bl_qty',store=True)
    shore_tank_qty = fields.Float(string='Shore Tank Qty. (Ltrs)',related='ship_to_ship_id.shore_receipt',store=True)
    final_invoice_value = fields.Float(string='Final Invoice Value')
    difference_value = fields.Float(string='Difference Value',compute='_compute_difference_value',store=True)
    foreign_exchange_bid = fields.Float(string='Foreign Exchange (Bids)')
    exchange_rate = fields.Float(string='Exchange Rate')
    naira_value = fields.Float(string='Naira Value',compute='_compute_naira_value',store=True)
    sgd_qty = fields.Float(string='SGD Qty (MT)')
    sgd_submission_date = fields.Date(string='SGD Submission Date')
    dpr_product_cert_qty = fields.Float(string='DPR Product Cert. Qty.')
    dpr_submission_date = fields.Date(string='DPR Submission Date')
    is_shipping_documents = fields.Selection([('Yes','Yes'),('No','No')],string='Shipping Documents (Y/N)')
    pef_amount = fields.Float(string='PEF Amount')
    is_pef_payment_status = fields.Selection([('Yes', 'Yes'), ('No', 'No')],string='PEF Status of Payment (Y/N)')
    sdn_value = fields.Float(string='SDN Value')
    batch = fields.Char(string='Batch')
    status = fields.Char(string='Status')
    date_paid = fields.Date(string='Date Paid')
    receiving_bank = fields.Char(string='Receiving Bank')
    is_shipping_documents = fields.Boolean(string="Shipping Documents Complete")
    dpr_date_interval = fields.Float(string='DPR Date Interval (days)',default=90)
    due_date_dpr_submission = fields.Date(compute="_compute_due_date_dpr_submission", string='Due Date for DPR Submission',store=True)

    #PEF and PPPRA Report
    issue_date_paid = fields.Date(string='Date Issued/Paid')
    name_of_vessel = fields.Char(string='Name of Vessel',related='ship_to_ship_id.mv_vessel',store=True)
    product_id2 = fields.Many2one('product.product',related='product_id',string='Product')
    volume = fields.Float(string='Volume (ltrs)',related='ship_to_ship_id.shore_receipt',store=True)
    rate_pef = fields.Float(string='Rate (PEF)',compute="_compute_rate_pef_pppra",store=True)
    pef_payment = fields.Float(string='PEF Payment',compute="_compute_pef_pppra_payment",store=True)
    status_payment_pef = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status of Payment (PEF)', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False, related='pef_invoice.state',store=True,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")
    rate_pppra = fields.Float(string='Rate (PPPRA)',compute="_compute_rate_pef_pppra",store=True)
    admin_charge = fields.Float(string='Admin Charge (PPPRA Payment)',compute="_compute_pef_pppra_payment",store=True)
    status_payment_pppra = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status of Payment (PPPRA)', index=True, readonly=True, default='draft',store=True,
        track_visibility='onchange', copy=False, related='pppra_invoice.state',
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")
    lc_bc_pfi = fields.Char(string='Form M / PFI')
    in_house_no_pef_pppra = fields.Char(string='In - House No.',related='in_house_no')
    pef_invoice = fields.Many2one('account.invoice',string='PEF Invoice')
    pppra_invoice = fields.Many2one('account.invoice',string='PPPRA Invoice')
    lc_bc_invoice = fields.Many2one('account.invoice',string='LC/BC Invoice')



    purchase_type = fields.Selection([
        ('local_purchase', 'Local Purchase'),
        ('foreign_purchase', 'Foreign Purchase'),
    ], string='Purchase Type')
    state = fields.Selection(selection_add=[
        ('local_purchase','Local Purchase'),
        ('foreign_purchase', 'Foreign Purchase'),
        ('form_m_forwarded_scanning_agent', 'Form M Forwarded to Scanning Agent'),
        ('form_m_forwarded_to_cbn', 'Form M Forwarded to CBN by Bank'),
        ('letter_of_credit_established', 'letter of Credit Established')
    ])
    reminder_ids = fields.One2many('kin.reminder', 'purchase_id', string='Reminders')
    is_lc_purchase = fields.Boolean(string='Is LC Purchase')
    ship_to_ship_id = fields.Many2one('ship.to.ship',string='Ship To Ship Transfer',ondelete='restrict')



class PurchaseOrderLineExtend(models.Model):
    _inherit = 'purchase.order.line'


    #For proper conversion in the product uom
    # @api.multi
    # def _create_stock_moves(self, picking):
    #     moves = self.env['stock.move']
    #     done = self.env['stock.move'].browse()
    #     for line in self:
    #         order = line.order_id
    #         price_unit = line.price_unit
    #         if line.taxes_id:
    #             price_unit = line.taxes_id.compute_all(price_unit, currency=line.order_id.currency_id, quantity=1.0)['total_excluded']
    #         if line.product_uom.id != line.product_id.uom_id.id:
    #             price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
    #         if order.currency_id != order.company_id.currency_id:
    #             price_unit = order.currency_id.with_context(date=line.order_id.date_order or fields.Date.context_today(self)).compute(price_unit, order.company_id.currency_id, round=False)
    #
    #         template = {
    #             'name': line.name or '',
    #             'product_id': line.product_id.id,
    #             'product_uom': line.product_id.uom_id.id,
    #             'date': line.order_id.date_order,
    #             'date_expected': line.date_planned,
    #             'location_id': line.order_id.partner_id.property_stock_supplier.id,
    #             'location_dest_id': line.order_id._get_destination_location(),
    #             'picking_id': picking.id,
    #             'partner_id': line.order_id.dest_address_id.id,
    #             'move_dest_id': False,
    #             'state': 'draft',
    #             'purchase_line_id': line.id,
    #             'company_id': line.order_id.company_id.id,
    #             'price_unit': price_unit,
    #             'picking_type_id': line.order_id.picking_type_id.id,
    #             'group_id': line.order_id.group_id.id,
    #             'procurement_id': False,
    #             'origin': line.order_id.name,
    #             'route_ids': line.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
    #             'warehouse_id':line.order_id.picking_type_id.warehouse_id.id,
    #
    #
    #         }
    #
    #         # Fullfill all related procurements with this po line
    #
    #         #diff_quantity = line.product_qty # I have to do this so that it creates teh stock moves in the product unit of sales, rather than the product unit of purchase in order to avoid the system from creating the extra stock move when the system does the stock picking documnet is validatted.
    #         diff_quantity = line.product_uom._compute_qty_obj(line.product_uom, line.product_qty, line.product_id.uom_id) # outputs teh qty from purchase uom to sales uom
    #
    #         for procurement in line.procurement_ids:
    #             #procurement_qty = procurement.product_uom._compute_qty_obj(procurement.product_uom, procurement.product_qty, line.product_uom)
    #             tmp = template.copy()
    #             tmp.update({
    #                 #'product_uom_qty': min(procurement_qty, diff_quantity),
    #                 'product_uom_qty': diff_quantity,
    #                 'move_dest_id': procurement.move_dest_id.id,  #move destination is same as procurement destination
    #                 'procurement_id': procurement.id,
    #                 'propagate': procurement.rule_id.propagate,
    #             })
    #             done += moves.create(tmp)
    #             #diff_quantity -= min(procurement_qty, diff_quantity)
    #             diff_quantity -= diff_quantity
    #
    #         # from odoo.tools.float_utils import float_round
    #         # diff_quantity = 1000.43
    #         # fdfd = round(1000.45,0)
    #         # ccfdsc =  round(1000.75,0)
    #         # ccfsdsc = round(1000.45)
    #         # a = float_round(diff_quantity, precision_rounding=0.01, rounding_method='UP')
    #         # sa = float_round(diff_quantity, precision_rounding=0.1, rounding_method='UP')
    #         # sssa = float_round(diff_quantity, precision_rounding=0.2, rounding_method='UP')
    #         # sads = float_round(diff_quantity, precision_rounding=2, rounding_method='UP')
    #         # sdaa = float_round(diff_quantity, precision_rounding=1, rounding_method='UP')
    #         if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
    #             template['product_uom_qty'] = diff_quantity
    #             done += moves.create(template)
    #     return done

    @api.depends('product_qty', 'price_unit', 'taxes_id','product_id','price_subtotal')
    def _compute_amount(self):
        res = super(PurchaseOrderLineExtend,self)._compute_amount()
        for rec in self:
            if rec.product_id and rec.product_id.white_product in ['pms','ago','kero'] :
                rec.order_id.update({'product_id':rec.product_id,'unit_price_product':rec.price_unit,'form_m_qty':rec.product_qty,'form_m_value':rec.price_subtotal, 'conv_rate': rec.conv_rate, 'form_m_qty_ltr' : rec.conv_rate * rec.product_qty})
        return res

    conv_rate = fields.Float(related='product_uom.factor_inv',string='Conv. Rate')


class Reminder(models.Model):
    _inherit = 'kin.reminder'

    purchase_id =  fields.Many2one('purchase.order',string='Purchase Record')


class ProductProduct(models.Model):
    _inherit = 'product.template'

    rate_pef = fields.Float(string='PEF Rate')
    rate_pppra = fields.Float(string='PPPRA Rate')
    pef_org = fields.Many2one('res.partner',string='PEF Organization')
    pppra_org = fields.Many2one('res.partner', string='PPPRA Organization')
    pef_account = fields.Many2one('account.account',string='PEF Expense Account')
    pppra_account = fields.Many2one('account.account',string='PPPRA Expense Account')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    lc_bc_po = fields.Many2one('purchase.order',string='LC/BC PO')
    pef_po = fields.Many2one('purchase.order',string='PEF PO')
    pppra_po = fields.Many2one('purchase.order',string='PPPRA PO')
    is_lc_bc_invoice = fields.Boolean(string='LC BC Invoice')
    is_pef_invoice = fields.Boolean(string='PEF Invoice')
    is_pppra_invoice = fields.Boolean(string='PPPRA invoice')





