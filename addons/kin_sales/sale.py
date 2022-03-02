# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
import  time
from datetime import *


class CrmTeamExtend(models.Model):
    _inherit = 'crm.team'

    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')
    sale_stock_location_ids = fields.Many2many('stock.location',string="Sale Stock Locations",help="stock locations where sold items are to delivered from")

    @api.model
    def _get_default_team_id(self, user_id=None):
        res = None
        # settings_obj = self.env['sale.config.settings']
        # is_select_sales_team  = settings_obj.search([('is_select_sales_team', '=', True)], limit=1)
        is_select_sales_team  = self.env.user.company_id.is_select_sales_team
        if not is_select_sales_team :
            res = super(CrmTeamExtend,self)._get_default_team_id(user_id=user_id)
        return  res

class ResCompanyExtend(models.Model):
    _inherit = "res.company"

    is_select_sales_team = fields.Boolean(string='Users Must Select Sales Channel. otherwise pre-select the default Sales channel', help="By default, the system select the default sales team, but if the box is checked, then it clear the selection, for users to select themselves manually")
    is_contraint_sales_order_stock =  fields.Boolean('Do not allow confirmation of sales if stock is lesser than ordered quantity during Sales order confirmation')
    is_sales_order_stock_notification =  fields.Boolean('Send Email Notification if stock is lesser than ordered quantity during Sales order confirmation')
    is_sales_order_stock_purchase_request =  fields.Boolean('Send Email Notification with new created purchase Request if stock is lesser than ordered quantity during Sales order confirmation')
    is_send_stock_notification = fields.Boolean('Send Daily Stock Minimum Notification Report')
    is_invoice_before_delivery = fields.Boolean('Create Invoice from Sales Ordered Qty. before Delivery',help='This should be used for products with fixed/standard costing method')
    is_send_invoice_notification = fields.Boolean('Send Invoice Email Notification on Sales ordered quantity',help='This should be used for products with fixed/standard costing method')
    is_po_check = fields.Boolean('Forces Sales Person to Enter a PO Reference', default=True)
    validity_date_interval = fields.Integer(string='Reminder Days Before Sales Quote Expires', default=3)
    is_send_expiry_email_quote_notification = fields.Boolean(string='Send Expiration Email Quote Notification', default=True)
    is_delete_quote_after_expiration_date  = fields.Boolean(string='Delete Sales Quotation after Expiration Date')


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    #ref: https://odooforbeginnersblog.wordpress.com/2017/06/11/how-to-hide-an-options-in-more-button/
    @api.model
    def hide_invoice_order_from_tree(self):
        pass
        # invoice_order_tree_menu = self.env.ref('sale.sale_order_line_make_invoice')
        # if invoice_order_tree_menu :
        #     invoice_order_tree_menu.unlink()




    #
    # @api.multi
    # def set_credit_sale_state(self):
    #     self.state = 'credit'
    #     # self.is_has_advance_invoice = False
    #     return


    # @api.multi
    # def show_advance_invoice_wizard(self):
    #     if self.amount_total != 0:
    #         model_data_obj = self.env['ir.model.data']
    #         action = self.env.ref(
    #             'kin_sales.action_create_advance_invoice_wizard')
    #         form_view_id = model_data_obj.xmlid_to_res_id(
    #             'kin_sales.view_create_advance_invoice_wizard')
    #
    #         return {
    #             'name': action.name,
    #             'help': action.help,
    #             'type': action.type,
    #             'views': [[form_view_id, 'form']],
    #             'target': action.target,
    #             'domain': action.domain,
    #             'context': {'default_sale_amount': self.amount_total},
    #             'res_model': action.res_model,
    #             'target': 'new'
    #         }
    #     else:
    #         raise UserError(_('Sales Amount cannot be zero'))



    @api.model
    def run_check_expiration_date_sale_order(self):
        is_send_expiry_email_quote_notification = self.env.user.company_id.is_send_expiry_email_quote_notification
        if is_send_expiry_email_quote_notification:
            expiry_day_interval = self.env.user.company_id.validity_date_interval
            the_date = datetime.today().strftime('%d-%m-%Y %H:%M:%S')
            msg = "<style> " \
                  "table, th, td {" \
                  "border: 1px solid black; " \
                  "border-collapse: collapse;" \
                  "}" \
                  "th, td {" \
                  "padding-left: 5px;" \
                  "}" \
                  "</style>"
            msg += "<p>Hello,</p>"
            msg += "<p>Please see the list of Sales Quotations that are about to expire, before %s day(s), which may be deleted, if the are not confirmed</p><p></p>" % (expiry_day_interval)
            msg += "<table width='100%' >"
            msg += "<tr><td colspan='5' align='center' style='margin:35px' ><h3>List of Sales Quotation About to Expire</h3></td></tr>" \
                   "<tr align='left' ><th>S/N</th><th>ID</th><th>Customer</th><th>Expiry Date</th><th>Remaining Days to Expire</th></tr>"

            at_least_one = False
            sales_obj = self.env['sale.order']
            sale_quotes = sales_obj.search([('validity_date','>',the_date),('state','not in',['sale','done'])])
            count = 0

            for sale_quote in sale_quotes:
                sale_quote_name = sale_quote.name
                customer_name = sale_quote.partner_id.name
                validity_date_format = datetime.strptime(sale_quote.validity_date, '%Y-%m-%d').strftime('%d-%m-%Y')

                if sale_quote.validity_date:
                    exp_date = sale_quote.validity_date
                    today = datetime.strptime(datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                                              DEFAULT_SERVER_DATETIME_FORMAT)
                    expiry_date = datetime.strptime(exp_date, '%Y-%m-%d')
                    date_diff = expiry_date - today
                    remaining_days = date_diff.days
                    if (remaining_days <= expiry_day_interval) and (remaining_days < 0):
                        # delete the quotaion
                        if sale_quote.env.user.company_id.is_delete_quote_after_expiration_date:
                            sale_quote.unlink()
                    elif (remaining_days <= expiry_day_interval) and (remaining_days > 0):
                        count += 1
                        at_least_one = True
                        msg += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                            count, sale_quote_name, customer_name, validity_date_format, remaining_days)


            msg += "</table> <p></p><p>This is just a reminder to the follow up on the sales quotaion before expiration date</p>" \
                   "<p>Regards and Thanks</p>" \
                   "<p>This is an autogenerated message from %s ERP System</p>" % (self.env.user.company_id.name)

            # Send Email
            company_email = self.env.user.company_id.email.strip()
            if company_email and at_least_one:
                user_ids = []
                mail_obj = self.env['mail.mail']
                group_obj = self.env.ref('kin_sales.group_receive_sale_quote_expiration_email')
                for user in group_obj.users:
                    # Send Email
                    mail_data = {
                        'model': 'sale.order',
                        'res_id': self.id,
                        'record_name': 'Sales Quotation Expiration Date Reminder Notification',
                        'email_from': company_email,
                        'reply_to': company_email,
                        'subject': "Sales Quotation Expiry Alert Notification Generated for the Date %s" % (the_date),
                        'body_html': '%s' % msg,
                        'auto_delete': True,
                        # 'recipient_ids': [(4, id) for id in new_follower_ids]
                        'email_to': user.partner_id.email
                    }
                    mail_id = mail_obj.create(mail_data)
                    mail_obj.send([mail_id])

            return True

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrderExtend,self).onchange_partner_id()
        self.operating_unit_id_change()
        return res

    @api.multi
    @api.onchange('operating_unit_id')
    def operating_unit_id_change(self):
        pricelist_ou = self.env['product.pricelist'].search([('operating_unit_id', '=', self.operating_unit_id.id)])
        sales_team_ou = self.env['crm.team'].search([('operating_unit_id', '=', self.operating_unit_id.id)])
        # Note that update() is different from Write(). Update(0 method updates on the front end. Similar to what return {'value':{}} does
        if pricelist_ou :
            self.update({'pricelist_id':pricelist_ou[0].id,'team_id':sales_team_ou[0].id})


    @api.multi
    def action_approve(self):
        res = super(SaleOrderExtend,self).action_confirm()
        #check if all sales order line are services
        for order in self :
            is_service_consumable = all([line.product_id.type != 'product' for line in order.order_line])
            if is_service_consumable :
                order.create_customer_invoice()
        return res


    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        res = super(SaleOrderExtend, self).copy(default)
        res.so_name = False
        return res

    @api.model
    def create(self, vals):
        order = super(SaleOrderExtend, self).create(vals)
        order.quote_name = order.name
        return order

    @api.multi
    def write(self, vals):
        res = super(SaleOrderExtend, self).write(vals)
        for rec in self:
            # This is causing some issue, for some invoices when merging invoices in aminata
            # if rec.partner_id.customer and  rec.partner_id.active == False :
            #     raise UserError(_('%s is not approved and active' % (rec.partner_id.name)))
            if len(rec.order_line) == 0:
                raise UserError(_('At Least an Order Line is Required'))
        return res



    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = amt_discount_total = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amt_discount_total += line.discount_amt
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'amt_discount_total' : order.pricelist_id.currency_id.round(amt_discount_total)
            })

    @api.multi
    def action_cancel(self):
        self.show_alert_box = False
        self.show_alert_box1 = False
        for picking in self.picking_ids:
            if picking.state == "done":
                raise UserError(_("Sorry, a delivery has been completed, this sales order cannot be cancelled"))

        return  super(SaleOrderExtend,self).action_cancel()


    @api.onchange('team_id')
    def _team_id(self):
        if self.team_id.warehouse_id:
            self.warehouse_id = self.team_id.warehouse_id.id
        else :
            company = self.env.user.company_id.id
            self.warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)


    @api.multi
    def action_view_delivery(self):
        res = super(SaleOrderExtend,self).action_view_delivery()
        res['target'] = 'new'
        res['nodestroy'] = True
        return  res


    def _get_invoice_url(self, module_name,menu_id,action_id, context=None):
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

    @api.multi
    def close_alert_box(self):
        self.show_alert_box = False
        return

    @api.multi
    def close_alert_box1(self):
        self.show_alert_box1 = False
        return


    def check_line_qty(self,sale_stock_loc_ids):
        listdata= []
        product_obj = self.env['product.product']
        ctx = self.env.context.copy()

        for sale_order in self :
            for sale_order_line in sale_order.order_line :
                product  = sale_order_line.product_id
                product_id = product.id
                product_name = product.name
                min_alert_qty = product.min_alert_qty
                order_line_qty = sale_order_line.product_uom_qty
                qty_available = 0
                if sale_order_line.product_id.type == 'product':
                    for location_id in sale_stock_loc_ids :
                        ctx.update({"location":location_id.id})
                        res = product_obj.browse([product_id])[0].with_context(ctx)._product_available()
                        qty_available += res[product_id]['qty_available']

                    product_qty = self.env['product.uom']._compute_qty_obj(sale_order_line.product_uom, order_line_qty, sale_order_line.product_id.uom_id)
                    if qty_available < product_qty    :
                        listdata.append({product_name:qty_available})
        return listdata

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

        fragment['id'] =  context.get("request_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


        return res


    def create_purchase_request(self,sale_stock_loc_ids):
        purchase_request_obj = self.env['purchase.request']
        sale_order_line_obj = self.env['sale.order.line']
        lines =[]
        for sale_order in self :
            for sale_line in sale_order.order_line :
                low_stock_dict = sale_line.check_order_line_qty_location(sale_stock_loc_ids)
                if low_stock_dict :
                    product_id = low_stock_dict.keys()[0]
                    lines += [(0,0, {
                        'product_id':product_id,
                        'product_qty': sale_line.product_uom_qty,
                        'name' : sale_line.name,
                    })
                    ]
        vals = {
                'origin' : self.name,
                'sale_order_id': self.id,
                'description': self.user_id.name + " was about selling the following listed items with zero stock level. Please request for the items to be purchased from the manager. The sales order reference is: " + self.name ,
                'line_ids':lines
            }
        pr_id = purchase_request_obj.create(vals)
        return pr_id


    @api.multi
    def action_cancel(self):
        #Deletes draft invoices
        self.invoice_ids.unlink()
        for picking in self.picking_ids:
            if picking.state == 'done' :
                raise UserError(_('The Delivery order is done already'))

        res = super(SaleOrderExtend,self).action_cancel()
        return res

    @api.multi
    def action_credit_limit_bypass_request(self,msg):
        self.state = 'credit_limit_by_pass_request'
        self.credit_limit_bypass_requested_by_id = self.env.user.id
        self.bypass_msg = msg

        user_ids = []
        group_obj = self.env.ref('kin_sales.group_receive_request_credit_limit_bypass_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_('A New Credit Limit Request By Pass for the sales order %s has been requested from %s and need your confirmation.') % (
            self.name,self.env.user.name),
                          subject='A New Credit Limit Request By Pass for the sales order has been requested', subtype='mail.mt_comment')

    @api.multi
    def confirm_credit_limit_bypass(self):
        self.state = 'credit_limit_by_pass_confirm'
        self.credit_limit_bypass_confirmed_by_id = self.env.user.id
        #send email notification
        user_ids = []
        group_obj = self.env.ref('kin_sales.group_receive_confirm_credit_limit_bypass_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
            'The Credit Limit Request By Pass for the sales order %s has been confirmed by %s and further needs your approval.') % (
            self.name,self.env.user.name),
                          subject='The Credit Limit Request By Pass for the sales order has been confirmed',
                          subtype='mail.mt_comment')



    @api.multi
    def approve_credit_limit_bypass(self):
        self.credit_limit_bypass_approved_by_id = self.env.user.id
        #self.state = 'credit_limit_by_pass_approve' # no need for this. since anyway the action_approve() will change the state to sales order approved
        self.is_credit_limit_bypass = True
        self.action_approve()
        # send email notification
        user_ids = []
        group_obj = self.env.ref('kin_sales.group_receive_approve_credit_limit_bypass_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
            'The Credit Limit Request By Pass for the sales order %s has been finally approved by %s.') % (
                               self.name,self.env.user.name),
                          subject='The Credit Limit Request By Pass for the sales order has been finally approved',
                          subtype='mail.mt_comment')


    @api.multi
    def action_credit_limit_disapprove(self,msg):
        self.bypass_msg_disapproved = msg
        self.is_credit_limit_bypass = False
        self.state = 'credit_limit_by_pass_disapprove'
        user_ids = []
        group_obj = self.env.ref('kin_sales.group_receive_disapprove_credit_limit_bypass_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
            'The Credit Limit Request By Pass for the sales order %s has been dis-approved by %s, with the following message: %s.') % (
                              self.name, self.env.user.name,msg),
                          subject='The Credit Limit Request By Pass for the sales order has been dis-approved',
                          subtype='mail.mt_comment')


    @api.multi
    def cancel_credit_limit_bypass(self):
        self.state = 'credit_limit_by_pass_cancel'
        self.is_credit_limit_bypass = False


    @api.multi
    def reset_to_draft(self):
        self.state = 'draft'



    @api.multi
    def action_confirm(self):
        list_data = []
        is_contraint_sales_order_stock  = self.env.user.company_id.is_contraint_sales_order_stock
        is_sales_order_stock_notification  = self.env.user.company_id.is_sales_order_stock_notification
        is_sales_order_stock_purchase_request  = self.env.user.company_id.is_sales_order_stock_purchase_request
        is_po_check = self.env.user.company_id.is_po_check

        customer = self.partner_id

        # Check if partner credit limit has been approved
        if customer:
            if customer.is_credit_limit_changed and not customer.is_credit_limit_approved:
                raise UserError(
                    _(
                        'Please Contact the Responsible User to Approve the New Credit Limit (%s), for the Partner (%s)') % (
                        customer.credit_limit, customer.name))

        #is PO Check
        if is_po_check :
            if self.client_order_ref :
                client_order_ref = self.client_order_ref.strip()

                if len(client_order_ref) <= 0 :
                    raise UserError('Please Ensure that the Quote is confirmed from the customer and that the PO reference is set. e.g. you may put the po number, email, contact name, number of the customer that confirmed the Quote on the PO reference field')

            else :
                raise UserError('Please Ensure that the Quote is confirmed from the customer and that the PO reference is set. e.g. you may put the po number, email, contact name, number of the customer that confirmed the Quote')

        #Credit limit Check
        if customer.is_enforce_credit_limit_so and not self.is_credit_limit_bypass :
            if self.amount_total > customer.allowed_credit :
                # Show the wizard to by-pass or display message
                model_data_obj = self.env['ir.model.data']
                action = self.env['ir.model.data'].xmlid_to_object(
                    'kin_sales.action_credit_limit_bypass')
                form_view_id = model_data_obj.xmlid_to_res_id(
                    'kin_sales.view_credit_limit_bypass')

                err_msg ='Total Sales Amount %s%s has exceeded the remaining credit %s%s for %s. You may request for credit limit by pass for this sales order with a reason.' % (self.currency_id.symbol, self.amount_total, self.currency_id.symbol, customer.allowed_credit,customer.name)
                return {
                    'name': action.name,
                    'help': action.help,
                    'type': action.type,
                    'views': [[form_view_id, 'form']],
                    'target': action.target,
                    'domain': action.domain,
                    'context': {'default_err_msg': err_msg},
                    'res_model': action.res_model,
                    'target': 'new'
                }

        if  is_contraint_sales_order_stock or is_sales_order_stock_notification or is_sales_order_stock_purchase_request :
            # Check product qty if is less than 0 for each location
            for sale_order in self :
                stock_locations = ""
                sale_team = sale_order.team_id
                sale_stock_loc_ids = sale_team.sale_stock_location_ids
                list_data  = self.check_line_qty(sale_stock_loc_ids)

                if len(list_data) > 0 :
                    for stock_location in sale_stock_loc_ids:
                        stock_locations += stock_location.name + ", "
                    stock_locations= stock_locations.rstrip(', ')
                    msg = ""
                    sale_msg = ""
                    sale_msg += "The following Items are lesser than the quantity available in the stock locations (%s) \n" % (stock_locations)
                    count = 0
                    for data_dict in list_data:
                        for key, value in data_dict.iteritems(): # keys = data_dict.keys()  # see ref: http://stackoverflow.com/questions/5904969/python-how-to-print-a-dictionarys-key
                            msg += "%s (%s) qty. is lesser than the quantity available in the stock locations (%s) \n" %  (key,value,stock_locations)
                            count+=1
                            sale_msg = "%s). %s (%s) qty. \n" %  (count,key,value)
                    msg += "Please contact the purchase manager to create purchase order for the item(s) \n"

                    company_email = self.env.user.company_id.email

                    #Create and Send Purchase Request Notification
                    if company_email and is_sales_order_stock_purchase_request :

                        pr_id = self.create_purchase_request(sale_stock_loc_ids)
                        ctx = {}
                        ctx.update({'request_id':pr_id.id})
                        the_url = self._get_purchase_request_url('purchase_request','menu_purchase_request_pro_mgt','purchase_request_form_action',ctx)
                        mail_template = self.env.ref('kin_sales.mail_templ_purchase_request_email_sales_stock')
                        users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                        for user in users :
                            if user.has_group('kin_sales.group_receive_sale_order_purchase_request_email') and user.partner_id.email and user.partner_id.email :
                                ctx = {'system_email': company_email,
                                        'purchase_request_email':user.partner_id.email,
                                        'partner_name': user.partner_id.name ,
                                        'sale_order_name': sale_order.name,
                                        'url' : the_url,
                                    }
                                mail_template.with_context(ctx).send_mail(pr_id.id,force_send=False) #Before force_send was True
                                self.show_alert_box1 = True

                    #Send Email to purchase person
                    if is_contraint_sales_order_stock and not is_sales_order_stock_notification :
                        raise UserError(_(msg))
                    elif company_email and is_contraint_sales_order_stock and is_sales_order_stock_notification:
                        # Custom Email Template
                        mail_template = self.env.ref('kin_sales.mail_templ_purchase_stock_level_email_sales_stock_alert')
                        users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                        users_msg = ""
                        for user in users :
                            if user.has_group('kin_sales.group_receive_sale_order_stock_alert_email') and user.partner_id.email and user.partner_id.email :
                                ctx = {'system_email': company_email,
                                        'purchase_stock_email':user.partner_id.email,
                                        'partner_name': user.partner_id.name ,
                                        'sale_order_name': sale_order.name,
                                        'stock_locations' : stock_locations,
                                        'msg' : sale_msg
                                        }
                                mail_template.with_context(ctx).send_mail(sale_order.id,force_send=True) # It has to force send the email, before hitting the user error below, otherwise it will not send the email because of the user error raised below
                                self.show_alert_box1 = True
                                users_msg += user.partner_id.name + ", "
                        users_msg = users_msg.rstrip(", ")
                        if users_msg :
                            msg += "However, A Stock Alert Email for the item(s) has been sent to %s ." % (users_msg)
                        raise UserError(_(msg))

                    elif company_email and not is_contraint_sales_order_stock and is_sales_order_stock_notification :
                        # Custom Email Template
                        mail_template = self.env.ref('kin_sales.mail_templ_purchase_stock_level_email_sales_stock_alert')
                        users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                        users_msg = ""
                        for user in users :
                            if user.has_group('kin_sales.group_receive_sale_order_stock_alert_email') and user.partner_id.email and user.partner_id.email :
                                ctx = {'system_email': company_email,
                                        'purchase_stock_email':user.partner_id.email,
                                        'partner_name': user.partner_id.name ,
                                        'sale_order_name': sale_order.name,
                                        'stock_locations' : stock_locations,
                                        'msg' : sale_msg
                                    }
                                mail_template.with_context(ctx).send_mail(sale_order.id,force_send=False)
                                self.show_alert_box1 = True

        if self.so_name:
            self.name = self.so_name
        else:
            self.quote_name = self.name
            self.name = self.env['ir.sequence'].get('so_id_code')
            self.so_name = self.name
        ctx = dict(self._context)
        ctx['is_other_sale'] = True
        res = super(SaleOrderExtend, self.with_context(ctx)).action_confirm()

        picking_id = self.picking_ids and  self.picking_ids[0]

        # Send Email to the Stock Person
        company_email = self.env.user.company_id.email
        if company_email and picking_id :
            # Custom Email Template
            mail_template = self.env.ref('kin_sales.mail_templ_delivery_transfer_created')
            ctx = {}
            ctx.update({'picking_id':picking_id.id})
            the_url = self._get_url('stock','all_picking','action_picking_tree_all',ctx)
            users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

            for user in users :
                if user.has_group('kin_sales.group_receive_delivery_stock_transfer_email') and user.partner_id.email and user.partner_id.email :
                    ctx = {'system_email': company_email,
                            'stock_person_email':user.partner_id.email,
                            'stock_person_name': user.partner_id.name ,
                            'url':the_url,
                            'origin': picking_id.origin
                        }
                    mail_template.with_context(ctx).send_mail(picking_id.id,force_send=False)
                    self.show_alert_box = True


        # Create Invoice on Ordered Quantity. This should be used for Stock configured with Standard Cost
        is_invoice_before_delivery = self.env.user.company_id.is_invoice_before_delivery
        is_send_invoice_notification = self.env.user.company_id.is_send_invoice_notification


        if is_invoice_before_delivery :
            inv = self.create_customer_invoice()
            # Send Email to the Accountant
            company_email = self.env.user.company_id.email.strip()
            if company_email and  is_send_invoice_notification:
                # Custom Email Template
                mail_template = self.env.ref('kin_sales.mail_templ_invoice_before_delivery')
                ctx = {}
                ctx.update({'invoice_id':inv.id})
                the_invoice_url = self._get_invoice_url('account','menu_action_invoice_tree2','action_invoice_tree2',ctx)
                users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                for user in users :
                    if user.has_group('kin_sales.group_invoice_before_delivery_email') and user.partner_id.email and user.partner_id.email :
                        ctx = {'system_email': company_email,
                                'accountant_email':user.partner_id.email,
                                'accountant_name': user.partner_id.name ,
                                'url':the_invoice_url,
                                'origin' : self.name,
                                'partner_name' : self.partner_id.name
                            }
                        mail_template.with_context(ctx).send_mail(inv.id,force_send=False)

        return res

    @api.multi
    def action_draft(self):
        res = super(SaleOrderExtend, self).action_draft()
        if self.quote_name:
            self.name = self.quote_name
            self.is_credit_limit_bypass = False
        return res


    @api.depends('amount_untaxed')
    def _compute_markup_margin(self):
        for order in self:
            if order.amount_untaxed != 0 :
                total_profit = order.margin
                untaxed_amt = order.amount_untaxed
                order.total_gross_margin_perc = (total_profit / untaxed_amt) * 100
                total_cost = untaxed_amt - total_profit
                if total_cost != 0 :
                    order.total_markup_perc = (total_profit / total_cost) * 100
                order.total_cost = total_cost



    show_alert_box  = fields.Boolean(string="Show Alert Box")
    amt_discount_total = fields.Monetary(string='Discounts', store=True, readonly=True, compute='_amount_all')
    show_alert_box1  = fields.Boolean(string="Show Alert Box1")
    sale_shipping_term_id = fields.Many2one('sale.shipping.term', string='Shipping Term')
    date_order = fields.Datetime(string='Order Date',  required=True, readonly=True, index=True,states={'draft': [('readonly', False),('required',False)], 'sent': [('readonly', False)], 'waiting': [('readonly',False)]}, copy=False)
    date_quote = fields.Datetime(string='Quote Date',  required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    so_name = fields.Char('SO Name')
    quote_name = fields.Char('Quote Name')
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_markup_margin')
    total_gross_margin_perc = fields.Float(string='Gross Margin(%)', digits_compute= dp.get_precision('Product Price'), compute='_compute_markup_margin')
    total_markup_perc = fields.Float(string='Markup(%)',digits_compute= dp.get_precision('Product Price'), compute='_compute_markup_margin')

    credit = fields.Monetary(string='Total Receivable',related='partner_id.credit', store=True)
    not_due_amount_receivable = fields.Monetary(string='Not Due',related='partner_id.not_due_amount_receivable',store=True)
    due_amount_receivable = fields.Monetary(string='Due', related='partner_id.due_amount_receivable',store=True)
    credit_limit = fields.Monetary(string='Credit Limit', related='partner_id.credit_limit',  track_visibility='onchange', store=True)
    allowed_credit = fields.Float(string='Remaining Credit Allowed', related='partner_id.allowed_credit',store=True)
    is_credit_limit_bypass = fields.Boolean(string='Is By Pass Credit limit',default=False,copy=False)
    bypass_msg = fields.Text('Credit Limit By Pass Message')
    bypass_msg_disapproved = fields.Text('Credit Limit Dis-approved reason')
    credit_limit_bypass_requested_by_id = fields.Many2one('res.users',string='Credit Limit by Pass Requested By')
    credit_limit_bypass_confirmed_by_id = fields.Many2one('res.users', string='Credit Limit by Pass Confirmed By')
    credit_limit_bypass_approved_by_id = fields.Many2one('res.users', string='Credit Limit by Pass Approved By')
    warehouse_id = fields.Many2one('stock.warehouse', readonly=False)

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('advance', 'Cash Sales'),
        ('credit', 'Credit Sales'),
        ('sale', 'Sale Order'),
        ('credit_limit_by_pass_request', 'Credit Limit By Pass Request'),
        ('credit_limit_by_pass_confirm','Credit Limit By Pass Confirmed'),
        ('credit_limit_by_pass_approve', 'Credit Limit By Pass Approved'),
        ('credit_limit_by_pass_disapprove', 'Credit Limit By Pass DisApproved'),
        ('credit_limit_by_pass_cancel', 'Credit Limit By Pass Cancelled'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def action_view_invoice(self):
        res = super(SaleOrderExtend,self).action_view_invoice()
        res['target'] = 'new'
        return  res

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderExtend,self)._prepare_invoice()
        if self.env.user.company_id.inv_note and len(self.env.user.company_id.inv_note) > 0 :
            invoice_vals['comment'] = self.env.user.company_id.inv_note
        return  invoice_vals



    def create_customer_invoice(self):

        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        invoice_vals = {
            'name':  '',
            'origin': self.name,
            'type': 'out_invoice',
            'reference': self.client_order_ref or '',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'incoterms_id' : self.incoterm.id or False
        }

        invoice = inv_obj.create(invoice_vals)

        lines = []
        for sale_order_line_id in self.order_line:

            if not float_is_zero(sale_order_line_id.product_uom_qty, precision_digits=precision):
                account = sale_order_line_id.product_id.property_account_income_id or sale_order_line_id.product_id.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (sale_order_line_id.product_id.name, sale_order_line_id.product_id.id, sale_order_line_id.product_id.categ_id.name))

                fpos = sale_order_line_id.order_id.fiscal_position_id or sale_order_line_id.order_id.partner_id.property_account_position_id
                if fpos:
                    account = fpos.map_account(account)

                default_analytic_account = self.env['account.analytic.default'].account_get(sale_order_line_id.product_id.id, sale_order_line_id.order_id.partner_id.id, sale_order_line_id.order_id.user_id.id, time.strftime('%Y-%m-%d'))

                inv_line = {
                        'name': sale_order_line_id.name,
                        'sequence': sale_order_line_id.sequence,
                        'origin': sale_order_line_id.order_id.name,
                        'account_id': account.id,
                        'price_unit': sale_order_line_id.price_unit,
                        'quantity':  sale_order_line_id.product_uom_qty,
                        'discount': sale_order_line_id.discount,
                        'uom_id': sale_order_line_id.product_uom.id,
                        'product_id': sale_order_line_id.product_id.id or False,
                       'invoice_line_tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
                       'account_analytic_id':  sale_order_line_id.order_id.project_id.id  or default_analytic_account and default_analytic_account.analytic_id.id,
                       'invoice_id': invoice.id ,
                       'sale_line_ids': [(6, 0, [sale_order_line_id.id])]   #Never remove this sale_line_ids. This determines the cost of goods sold using the FIFO and not from the product page
                }
                self.env['account.invoice.line'].create(inv_line)


        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if invoice.amount_untaxed < 0:
            invoice.type = 'out_refund'
            # for line in invoice.invoice_line_ids:
            #     line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()

        return invoice


