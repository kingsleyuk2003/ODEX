# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from datetime import datetime, time, timedelta
from openerp import api, fields, models, _
from urllib import urlencode
from urlparse import urljoin
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT






class produce_price_sale_history(models.Model):
    """
    Keep track of the ``product.template`` standard prices as they are changed.
    """

    _name = 'product.sale.price.history'
    _rec_name = 'date_change'
    _order = 'date_change desc'


    company_id = fields.Many2one('res.company', required=True,default=lambda self: self.env.user.company_id.id, string='Company')
    product_id =  fields.Many2one('product.product', 'Product', required=True, ondelete='cascade')
    price =  fields.Float('Sale Price')
    pricelist_id = fields.Many2one('product.pricelist',string='Price List')
    user_id = fields.Many2one('res.users', string='Last Changed By')
    date_change = fields.Datetime(string='Last Changed Date', default=lambda self: datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    prev_price = fields.Float(string='Previous Price')
    uom_id =  fields.Many2one(string='Unit',related='product_id.uom_id')



class ProductProductExtend(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        context = self.env.context
        ctx = dict(context or {}, create_product_product=True)
        product_id = super(ProductProductExtend, self).create(vals)
        self.with_context(ctx)._set_sales_price(product_id, vals.get('list_price', 0.0))
        return product_id

    @api.multi
    def write(self,vals):
        res = super(ProductProductExtend, self).write(vals)
        if 'list_price' in vals:
            for product_id in self:
                self._set_sales_price(product_id, vals.get('list_price', 0.0))
        return res


    def _set_sales_price(self, product_id, value):
        ctx = self.env.context or {}
        price_cost_history_obj = self.env['product.sale.price.history']
        user_company = self.env.user.company_id.id
        company_id = ctx.get('force_company', user_company)
        user = self.env.user.id
        date = datetime.today()
        prev_price = self.lst_price
        price_cost_history_obj.with_context(ctx).create(
                {
                'product_id': product_id.id,
                'price': value,
                'company_id': company_id,
                'user_id': user,
                'date_change': date,
                'prev_price': prev_price
                }
        )

    product_cost_price_history_ids = fields.One2many('product.price.history','product_id',string='Product Price History')
    product_sale_price_history_ids = fields.One2many('product.sale.price.history', 'product_id', string='Product Sales Price History')





class ProductPricelistExtend(models.Model):

    _inherit = 'product.pricelist'

    operating_unit_id = fields.Many2one('operating.unit',string='Operating Unit')


class PricelistItem(models.Model):

    _inherit = 'product.pricelist.item'


    uom_id = fields.Many2one(related='product_id.uom_id', string='Unit of Measure')
    # categ_id = fields.Many2one(related='product_id.categ_id', string='Product Category')
    user_id = fields.Many2one('res.users',string='Last Changed By')
    date_change = fields.Datetime(string='Last Changed Date', default=lambda self: datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    prev_price = fields.Float(string='Previous Price')
    applied_on = fields.Selection([('3_global', 'Global'), ('2_product_category', ' Product Category'), ('0_product_variant', 'Product')], string="Apply On", required=True, help='Pricelist Item applicable on selected option')


    @api.model
    def create(self, vals):
        user = self.env.user.id
        vals.update({'user_id':user})
        res = super(PricelistItem,self).create(vals)
        product_id = vals.get('product_id', False)
        fixed_price = vals.get('fixed_price',0)
        pricelist_id = vals.get('pricelist_id',False)
        is_product = vals.get('applied_on',False)
        compute_price = vals.get('compute_price', False)
        if product_id and pricelist_id and is_product == '0_product_variant' and compute_price == 'fixed' :
            self._set_sales_price(product_id,fixed_price,pricelist_id)
        return res

    @api.multi
    def write(self, vals):
        user = self.env.user.id
        fixed_price = vals.get('fixed_price', 'nil')
        prev_price = self.fixed_price
        vals.update({'user_id': user,'date_change':datetime.today().strftime('%Y-%m-%d %H:%M:%S')})
        product_id = vals.get('product_id', False)
        if not product_id:
            product_id = self.product_id.id or False
        if product_id and fixed_price == 'nil' :
            fixed_price = prev_price
        if fixed_price != 'nil':
            vals.update({'prev_price':prev_price})
            pricelist_id = self.pricelist_id or False
            is_product = vals.get('applied_on',False)
            if not is_product :
                is_product = self.applied_on
            compute_price = vals.get('compute_price',False)
            if not compute_price:
                compute_price = self.compute_price
            if product_id and pricelist_id and  is_product == '0_product_variant' and compute_price == 'fixed' :
                self._set_sales_price(product_id, fixed_price, pricelist_id.id)

        res = super(PricelistItem, self).write(vals)
        return res


    def _set_sales_price(self, product_id, value,pricelist_id):
        ctx = self.env.context or {}
        price_cost_history_obj = self.env['product.sale.price.history']
        user_company = self.env.user.company_id.id
        company_id = ctx.get('force_company', user_company)
        user = self.env.user.id
        prev_price = self.fixed_price
        price_cost_history_obj.with_context(ctx).create(
                {
                'product_id': product_id,
                'price': value,
                'company_id': company_id,
                'user_id': user,
                'prev_price': prev_price,
                 'pricelist_id': pricelist_id,
                }
        )


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'


    def _get_url(self, module_name, menu_id, action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name, menu_id)[1]
        fragment['model'] = 'product.template'
        fragment['view_type'] = 'form'
        fragment['action'] = model_data.get_object_reference(module_name, action_id)[1]
        query = {'db': self.env.cr.dbname}
        # for displaying tree view. Remove if you want to display form view
        #         fragment['page'] = '0'
        #         fragment['limit'] = '80'
        #         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


        # For displaying a single record. Remove if you want to display tree view
        fragment['id'] = context.get("product_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res

    @api.model
    def create(self,vals):
        res = super(ProductTemplateExtend,self).create(vals)
        #notify the group people
        # Send Email
        company_email = self.env.user.company_id.email.strip()
        product_person_email = self.env.user.partner_id.email.strip()
        product_person_name = self.env.user.name


        if company_email and product_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kin_product.mail_templ_create_product_email')
            ctx = {}
            ctx.update({'product_id': res.id})
            the_url = self._get_url('product', 'menu_product_template_action', 'product_template_action_product', ctx)

            user_ids = []
            group_obj = self.env.ref('kin_product.group_receive_create_product_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'product_person_name': product_person_name,
                           'product_person_email': product_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url,
                           'obj' : res,
                           }
                    mail_template.sudo().with_context(ctx).send_mail(self.id, force_send=False)
        return res

    # It repeats sending of email for the each edit for the fields. So no need
    # @api.multi
    # def write(self, vals):
    #     res = super(ProductTemplateExtend, self).write(vals)
    #     # notify the group people
    #     # Send Email
    #     company_email = self.env.user.company_id.email.strip()
    #     product_person_email = self.env.user.partner_id.email.strip()
    #     product_person_name = self.env.user.name
    #
    #     if company_email and product_person_email:
    #         # Custom Email Template
    #         mail_template = self.env.ref('kin_product.mail_templ_edit_product_email')
    #         ctx = {}
    #         ctx.update({'product_id': self.id})
    #         the_url = self._get_url('product', 'menu_product_template_action', 'product_template_action_product', ctx)
    #
    #         user_ids = []
    #         group_obj = self.env.ref('kin_product.group_receive_edit_product_email')
    #         for user in group_obj.users:
    #             if user.partner_id.email and user.partner_id.email.strip():
    #                 user_ids.append(user.id)
    #                 ctx = {'system_email': company_email,
    #                        'product_person_name': product_person_name,
    #                        'product_person_email': product_person_email,
    #                        'notify_person_email': user.partner_id.email,
    #                        'notify_person_name': user.partner_id.name,
    #                        'url': the_url
    #                        }
    #                 mail_template.with_context(ctx).send_mail(self.id, force_send=True)
    #     return res

    @api.multi
    def unlink(self):
        for rec in self:
            # notify the group people
            # Send Email
            company_email = rec.env.user.company_id.email.strip()
            product_person_email = rec.env.user.partner_id.email.strip()
            product_person_name = rec.env.user.name

            if company_email and product_person_email:
                # Custom Email Template
                mail_template = rec.env.ref('kin_product.mail_templ_delete_product_email')
                ctx = {}
                # ctx.update({'product_id': self.id})
                # the_url = self._get_url('product', 'menu_product_template_action', 'product_template_action_product', ctx)

                user_ids = []
                group_obj = rec.env.ref('kin_product.group_receive_delete_product_email')
                for user in group_obj.users:
                    if user.partner_id.email and user.partner_id.email.strip():
                        user_ids.append(user.id)
                        ctx = {'system_email': company_email,
                               'product_person_name': product_person_name,
                               'product_person_email': product_person_email,
                               'notify_person_email': user.partner_id.email,
                               'notify_person_name': user.partner_id.name,
                               # 'url': the_url
                               }
                        mail_template.with_context(ctx).send_mail(rec.id, force_send=True) #You have to force send at this point, because the specific record will be deleted soon
        return super(ProductTemplateExtend, self).unlink()


    @api.model
    def run_min_alert_qty_check(self):

        # settings_obj = self.env['sale.config.settings']
        # is_send_stock_notification  = settings_obj.search([('is_send_stock_notification', '=', True)], limit=1)
        is_send_stock_notification  = self.env.user.company_id.is_send_stock_notification
        if  is_send_stock_notification :
            product_obj = self.env['product.product']
            stock_location_obj = self.env['stock.location']
            ctx = self.env.context.copy()

            the_date = datetime.today().strftime('%d-%m-%Y %H:%M:%S')
            msg = "<style> " \
                    "table, th, td {" \
                    "border: 1px solid black; " \
                    "border-collapse: collapse;" \
                    "}" \
                    "th, td {" \
                    "padding-left: 5px;"\
                    "}" \
                    "</style>"
            msg += "<p>Hello,</p>"
            msg += "<p>Please see the Minimum Stock Notification as at %s</p><p></p>"  % (the_date)
            msg += "<table width='100%' >"

            at_least_one = False
            stock_locations = stock_location_obj.search([('usage','=','internal')])
            products = product_obj.search([])

            for stock_location in stock_locations :
                count = 0
                msg +=  "<tr><td colspan='5' align='center' style='margin:35px' ><h2>"+ stock_location.name +"</h2></td></tr>" \
                 "<tr align='left' ><th>S/N</th><th>Product Name</th><th>Unit</th><th>Min. Alert Qty</th><th>Qty. Available</th></tr>"

                ctx.update({'location':stock_location.id})
                for product in products :
                    min_alert_qty = product.min_alert_qty
                    is_included_in_min_alert_qty = product.is_included_in_min_alert_qty
                    product_id = product.id
                    product_name = product.name
                    product_uom = product.uom_id.name
                    res = product_obj.browse([product_id]).with_context(ctx)._product_available()
                    qty_available = res[product_id]['qty_available']
                    if (qty_available <= min_alert_qty) and is_included_in_min_alert_qty:
                        count += 1
                        at_least_one = True
                        msg += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (count,product_name,product_uom,min_alert_qty,qty_available)

            msg += "</table> <p></p><p>You may manually create purchase order for the listed items, to replenish the stock</p>" \
				  "<p>Regards and Thanks</p>" \
				  "<p>This is an autogenerated message from %s ERP System</p>" % (self.env.user.company_id.name)


            #Send Email
            company_email = self.env.user.company_id.email.strip()
            if company_email and at_least_one :
                # Custom Email Template
                #mail_template = self.env.ref('kin_sales.mail_templ_min_alert_stock_level')
                users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                for user in users :
                    if user.has_group('kin_stock.group_minimum_stock_notification_email') and user.partner_id.email and user.partner_id.email.strip() :
                        # ctx = {'system_email': company_email,
                        #         'user_email':user.partner_id.email,
                        #         'partner_name': user.partner_id.name ,
                        #         'msg' : msg,
                        #         'the_date' : the_date ,
                        #        }
                        #Not used because it renders the raw html table rather than evaluating the html
                        #mail_template.with_context(ctx).send_mail(self.id,force_send=False)

                        #Send Email
                        mail_obj = self.env['mail.mail']
                        mail_data = {
                            'model': 'product.template',
                            'res_id': self.id,
                            'record_name': 'Minimum Alert Stock Level',
                            'email_from': company_email,
                            'reply_to': company_email,
                            'subject': "Minimum Stock Level Notification for the date %s" % (the_date),
                            'body_html': '%s' % msg,
                            'auto_delete': True,
                            #'recipient_ids': [(4, id) for id in new_follower_ids]
                            'email_to': user.partner_id.email
                        }
                        mail_id = mail_obj.create(mail_data)
                        mail_obj.send([mail_id])


            return True


    name = fields.Char('Name', required=True, translate=True, select=True,track_visibility = "onchange")
    description_sale =  fields.Text('Sale Description', translate=True,
                                    help="A description of the Product that you want to communicate to your customers. "
                                         "This description will be copied to every Sale Order, Delivery Order and Customer Invoice/Refund",
                                    track_visibility="onchange"
                                    )

    description_purchase = fields.Text('Purchase Description', translate=True,
                                        help="A description of the Product that you want to communicate to your vendors. "
                                             "This description will be copied to every Purchase Order, Receipt and Vendor Bill/Refund.",
                                        track_visibility = "onchange")

    description_picking = fields.Text('Description on Picking', translate=True,track_visibility = "onchange")
    min_alert_qty = fields.Float(string='Minimum Alert Qty.', help="Minimum Alert Qty. for the Item to be Included in the Notification Report")
    is_included_in_min_alert_qty = fields.Boolean(string="Include M.A.Q. in Notif.", help="Include this product in the email message that is sent sent by the scheduler")


class ProductCategoryExtend(models.Model):
    _name = "product.category"
    _inherit = ["product.category","mail.thread"]

    name = fields.Char(track_visibility='onchange')
    parent_id = fields.Many2one(track_visibility='onchange')
    type = fields.Selection(track_visibility='onchange')
    property_account_income_categ_id  = fields.Many2one(track_visibility='onchange',company_dependent=True)
    property_account_expense_categ_id  = fields.Many2one(track_visibility='onchange',company_dependent=True)
    disc_acct_analytic_purchase_id = fields.Many2one(track_visibility='onchange')
    disc_acct_analytic_sale_id = fields.Many2one(track_visibility='onchange')

    #New api way of creating property fields is to set company_dependent=True
    property_stock_journal = fields.Many2one('account.journal', company_dependent=True,track_visibility='onchange')
    property_valuation = fields.Selection(track_visibility='onchange',company_dependent=True)
    property_cost_method = fields.Selection(track_visibility='onchange',company_dependent=True)
    property_stock_journal = fields.Many2one(track_visibility='onchange',company_dependent=True)
    property_stock_account_input_categ_id = fields.Many2one(track_visibility='onchange',company_dependent=True)
    property_stock_account_output_categ_id = fields.Many2one(track_visibility='onchange',company_dependent=True)
    property_stock_valuation_account_id = fields.Many2one(track_visibility='onchange',company_dependent=True)
    # route_ids = fields.Many2one(track_visibility='onchange')
    removal_strategy_id = fields.Many2one(track_visibility='onchange')
    property_account_creditor_price_difference_categ = fields.Many2one(company_dependent=True,track_visibility='onchange')
    property_inventory_revaluation_increase_account_categ = fields.Many2one(company_dependent=True,track_visibility='onchange')
    property_inventory_revaluation_decrease_account_categ = fields.Many2one(company_dependent=True,track_visibility='onchange')