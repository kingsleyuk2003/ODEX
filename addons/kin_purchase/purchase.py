# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_is_zero, float_compare
from urllib import urlencode
from urlparse import urljoin
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, Warning
from openerp.tools import amount_to_text
from datetime import *

class PurchaseOrderApprovers(models.Model):
    _name = 'purchase.order.approver'

    user_id = fields.Many2one('res.users',string='Approver User')
    date_approver = fields.Datetime(string='Approval Date and Time')
    has_approved = fields.Boolean(string='Has Approved')
    po_ids = fields.Many2many('purchase.order', 'poapprovers', 'poa_id', 'po_id',
                              string='Purchase Orders', ondelete='restrict')

class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'


    @api.model
    def _default_note(self):
        return self.env.user.company_id.po_note

    @api.multi
    def amount_to_text(self, amt, currency=False):
        big = ''
        small = ''
        if currency.name == 'NGN':
            big = 'Naira'
            small = 'kobo'
        elif currency.name == 'USD':
            big = 'Dollar'
            small = 'Cent'
        else:
            big = 'Naira'
            small = 'kobo'

        amount_text = amount_to_text(amt, currency).replace('euro', big).replace('Cent', small)
        return str.upper('**** ' + amount_text + '**** ONLY')


    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = amt_discount_total =  0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amt_discount_total += line.discount_amt

            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'amt_discount_total' : order.currency_id.round(amt_discount_total)
            })

    def _get_url_account_invoice(self, module_name,menu_id,action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name,menu_id)[1]
        fragment['model'] =  'account.invoice'
        fragment['view_type'] = 'form'
        fragment['action']= model_data.get_object_reference(module_name,action_id)[1]
        query = {'db': self.env.cr.dbname}

