# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _
from urllib import urlencode
from urlparse import urljoin
from openerp.exceptions import UserError


class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ['draft','to_accept']:
                raise UserError(_('You can only delete draft quotations or Quotations Awaiting Acceptance!'))
            self.env.cr.execute("delete from sale_order where id = %s" % order.id)


    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        res = super(SaleOrderExtend, self).copy(default)
        res.onchange_reach_limit()
        return res

    @api.multi
    def action_send_to_manager(self, msg):
        company_email = self.env.user.company_id.email.strip()
        sender_person_email = self.env.user.partner_id.email.strip()
        sender_person_name = self.env.user.name
        res = {}
        self.state = 'to_accept'

        if company_email and sender_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kin_sales_double_validation.mail_templ_sale_send_to_manager')
            ctx = {}
            ctx.update({'sale_id': self.id})
            the_url = self._get_sale_order_url('sale', 'menu_sale_order', 'action_orders', ctx)

            user_ids = []
            group_obj = self.env.ref('kin_sales_double_validation.group_show_receive_send_to_manager')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'sender_person_name': sender_person_name,
                           'sender_person_email': sender_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url,
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)

                    #Simulates Notification Dialog Box
                    res = {
                        'name': 'Send to Manager Notification',
                        'view_mode': 'form',
                        'res_model': 'send.manager.wizard',
                        'type': 'ir.actions.act_window',
                        'target': 'new'
                    }

        return res


    @api.multi
    def action_disapprove(self,msg):
        reason_for_dispproval = msg
        self.disapproved_by_user_id = self.env.user
        self.state = 'no_sale'

        # Send Email
        company_email = self.env.user.company_id.email.strip()
        disapprove_person_email = self.disapproved_by_user_id.partner_id.email.strip()
        disapprove_person_name = self.disapproved_by_user_id.name

        if company_email and disapprove_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kin_sales_double_validation.mail_templ_sale_disapproved')
            ctx = {}
            ctx.update({'sale_id': self.id})
            the_url = self._get_sale_order_url('sale', 'menu_sale_order', 'action_orders', ctx)

            user_ids = []
            group_obj = self.env.ref('kin_sales_double_validation.group_receive_disapprove_sale_order_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'disapprove_person_name': disapprove_person_name,
                           'disapprove_person_email': disapprove_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url,
                           'reason_for_dispproval': reason_for_dispproval,
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)

            if user_ids :
                self.message_subscribe_users(user_ids=user_ids)
                # For Similar Odoo Kind of Email. Works fine
                #self.message_post( _("Sales Order has been Disapproved with reason: " + reason_for_dispproval + "") ,subject='Please See the Disapproved Sales Order', subtype='mail.mt_comment')

                #Just Log the Note Only
                self.message_post(_("Sales Order has been Disapproved with reason: " + reason_for_dispproval + ""), subject='Please See the Disapproved Sales Order')

    @api.multi
    def action_approve(self):
        res = super(SaleOrderExtend, self).action_confirm()
        self.approved_by_user_id = self.env.user

        # Send Email
        company_email = self.env.user.company_id.email.strip()
        approve_person_email = self.approved_by_user_id.partner_id.email.strip()
        approve_person_name = self.approved_by_user_id.name

        if company_email and approve_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kin_sales_double_validation.mail_templ_sale_approved')
            ctx = {}
            ctx.update({'sale_id': self.id})
            the_url = self._get_sale_order_url('sale', 'menu_sale_order', 'action_orders', ctx)

            user_ids = []
            group_obj = self.env.ref('kin_sales_double_validation.group_receive_approve_sale_order_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'approve_person_name': approve_person_name,
                           'approve_person_email': approve_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
            if user_ids :
                self.message_subscribe_users(user_ids=user_ids)

        return res


    @api.multi
    def action_confirm(self):
        self.state = 'so_to_approve'
        self.confirmed_by_user_id = self.env.user

        # Give a SO ID
        if self.so_name:
            self.name = self.so_name
        else:
            self.quote_name = self.name
            self.name = self.env['ir.sequence'].get('so_id_code')
            self.so_name = self.name

        #Send FYI email notification
        company_email = self.env.user.company_id.email and self.env.user.company_id.email.strip()
        confirm_person_email = self.confirmed_by_user_id.partner_id.email.strip()
        confirm_person_name = self.confirmed_by_user_id.partner_id.name

        if company_email and  confirm_person_email :
            # Custom Email Template
            mail_template = self.env.ref('kin_sales_double_validation.mail_templ_quote_confirmed')
            ctx = {}
            ctx.update({'sale_id':self.id})
            the_url = self._get_sale_order_url('sale','menu_sale_order','action_orders',ctx)

            user_ids = []
            group_obj = self.env.ref('kin_sales_double_validation.group_receive_quotation_confirmed_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {
                            'system_email': company_email,
                            'confirm_person_name': confirm_person_name ,
                            'confirm_person_email' :confirm_person_email,
                            'notify_person_email': user.partner_id.email,
                            'notify_person_name': user.partner_id.name,
                            'url':the_url
                            }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
            if user_ids:
                self.message_subscribe_users(user_ids=user_ids)

            #Send email for approval or disapproval
            mail_template = self.env.ref('kin_sales_double_validation.mail_templ_quote_confirmed_to_approve')
            user_ids = []
            group_obj = self.env.ref('kin_sales_double_validation.group_receive_quotation_confirmed_email_to_approve')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {
                        'system_email': company_email,
                        'confirm_person_name': confirm_person_name,
                        'confirm_person_email': confirm_person_email,
                        'notify_person_email': user.partner_id.email,
                        'notify_person_name': user.partner_id.name,
                        'url': the_url
                    }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
            if user_ids :
                self.message_subscribe_users(user_ids=user_ids)

        return

    # It acts as a helper for other sub classess to call the parent action_confirm() method
    @api.multi
    def action_confirm_subclass(self):
        res = super(SaleOrderExtend, self).action_confirm()

    @api.multi
    def action_cancel(self):
        res = super(SaleOrderExtend,self).action_cancel()

        #Send Email
        company_email = self.env.user.company_id.email.strip()
        sales_person_email = self.user_id.partner_id.email.strip()
        confirm_person_email = self.env.user.partner_id.email.strip()

        if company_email and sales_person_email and confirm_person_email and  (sales_person_email != confirm_person_email ):
            # Custom Email Template
            mail_template = self.env.ref('kin_sales_double_validation.mail_templ_sale_canceled')
            ctx = {}
            ctx.update({'sale_id':self.id})
            the_url = self._get_sale_order_url('sale','menu_sale_order','action_orders',ctx)

            ctx = {'system_email': company_email,
                    'confirm_person_name': self.env.user.name ,
                    'confirm_person_email' :confirm_person_email,
                    'url':the_url
                    }
            mail_template.with_context(ctx).send_mail(self.id,force_send=False)
        return res

    def onchange_reach_limit(self):
        for order in self:
            amount_total = order.amount_total
            sale_confirm_limit = self.env.user.sale_confirm_limit
            is_use_sale_confirm_limit = self.env.user.is_use_sale_confirm_limit
            if (amount_total < sale_confirm_limit) and is_use_sale_confirm_limit  and  order.state in ['draft','sent','to_accept']:
                self.env.cr.execute("update sale_order set state = 'so_to_approve' where id = %s" % (self.id))
            elif ((amount_total >= sale_confirm_limit) and is_use_sale_confirm_limit and order.state in ['draft','sent']) :
                self.env.cr.execute("update sale_order set state = 'to_accept' where id = %s" % (self.id))
        return



    @api.model
    def create(self, vals):
        order = super(SaleOrderExtend, self).create(vals)
        return order

    def _get_sale_order_url(self, module_name,menu_id,action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name,menu_id)[1]
        fragment['model'] =  'sale.order'
        fragment['view_type'] = 'form'
        fragment['action']= model_data.get_object_reference(module_name,action_id)[1]
        query = {'db': self.env.cr.dbname}

# for displaying tree view. Remove if you want to display form view
#         fragment['page'] = '0'
#         fragment['limit'] = '80'
#         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


 # For displaying a single record. Remove if you want to display tree view

        fragment['id'] =  context.get("sale_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res

    @api.multi
    def action_send_for_confirm(self):

        for order in self:
            order.state = 'waiting'
            order.is_show_btn_send_for_confirm = False
            order.is_show_btn_approve = False
            order.is_show_btn_confirm = True

            is_po_check = order.env.user.company_id.is_po_check
            # is PO Check
            if is_po_check:
                if order.client_order_ref:
                    client_order_ref = order.client_order_ref.strip()

                    if len(client_order_ref) <= 0:
                        raise UserError(
                            'Please Ensure that the Quote is confirmed from the customer and that the PO reference is set. e.g. you may put the po number, email, contact name, number of the customer that confirmed the Quote on the PO reference field')

                else:
                    raise UserError(
                        'Please Ensure that the Quote is confirmed from the customer and that the PO reference is set. e.g. you may put the po number, email, contact name, number of the customer that confirmed the Quote')

            #Send Email
            company_email = order.env.user.company_id.email and order.env.user.company_id.email.strip()
            sales_person_email = order.user_id.partner_id.email.strip()

            if company_email and sales_person_email  :
                # Custom Email Template
                mail_template = order.env.ref('kin_sales_double_validation.mail_templ_send_for_confirmation')
                ctx = {}
                ctx.update({'sale_id':order.id})
                the_url = order._get_sale_order_url('sale','menu_sale_order','action_orders',ctx)

                user_ids = []
                group_obj = self.env.ref('kin_sales_double_validation.group_receive_send_for_confirm_email')
                for user in group_obj.users :
                    if user.partner_id.email and user.partner_id.email.strip() :
                        user_ids.append(user.id)
                        ctx = {'system_email': company_email,
                                'confirm_person_email':user.partner_id.email,
                                'confirm_person_name': user.partner_id.name ,
                                'url':the_url
                                }
                        mail_template.with_context(ctx).send_mail(order.id,force_send=False)

                if user_ids :
                    order.message_subscribe_users(user_ids=user_ids)

                #self.message_post( _('Sales Order has been created %s.') % (self.name),subject='Please See the Created Sales Order', subtype='mail.mt_comment')

    partner_id = fields.Many2one(states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'to_accept': [('readonly', False)], 'waiting': [('readonly', False)], 'so_to_approve': [('readonly', False)]})
    partner_invoice_id = fields.Many2one(states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'to_accept': [('readonly', False)], 'waiting': [('readonly', False)], 'so_to_approve': [('readonly', False)]}, track_visibility='always')
    partner_shipping_id = fields.Many2one(states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'to_accept': [('readonly', False)], 'waiting': [('readonly', False)], 'so_to_approve': [('readonly', False)]}, track_visibility='always')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True,
                                   states={'draft': [('readonly', False)],'to_accept': [('readonly', False)], 'sent': [('readonly', False)]},
                                   help="Pricelist for current sales order.")
    #state = fields.Selection(selection_add=[('waiting', 'Waiting Approval')]) # it worked but , i could not sequence it
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quote Sent'),
        ('to_accept', 'Quote Awaiting Acceptance'),
        ('waiting', 'Quote Awaiting Conversion to SO'),
        ('so_to_approve', 'Sale Order To Approve'),
        ('sale', 'Sale Order Approved'),
        ('no_sale', 'Sale Order Disapproved'),
        ('credit_limit_by_pass_request', 'Credit Limit By Pass Request'),
        ('credit_limit_by_pass_confirm', 'Credit Limit By Pass Confirmed'),
        ('credit_limit_by_pass_approve', 'Credit Limit By Pass Approved'),
        ('credit_limit_by_pass_disapprove', 'Credit Limit By Pass DisApproved'),
        ('credit_limit_by_pass_cancel', 'Credit Limit By Pass Cancelled'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    confirmed_by_user_id = fields.Many2one('res.users',string= 'Confirmed By')
    approved_by_user_id = fields.Many2one('res.users', string='Approved By')
    disapproved_by_user_id = fields.Many2one('res.users', string='Disapproved By')
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False), ('required', False)],
                                         'sent': [('readonly', False)], 'waiting': [('readonly', False)],
                                         'so_to_approve': [('readonly', False)]}, copy=False)




class ResUsersExtend(models.Model):
    _inherit = 'res.users'

    sale_confirm_limit = fields.Float('Sales Confirmation Limit',help='If user exceeds this limit, expose the confirmation button for validation')
    is_use_sale_confirm_limit = fields.Boolean('Use Sales Confirm Limit')