class SalesShippingTerms(models.Model):
    _name = 'sale.shipping.term'

    name = fields.Char(string='Shipping Term')
    description = fields.Text(string='Description')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # @api.multi
    # def _prepare_order_line_procurement(self, group_id=False):
    #     res = super(SaleOrderLine,self)._prepare_order_line_procurement(group_id)
    #     res['po_ref'] = self.order_id.client_order_ref
    #     return res



    @api.model
    def create(self, vals):
        product_id = vals.get('product_id', False)
        if product_id:
            product_obj = self.env['product.product'].browse(product_id)
            description_sale = product_obj.description_sale
            if description_sale and len(description_sale) > 0:
                vals['name'] = description_sale
            else:
                vals['name'] = product_obj.name
            vals['product_uom'] = product_obj.uom_id.id
        res = super(SaleOrderLine, self).create(vals)
        if res.order_id.state in ('sale','cancel','done'):
            raise UserError(_('This Order Line cannot be be added for a confirmed, done or cancelled order'))
        return res

    @api.onchange('discount_amt')
    def _onchange_discount_amt(self):
        for line in self:
            if line.price_unit:
                disc_amt = line.discount_amt
                taxes = line.tax_id.compute_all((line.price_unit-disc_amt), line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)

                #Using write() here does not work.  but direct assignments works, but not suitable,
                # Note that update() is different from Write(). Update(0 method updates on the front end. Similar to what return {'value':{}} does
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


    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        res = super(SaleOrderLine,self)._compute_amount()
        self._onchange_discount()

    def check_order_line_qty_location(self,sale_stock_loc_ids):
        ctx = self.env.context.copy()
        product_obj = self.env['product.product']
        for sale_order_line in self :
            product  = sale_order_line.product_id
            product_id = product.id
            order_line_qty = sale_order_line.product_uom_qty
            qty_available = 0
            if sale_order_line.product_id.type == 'product':
                for location_id in sale_stock_loc_ids :
                    ctx.update({"location":location_id.id})
                    res = product_obj.browse([product_id])[0].with_context(ctx)._product_available()
                    qty_available += res[product_id]['qty_available']

                    order_line_product_qty = self.env['product.uom']._compute_qty_obj(sale_order_line.product_uom, order_line_qty, sale_order_line.product_id.uom_id)
                    if qty_available < order_line_product_qty    :
                        return {product_id:(qty_available,order_line_product_qty)}
        return {}

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product_qty = self.env['product.uom']._compute_qty_obj(self.product_uom, self.product_uom_qty, self.product_id.uom_id)

            if float_compare(self.product_id.virtual_available, product_qty, precision_digits=precision) == -1:

                sale_stock_loc_ids = self.order_id.team_id.sale_stock_location_ids
                res = self.check_order_line_qty_location(sale_stock_loc_ids)
                if res:
                    qty_available = res[self.product_id.id][0]
                    order_line_qty = res[self.product_id.id][1]
                    stck_list = ""
                    for stock_location in sale_stock_loc_ids :
                        stck_list += stock_location.name + ", "
                    stck_list = stck_list.rstrip(', ')
                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message' : _('You plan to sell %.2f %s of %s, but you only have %.2f %s available in the assigned stock location(s) (%s) \n The total stock on hand in the stock location(s) (%s) for %s is %.2f %s.') % \
                            (order_line_qty, self.product_uom.name, self.product_id.name, qty_available, self.product_id.uom_id.name,  stck_list, stck_list, self.product_id.name, qty_available, self.product_id.uom_id.name)
                    }

                    return {'warning': warning_mess}
        return {}



    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine,self).product_id_change()
        vals = {}
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )
        if product.description_sale:
            name = product.description_sale
            vals['name'] = name
            self.update(vals)

        if self.product_id.type == 'product':
            ctx = {}
            product_id = product.id
            qty_available = 0
            product_obj = self.env['product.product']
            sale_stock_loc_ids = self.order_id.team_id.sale_stock_location_ids
            for location_id in sale_stock_loc_ids:
                ctx.update({"location": location_id.id})
                res = product_obj.browse([product_id])[0].with_context(ctx)._product_available()
                qty_available += res[product_id]['qty_available']

            product_qty = self.env['product.uom']._compute_qty_obj(self.product_uom, qty_available,self.product_id.uom_id)
            vals['qty_available'] = product_qty
            self.update(vals)

        return res



    discount_amt = fields.Monetary(string='Disc./ Unit (Amt.)')
    date_order = fields.Datetime(string='Order date',related='order_id.date_order',ondelete='cascade', index=True,store=True)
    qty_available = fields.Float('Qty. Available',readonly=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # @api.model
    # def create(self,vals):
    #     is_customer = vals.get('customer',False)
    #     is_supplier = vals.get('supplier',False)
    #     if is_customer :
    #         vals['ref'] = self.env['ir.sequence'].get('cust_id_code')
    #     elif is_supplier :
    #         vals['ref'] = self.env['ir.sequence'].get('supp_id_code')
    #
    #     return super(ResPartner,self).create(vals)

    @api.model
    def create(self, vals):
        # Check if credit limit has been approved
        credit_limit = vals.get('credit_limit', False)
        if credit_limit:
            vals.update({'is_credit_limit_changed': True, 'is_credit_limit_changed_by': self.env.user.id,
                         'is_credit_limit_approved': False, 'is_credit_limit_last_approved_by': False})
        res = super(ResPartner, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        credit_limit = vals.get('credit_limit', False)

        if self and credit_limit:
            self.is_credit_limit_changed = True
            self.is_credit_limit_changed_by = self.env.user
            self.is_credit_limit_approved = False
            self.is_credit_limit_last_approved_by = False

            # notify superior for price change
            user_ids = []
            group_obj = self.env.ref('kin_sales.group_credit_limit_approval')
            user_names = ''
            for user in group_obj.users:
                user_names += user.name + ", "
                user_ids.append(user.id)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(
                _(
                    'The credit limit field has been changed by %s, from %s to %s, for the partner %s') % (
                    self.env.user.name, self.credit_limit, credit_limit, self.name),
                subject='Credit Limit Field Changed for Partner', subtype='mail.mt_comment')
            self.env.user.notify_info('%s Will Be Notified by Email for the change in credit limit field' % (user_names))

        res = super(ResPartner, self).write(vals)

        return res

    @api.multi
    def btn_approve_credit_limit(self):
        self.is_credit_limit_changed = False
        self.is_credit_limit_changed_by = False
        self.is_credit_limit_approved = True
        self.is_credit_limit_last_approved_by = self.env.user
        user_ids = []

        group_obj = self.env.ref('kin_sales.group_credit_limit_approval')
        user_names = ''
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(
            _(
                'The new credit limit (%s) has been approved by %s, for the partner %s') % (
               self.credit_limit, self.env.user.name, self.name),
            subject='Credit Limit Field Approved for the Partner', subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for the approval of the credit limit' % (user_names))


    # Reference: odoo community aged partner code for getting due amount
    def _get_not_due_amount_receivable(self):
        for partner in self :
            cr = self.env.cr
            partner_id = partner.id
            move_state = 'posted'
            account_type = 'receivable'
            date_from = fields.Date.context_today(self)
            user_company = self.env.user.company_id.id
            future_past = 0
            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state = %s)
                        AND (account_account.internal_type = %s)
                        AND (COALESCE(l.date_maturity,l.date) > %s)\
                        AND (l.partner_id = %s)
                    AND (l.date <= %s)
                    AND l.company_id = %s'''
            cr.execute(query, (move_state,account_type, date_from, partner_id, date_from, user_company))
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount -= partial_line.amount
                future_past += line_amount
            partner.not_due_amount_receivable = future_past

    def _get_due_amount_receivable(self):
        for partner in self:
            partner.due_amount_receivable = partner.credit - partner.not_due_amount_receivable


    def _get_allowed_credit(self):
        for partner in self:
            allowed_credit = partner.credit_limit - partner.due_amount_receivable
            if allowed_credit < 0 :
                partner.allowed_credit = 0
            else :
                partner.allowed_credit = allowed_credit


    name = fields.Char(track_visibility='onchange')
    credit_limit = fields.Monetary(string='Credit Limit')
    is_enforce_credit_limit_so = fields.Boolean(string='Activate Credit Limit')
    due_amount_receivable = fields.Monetary(string='Due',compute=_get_due_amount_receivable,help='Receivables that are Due to be paid')
    not_due_amount_receivable = fields.Monetary(string='Not Due',compute=_get_not_due_amount_receivable,help='Receivables that are Not Due to be Paid')
    allowed_credit = fields.Float(string='Remaining Credit Allowed',compute=_get_allowed_credit,help='Credit Allowance for the partner')
    is_credit_limit_changed = fields.Boolean(string="Is Credit Limit Changed") # no need to track visibilty on this fields, since it generates error for the partner model, when editing access right for users i.e. AttributeError: 'res.users' object has no attribute 'in_group_120
    is_credit_limit_changed_by = fields.Many2one('res.users', string='Credit Limit Changed User')
    is_credit_limit_approved = fields.Boolean(string="Is Credit Limit Approved")
    is_credit_limit_last_approved_by = fields.Many2one('res.users', string='Credit Limit Last Approved User')