# for displaying tree view. Remove if you want to display form view
#         fragment['page'] = '0'
#         fragment['limit'] = '80'
#         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


 # For displaying a single record. Remove if you want to display tree view

        fragment['id'] =  context.get("invoice_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res



    def _get_url(self, module_name,menu_id,action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name,menu_id)[1]
        fragment['model'] =  'stock.picking'
        fragment['view_type'] = 'form'
        fragment['action']= model_data.get_object_reference(module_name,action_id)[1]
        query = {'db': self.env.cr.dbname}

# for displaying tree view. Remove if you want to display form view
#         fragment['page'] = '0'
#         fragment['limit'] = '80'
#         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


 # For displaying a single record. Remove if you want to display tree view

        fragment['id'] =  context.get("picking_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res


    def _get_purchase_url(self, module_name, menu_id, action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name, menu_id)[1]
        fragment['model'] = 'purchase.order'
        fragment['view_type'] = 'form'
        fragment['action'] = model_data.get_object_reference(module_name, action_id)[1]
        query = {'db': self.env.cr.dbname}
        fragment['id'] = context.get("purchase_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res


    def confirm_po_email(self):

        if self.state == 'to approve' :
            #send email
            company_email = self.env.user.company_id.email.strip()
            purchase_person_email = self.user_id.partner_id.email.strip()
            purchase_person_name = self.user_id.partner_id.name

            if company_email and purchase_person_email:
                # Custom Email Template
                mail_template = self.env.ref('kin_purchase.mail_templ_rfq_confirmed')
                ctx = {}
                ctx.update({'purchase_id': self.id})
                the_url = self._get_purchase_url('purchase', 'menu_purchase_form_action', 'purchase_form_action', ctx)

                user_ids = []
                group_obj = self.env.ref('kin_purchase.group_receive_rfq_confirmed_email')
                for user in group_obj.users:
                    if user.partner_id.email and user.partner_id.email.strip():
                        user_ids.append(user.id)
                        ctx = {
                            'system_email': company_email,
                            'purchase_person_name': purchase_person_name,
                            'purchase_person_email': purchase_person_email,
                            'notify_person_email': user.partner_id.email,
                            'notify_person_name': user.partner_id.name,
                            'url': the_url
                        }
                        mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                        self.message_subscribe_users(user_ids=user_ids)

            return {}

    @api.multi
    def close_alert_box(self):
        self.show_alert_box = False
        return

    # @api.multi
    # def action_view_invoice(self):
    #     res = super(PurchaseOrderExtend,self).action_view_invoice()
    #     res['target'] = 'new'
    #     return  res
    #
    # @api.multi
    # def action_view_picking(self):
    #     res = super(PurchaseOrderExtend,self).action_view_picking()
    #     res['target'] = 'new'
    #     return  res

    @api.multi
    def _create_picking(self):
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                res = order._prepare_picking()
                res.update({'vend_ref':order.partner_ref})
                picking = self.env['stock.picking'].create(res)
                moves = order.order_line.filtered(lambda r: r.product_id.type in ['product', 'consu'])\
                    ._create_stock_moves(picking)
                move_ids = moves.action_confirm()
                moves = self.env['stock.move'].browse(move_ids)
                moves.force_assign()

                # Send Email to the Stock Person
                company_email = self.env.user.company_id.email.strip()
                if company_email :
                    # Custom Email Template
                    mail_template = self.env.ref('kin_purchase.mail_templ_transfer_created')
                    ctx = {}
                    ctx.update({'picking_id':picking.id})
                    the_url = self._get_url('stock','all_picking','action_picking_tree_all',ctx)
                    users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                    for user in users :
                        if user.has_group('kin_purchase.group_receive_stock_transfer_email') and user.partner_id.email and user.partner_id.email.strip() :
                            ctx = {'system_email': company_email,
                                    'stock_person_email':user.partner_id.email,
                                    'stock_person_name': user.partner_id.name ,
                                    'url':the_url,
                                    'origin': picking.origin
                                }
                            mail_template.with_context(ctx).send_mail(picking.id,force_send=False)
                            order.show_alert_box = True

        return True

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        res = super(PurchaseOrderExtend, self).copy(default)
        res.po_name = False
        res.group_id = False
        return res

    @api.multi
    def button_cancel(self):
        res = super(PurchaseOrderExtend, self).button_cancel()
        for inv in self.invoice_ids:
            if inv.name:
                inv.action_cancel()
            else:
                inv.unlink()
        return res

    @api.multi
    def button_draft(self):
        res = super(PurchaseOrderExtend, self).button_draft()
        if self.rfq_name:
            self.name = self.rfq_name
        for poa in self.poa_ids:
            poa.has_approved = False
        return res

    @api.multi
    def button_approve(self):
        # check if the user is an approver
        user = self.env.user
        all_approved_count = 0
        for poa in self.poa_ids:
            if user == poa.user_id:
                poa.has_approved = True
                poa.date_approver = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            if poa.has_approved == True:
                all_approved_count += 1

        if all_approved_count == len(self.poa_ids):
            is_create_invoice_after_po_confirm = self.env.user.company_id.is_create_invoice_after_po_confirm

            if is_create_invoice_after_po_confirm:
                invoice_obj = self.env['account.invoice']
                for order in self:
                    partn = order.partner_id
                    if partn:
                        journal_domain = [
                            ('type', '=', 'purchase'),
                            ('company_id', '=', self.env.user.company_id.id)
                        ]
                        default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
                        analytic_account_id = default_journal_id.analytic_account_id or False
                        vals = {
                            'partner_id': partn.id,
                            'company_id': order.company_id.id,
                            'type': 'in_invoice',
                            'account_id': partn.property_account_payable_id.id,
                            'payment_term_id': partn.property_supplier_payment_term_id.id,
                            'fiscal_position_id': partn.property_account_position_id.id,
                            'payment_term_id': partn.property_supplier_payment_term_id.id,
                            'partner_bank_id': partn.bank_ids and partn.bank_ids.ids[0] or False,
                            'journal_id': default_journal_id.id,
                            'origin': order.name,

                        }

                        purchase_inv = invoice_obj.create(vals)
                        purchase_inv.purchase_id = order

                        #I noticed the account of the invoice created is nopt populated, thus you may get  The operation cannot be completed, probably due to the following error fotr stockable and Consumable products, but there is no error for service product:
                        # - deletion: you may be trying to delete a record while other records still reference it
                        # - creation/update: a mandatory field is not correctly set
                        #
                        # [object with reference: account_id - account.id]
                        ans = purchase_inv.purchase_order_change()

                        purchase_inv.message_post(_('Invoice Created for Purchase Order  %s.') % (order.name),
                                                  subject='Please See the Created Invoice for the Purchased Order',
                                                  subtype='mail.mt_comment')

                        # Send Email to the Accountant
                        company_email = self.env.user.company_id.email.strip()
                        if company_email:
                            # Custom Email Template
                            mail_template = self.env.ref('kin_purchase.mail_templ_purchase_bill_created_on_ordered_qty')
                            ctx = {}
                            ctx.update({'invoice_id': purchase_inv.id})
                            the_url = self._get_url_account_invoice('account', 'menu_action_invoice_tree2',
                                                                    'action_invoice_tree2', ctx)
                            users = self.env['res.users'].search(
                                [('active', '=', True), ('company_id', '=', self.env.user.company_id.id)])

                            for user in users:
                                if user.has_group(
                                        'kin_stock.group_receive_purchase_bill_email') and user.partner_id.email and user.partner_id.email.strip():
                                    ctx = {'system_email': company_email,
                                           'accountant_email': user.partner_id.email,
                                           'accountant_name': user.partner_id.name,
                                           'url': the_url,
                                           'purchase_id': self.name,
                                           'partner_name': self.partner_id.name

                                           }
                                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                                    self.show_alert_box = True
            res = super(PurchaseOrderExtend, self).button_approve()
            return res

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            company = self.env.user.company_id
            if company.is_activate_purchase_request_approver :
                order.write({'state': 'to approve'})
                if order.po_name:
                    order.name = order.po_name
                else:
                    order.rfq_name = order.name
                    order.name = order.env['ir.sequence'].get('po_id_code')
                    order.po_name = order.name
                order.set_approver_list()
                order.confirm_po_email()
            else:
                return super(PurchaseOrderExtend,self).button_confirm()
        return

    def _is_approver(self):
        for order in self:
            user = self.env.user
            order.is_approver = False
            for poa in order.poa_ids:
                if poa.user_id == user and not poa.has_approved:
                    order.is_approver = True

    def set_approver_list(self):
        company = self.env.user.company_id
        if company.is_activate_purchase_request_approver == True:
            if self.currency_id:
                amt_conv = company.currency_id.compute(self.amount_total, self.currency_id)
            else:
                amt_conv = self.amount_total
            purchase_order_limit = self.env['purchase.order.limit'].search(
                [('from_value', '<', amt_conv), ('to_value', '>=', amt_conv)])
            if not purchase_order_limit and self.amount_total != 0:
                raise UserError(_('Please contact the Administrator to configure the purchase order limit'))

            if purchase_order_limit:
                lines = []
                user = self.env.user
                self.is_approver = False
                for pol in purchase_order_limit:
                    lines += [(0, 0, {
                        'user_id': pol.approver_id
                    })
                              ]
                    if user == pol.approver_id:
                        self.is_approver = True
                self.poa_ids.unlink()
                self.poa_ids = lines

    @api.onchange('amount_total')
    def onchange_amount_total(self):
        self.set_approver_list()

            #
            # self.limit_approver_id = purchase_order_limit[0].approver_id
            #     self.message_post(_(
            #         'The Purchase Order with ID (%s), for %s, from %s, is awaiting limit approval ') % (
            #                           self.name, self.partner_id.name, self.env.user.name),
            #                       subject='Purchase Order (%s) awaiting limit approval' % (self.name), partner_ids=[self.limit_approver_id.partner_id.id],
            #                       subtype='mail.mt_comment')







    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    show_alert_box  = fields.Boolean(string="Show Alert Box")
    amt_discount_total = fields.Monetary(string='Discounts', store=True, readonly=True, compute='_amount_all')
    response_due_date = fields.Datetime(string='Response Due Date')
    user_id = fields.Many2one('res.users', string='Purchase Person', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    purchase_shipping_term_id = fields.Many2one('purchase.shipping.term',string='Shipping Term')
    date_order = fields.Datetime('Order Date', required=True, states=READONLY_STATES, select=True, copy=False,help="Depicts the date where the Quotation should be validated and converted into a purchase order.")
    date_rfq = fields.Datetime('RFQ Date', required=True, states=READONLY_STATES, select=True, copy=False, default=fields.Datetime.now)
    po_name = fields.Char('PO Name')
    rfq_name = fields.Char('RFQ Name')
    notes = fields.Text('Terms and conditions', default=_default_note)
    is_approver = fields.Boolean(string='Is Approver',compute=_is_approver)
    poa_ids = fields.Many2many('purchase.order.approver', 'poapprovers', 'po_id', 'poa_id',
                              string='Purchase Order Approvers', ondelete='restrict')

class PurchaseShippingTerms(models.Model):
    _name = 'purchase.shipping.term'

    name = fields.Char(string='Shipping Term')
    description = fields.Text(string='Description')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # @api.model
    # def create(self, vals):
    #     product_id = vals.get('product_id',False)
    #     if product_id :
    #         product_obj = self.env['product.product'].browse(product_id)
    #         description_purchase = product_obj.description_purchase
    #         if  description_purchase and len(description_purchase.strip()) > 0:
    #             vals['name'] = description_purchase
    #         else :
    #             vals['name'] = product_obj.name
    #     return super(PurchaseOrderLine, self).create(vals)


    @api.onchange('discount_amt')
    def _onchange_discount_amt(self):
        for line in self:
            if line.price_unit:
                disc_amt = line.discount_amt
                taxes = line.taxes_id.compute_all((line.price_unit-disc_amt), line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)

                #means to write to the database fields. you can do direct assignment, but it is not suitable,
                # because, it will hit the database for the number of writes/assignment. e.g. line.price_subtotal = taxes['total_excluded']
                line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'discount' : (disc_amt / line.price_unit) * 100
            })

    @api.onchange('discount')
    def _onchange_discount(self):
        for line in self:
            if line.price_unit:
                disc_amt =  (line.discount / 100) * line.price_unit
                line.discount_amt = disc_amt


    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            disc_amt =  (line.discount / 100) * line.price_unit
            taxes = line.taxes_id.compute_all(line.price_unit-disc_amt, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'discount_amt' : disc_amt,
            })

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                price_unit = line.taxes_id.compute_all(price_unit, currency=line.order_id.currency_id, quantity=1.0)['total_excluded']
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                price_unit = order.currency_id.with_context(date=line.order_id.date_order or fields.Date.context_today(self)).compute(price_unit, order.company_id.currency_id, round=False)

            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'date': line.order_id.date_order,
                'date_expected': line.date_planned,
                'location_id': line.order_id.partner_id.property_stock_supplier.id,
                'location_dest_id': line.order_id._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': line.order_id.dest_address_id.id,
                'move_dest_id': False,
                'state': 'draft',
                'purchase_line_id': line.id,
                'company_id': line.order_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': line.order_id.picking_type_id.id,
                'group_id': line.order_id.group_id.id,
                'procurement_id': False,
                'origin': line.order_id.name,
                'route_ids': line.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id':line.order_id.picking_type_id.warehouse_id.id,


            }

            # Fullfill all related procurements with this po line

            #diff_quantity = line.product_qty # I have to do this so that it creates teh stock moves in the product unit of sales, rather than the product unit of purchase in order to avoid the system from creating the extra stock move when the system does the stock picking documnet is validatted.
            diff_quantity = line.product_uom._compute_qty_obj(line.product_uom, line.product_qty, line.product_id.uom_id) # outputs teh qty from purchase uom to sales uom

            for procurement in line.procurement_ids:
                #procurement_qty = procurement.product_uom._compute_qty_obj(procurement.product_uom, procurement.product_qty, line.product_uom)
                tmp = template.copy()
                tmp.update({
                    #'product_uom_qty': min(procurement_qty, diff_quantity),
                    'product_uom_qty': diff_quantity,
                    'move_dest_id': procurement.move_dest_id.id,  #move destination is same as procurement destination
                    'procurement_id': procurement.id,
                    'propagate': procurement.rule_id.propagate,
                })
                done += moves.create(tmp)
                #diff_quantity -= min(procurement_qty, diff_quantity)
                diff_quantity -= diff_quantity

            # from openerp.tools.float_utils import float_round
            # diff_quantity = 1000.43
            # fdfd = round(1000.45,0)
            # ccfdsc =  round(1000.75,0)
            # ccfsdsc = round(1000.45)
            # a = float_round(diff_quantity, precision_rounding=0.01, rounding_method='UP')
            # sa = float_round(diff_quantity, precision_rounding=0.1, rounding_method='UP')
            # sssa = float_round(diff_quantity, precision_rounding=0.2, rounding_method='UP')
            # sads = float_round(diff_quantity, precision_rounding=2, rounding_method='UP')
            # sdaa = float_round(diff_quantity, precision_rounding=1, rounding_method='UP')
            if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                template['product_uom_qty'] = diff_quantity
                done += moves.create(template)
        return done





    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return

        seller = self.product_id._select_seller(
            self.product_id,
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            return

        price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, self.product_id.supplier_taxes_id, self.taxes_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id.with_context(date=self.order_id.date_order or fields.Date.context_today(self)).compute(price_unit, self.order_id.currency_id)

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = self.env['product.uom']._compute_price(seller.product_uom.id, price_unit, to_uom_id=self.product_uom.id)

        self.price_unit = price_unit

    @api.onchange('product_id')
    def onchange_product_id(self):

        res = super(PurchaseOrderLine, self).onchange_product_id()
        vals = {}

        product_lang = self.product_id.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
        })
        if product_lang.description_purchase:
            self.name = product_lang.description_purchase

        return res



    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    discount_amt = fields.Float(string='Disc./Unit (Amt.)', digits=dp.get_precision('Discount'), default=0.0)
    date_order = fields.Datetime(string='Order date',related='order_id.date_order',ondelete='cascade', index=True,store=True)


