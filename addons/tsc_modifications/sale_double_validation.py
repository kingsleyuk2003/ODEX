# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from openerp import api, fields, models, _
from openerp.exceptions import UserError
from urllib import urlencode
from urlparse import urljoin



class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_disapprove_markup(self, msg):
        reason_for_markup_disapproval = msg
        self.markup_disapproved_by_user_id = self.env.user
        self.state = 'no_sale_approve'

        # Send Email
        company_email = self.env.user.company_id.email.strip()
        markup_disapprove_person_email = self.markup_disapproved_by_user_id.partner_id.email.strip()
        markup_disapprove_person_name = self.markup_disapproved_by_user_id.name

        if company_email and markup_disapprove_person_email:
            # Custom Email Template
            mail_template = self.env.ref('tsc_modifications.mail_templ_sale_markup_disapproved')
            ctx = {}
            ctx.update({'sale_id': self.id})
            the_url = self._get_sale_order_url('sale', 'menu_sale_order', 'action_orders', ctx)

            user_ids = []
            group_obj = self.env.ref('tsc_modifications.group_receive_disapprove_sale_order_markup_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'markup_disapprove_person_name': markup_disapprove_person_name,
                           'markup_disapprove_person_email': markup_disapprove_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url,
                           'reason_for_markup_disapproval': reason_for_markup_disapproval,
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                    self.message_subscribe_users(user_ids=user_ids)
                    # For Similar Odoo Kind of Email. Works fine
                    # self.message_post( _("Sales Order has been Disapproved with reason: " + reason_for_dispproval + "") ,subject='Please See the Disapproved Sales Order', subtype='mail.mt_comment')

                    # Just Log the Note Only
                    self.message_post(_("Sales Order Markup has been Disapproved with reason: " + reason_for_markup_disapproval + ""),
                                      subject='Please See the Disapproved Sales Order Markup')

    @api.multi
    def action_approve_markup(self):
        res = super(SaleOrderExtend,self).action_confirm_subclass()
        self.markup_approved_by_user_id = self.env.user
        self.state = 'so_to_approve_markup_ok'

        # Send Email
        company_email = self.env.user.company_id.email.strip()
        markup_approve_person_email = self.markup_approved_by_user_id.partner_id.email.strip()
        markup_approve_person_name = self.markup_approved_by_user_id.name

        if company_email and markup_approve_person_email:
            # Custom Email Template
            mail_template = self.env.ref('tsc_modifications.mail_templ_sale_markup_approved')
            ctx = {}
            ctx.update({'sale_id': self.id})
            the_url = self._get_sale_order_url('sale', 'menu_sale_order', 'action_orders', ctx)

            user_ids = []
            group_obj = self.env.ref('tsc_modifications.group_receive_approve_sale_order_markup_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'markup_approve_person_name': markup_approve_person_name,
                           'markup_approve_person_email': markup_approve_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                    self.message_subscribe_users(user_ids=user_ids)
        return res



        # Create Invoice on Ordered Quantity. This should be used for Stock configured with Standard Cost
        is_invoice_before_delivery = self.env.user.company_id.is_invoice_before_delivery
        is_send_invoice_notification = self.env.user.company_id.is_send_invoice_notification

        if is_invoice_before_delivery:
            inv = self.create_customer_invoice()
            # Send Email to the Accountant
            company_email = self.env.user.company_id.email.strip()
            if company_email and is_send_invoice_notification:
                # Custom Email Template
                mail_template = self.env.ref('kin_sales.mail_templ_invoice_before_delivery')
                ctx = {}
                ctx.update({'invoice_id': inv.id})
                the_invoice_url = self._get_invoice_url('account', 'menu_action_invoice_tree2', 'action_invoice_tree2',
                                                        ctx)
                users = self.env['res.users'].search(
                    [('active', '=', True), ('company_id', '=', self.env.user.company_id.id)])

                for user in users:
                    if user.has_group(
                            'kin_sales.group_invoice_before_delivery_email') and user.partner_id.email and user.partner_id.email.strip():
                        ctx = {'system_email': company_email,
                               'accountant_email': user.partner_id.email,
                               'accountant_name': user.partner_id.name,
                               'url': the_invoice_url,
                               'origin': self.name,
                               'partner_name': self.partner_id.name
                               }
                        mail_template.with_context(ctx).send_mail(inv.id, force_send=False)

        return res



    # @api.multi
    # def action_approve(self):
    #
    #     if self.state <> 'so_to_approve':
    #         super(SaleOrderExtend, self).action_confirm()
    #     else:
    #         self.state = 'so_to_approve_markup'
    #
    #     self.approved_by_user_id = self.env.user
    #
    #     # Send Email
    #     company_email = self.env.user.company_id.email.strip()
    #     approve_person_email = self.approved_by_user_id.partner_id.email.strip()
    #     approve_person_name = self.approved_by_user_id.name
    #
    #     if company_email and approve_person_email:
    #         # Custom Email Template
    #         mail_template = self.env.ref('kin_sales_double_validation.mail_templ_sale_approved')
    #         ctx = {}
    #         ctx.update({'sale_id': self.id})
    #         the_url = self._get_sale_order_url('sale', 'menu_sale_order', 'action_orders', ctx)
    #
    #         user_ids = []
    #         group_obj = self.env.ref('kin_sales_double_validation.group_receive_approve_sale_order_email')
    #         for user in group_obj.users:
    #             if user.partner_id.email and user.partner_id.email.strip():
    #                 user_ids.append(user.id)
    #                 ctx = {'system_email': company_email,
    #                        'approve_person_name': approve_person_name,
    #                        'approve_person_email': approve_person_email,
    #                        'notify_person_email': user.partner_id.email,
    #                        'notify_person_name': user.partner_id.name,
    #                        'url': the_url
    #                        }
    #                 mail_template.with_context(ctx).send_mail(self.id, force_send=False)
    #                 self.message_subscribe_users(user_ids=user_ids)





    markup_approved_by_user_id = fields.Many2one('res.users', string='Markup Approved By')
    markup_disapproved_by_user_id = fields.Many2one('res.users', string='Markup Disapproved By')

    #This works, but it does not allow my sequence ordering of states
    #state = fields.Selection(selection_add=[('so_to_approve_markup', 'Sale Order Markup To Approve')])
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quote Sent'),
        ('to_confirm', 'Quote to Convert to SO'),
        ('waiting', 'Quote Waiting Conversion to SO'),
        ('so_to_approve', 'SO To Approve'),
        ('sale', 'SO Approved'),
        ('no_sale', 'SO Disapproved'),
        ('so_to_approve_markup','SO Markup To Approve'),
        ('so_to_approve_markup_ok', 'SO Markup Approved'),
        ('no_sale_approve', 'SO Markup Disapproved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