class PurchaseRequestExtend(models.Model):
    _inherit = 'purchase.request'

    @api.multi
    def close_alert_box(self):
        self.show_alert_box = False
        return

    def _get_purchase_request_url(self, module_name,menu_id,action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name,menu_id)[1]
        fragment['model'] =  'purchase.request'
        fragment['view_type'] = 'form'
        fragment['action']= model_data.get_object_reference(module_name,action_id)[1]
        query = {'db': self.env.cr.dbname}

# for displaying tree view. Remove if you want to display form view
#         fragment['page'] = '0'
#         fragment['limit'] = '80'
#         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


 # For displaying a single record. Remove if you want to display tree view

        fragment['id'] =  context.get("preq_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res


    @api.multi
    def button_rejected(self):
        res = super(PurchaseRequestExtend,self).button_rejected()
        # Send Email back to Requester for feedback
        company_email = self.env.user.company_id.email.strip()
        requested_by_email = self.requested_by.partner_id.email.strip()

        if company_email and requested_by_email :
            # Custom Email Template
            mail_template = self.env.ref('kin_purchase.mail_templ_purchase_request_status')
            ctx = {}
            ctx.update({'preq_id':self.id})
            the_url = self._get_purchase_request_url('purchase_request','menu_purchase_request_pro_mgt','purchase_request_form_action',ctx)
            users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

            ctx = {'system_email': company_email,
                            'url':the_url
            }
            mail_template.with_context(ctx).send_mail(self.id,force_send=False)
        return res



    @api.multi
    def button_approved(self):
        if self.assigned_to != self.env.user:
            raise UserError(_('Sorry, you are not allowed to approve this request'))
        res = super(PurchaseRequestExtend,self).button_approved()
        # Send Email back to Requester for feedback
        company_email = self.env.user.company_id.email.strip()
        requested_by_email = self.requested_by.partner_id.email.strip()

        if company_email and requested_by_email :
            # Custom Email Template
            mail_template = self.env.ref('kin_purchase.mail_templ_purchase_request_status')
            ctx = {}
            ctx.update({'preq_id':self.id})
            the_url = self._get_purchase_request_url('purchase_request','menu_purchase_request_pro_mgt','purchase_request_form_action',ctx)
            users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

            ctx = {'system_email': company_email,
                            'url':the_url
            }
            mail_template.with_context(ctx).send_mail(self.id,force_send=False)

        return res

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in 'draft' :
                raise UserError(_('Cannot delete a purchase request that is not in draft state.'))
        return  super(PurchaseRequestExtend,self).unlink()

    @api.multi
    def button_to_approve(self):
        res = super(PurchaseRequestExtend,self).button_to_approve()

        if self.env.user.company_id.is_activate_purchase_request_approver == True:
            department_id = self.department_id
            if not department_id :
                raise UserError(_('Please only Employees in a department can perform internal requisition'))
            purchase_request_approver = self.env['purchase.request.approver'].search([('department_id', '=', department_id.id)])
            if not purchase_request_approver:
                raise UserError(_('Please contact the Administrator to configure the purchase request approver for the %s' % (department_id.name)))
            self.assigned_to = purchase_request_approver[0].approver_id


        # Send Email to Approver
        company_email = self.env.user.company_id.email.strip()
        assigned_to_email = self.assigned_to.partner_id.email
        if company_email and assigned_to_email :
            # Custom Email Template
            mail_template = self.env.ref('kin_purchase.mail_templ_purchase_request')
            ctx = {}
            ctx.update({'preq_id':self.id})
            the_url = self._get_purchase_request_url('purchase_request','menu_purchase_request_pro_mgt','purchase_request_form_action',ctx)
            users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

            ctx = {'system_email': company_email,
                            'url':the_url
            }
            mail_template.with_context(ctx).send_mail(self.id,force_send=False)

        return res

    @api.model
    def _get_default_assigned_to(self):
        group_obj = self.env.ref('kin_purchase.group_purchase_request_approver')
        return  group_obj.users and group_obj.users[0]


    assigned_to = fields.Many2one('res.users', 'Approver',track_visibility='onchange', default=_get_default_assigned_to)


class PurchaseRequestLineExtend(models.Model):
    _inherit = 'purchase.request.line'

    name = fields.Text('Description',  track_visibility='onchange', readonly=True)


    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseRequestLineExtend, self).onchange_product_id()
        vals = {}

        if self.product_id and self.product_id.description_purchase:
            self.name = self.product_id.description_purchase

        return res

    @api.model
    def create(self, vals):
        product_id = vals.get('product_id', False)
        if product_id:
            product_obj = self.env['product.product'].browse(product_id)
            description_purchase = product_obj.description_purchase
            if description_purchase and len(description_purchase.strip()) > 0:
                vals['name'] = description_purchase
            else:
                vals['name'] = product_obj.name
        return super(PurchaseRequestLineExtend, self).create(vals)



class PurchaseRequestApprover(models.Model):
    _name = 'purchase.request.approver'

    department_id = fields.Many2one('hr.department', string='Department')
    approver_id = fields.Many2one('res.users',string='Approver')


class PurchaseOrderLimit(models.Model):
    _name = 'purchase.order.limit'

    from_value = fields.Float(string='From Value')
    to_value = fields.Float(string='To Value')
    approver_id = fields.Many2one('res.users',string='Purchase Order Approver')


class ResCompanyExtend(models.Model):
    _inherit = "res.company"

    is_create_invoice_after_po_confirm = fields.Boolean(string='Creates Invoice after PO Confirmation', help="The Product has to be based on Ordered Quantity, for this to create an invoice of the amount ordered")
    is_activate_purchase_request_approver = fields.Boolean(string='Activate Purchase Request Approver',default=True)
    is_activate_purchase_order_limit = fields.Boolean(string='Activate Purchase Order Limit')