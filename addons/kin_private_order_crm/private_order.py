# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp import SUPERUSER_ID

class PrivateOrder(models.Model):

    _name = 'private.order'
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    @api.model
    def _get_default_team(self):
        default_team_id = self.env['crm.team']._get_default_team_id()
        return self.env['crm.team'].browse(default_team_id)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('private.order') or 'New'
        return super(PrivateOrder,self).create(vals)

    @api.model
    def _get_default_team(self):
        default_team_id = self.env['crm.team']._get_default_team_id()
        return self.env['crm.team'].browse(default_team_id)

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in 'draft':
                raise UserError(_("Cannot delete Order that is not in draft state."))
        return super(PrivateOrder, self).unlink()

    @api.multi
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        orders.write({
            'state': 'draft'
        })


    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_confirm(self):
        user_ids = []
        group_obj = self.env.ref('kin_private_order_crm.group_show_private_order_manager')
        for user in group_obj.users:
            user_ids.append(user.id)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_('A New Private Order from Sales Person %s has been Created for %s.') % (
            self.user_id.name, self.name),
                                subject='A New Private Order  has been Created ', subtype='mail.mt_comment')

        return self.write({'state': 'sale'})

    @api.multi
    def button_dummy(self):
        return True

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New Private Order'))
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that generated this sales order request.")
    client_order_ref = fields.Char(string='Customer Reference', copy=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sale', 'Private Sale Order'),
        ( 'cancel','Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False,
                                 default=fields.Datetime.now)

    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user,required=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True, default=_get_default_team,
                              oldname='section_id')
    partner_id = fields.Many2one('private.customer', string='Private Customer', readonly=True,
                                 states={'draft': [('readonly', False)]}, required=True,
                                 change_default=True, index=True, track_visibility='always')

    order_line = fields.One2many('private.order.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)

    currency_id = fields.Many2one("res.currency", string="Currency", required=True,default=lambda self: self.env.user.company_id.currency_id.id)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',track_visibility='always')


class PrivateOrderLine(models.Model):
    _name = 'private.order.line'

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.category_id.id != self.product_uom.category_id.id):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if  self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id,
                                                                                 self.tax_id)
        self.update(vals)
        return {'domain': domain}

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            line.tax_id = line.product_id.taxes_id if line.product_id.taxes_id else False

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom:
            self.price_unit = 0.0
            return
        if self.order_id.partner_id:
            product = self.product_id.with_context(
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                uom=self.product_uom.id
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id,
                                                                              self.tax_id)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    order_id = fields.Many2one('private.order', string='Order Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    price_reduce = fields.Monetary(compute='_get_price_reduce', string='Price Reduce', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes')

    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)

    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sale', 'Private Sale Order'),
         ('cancel','Cancel')
    ],default='draft')



class CustomerType(models.Model):
    _name = 'customer.type'

    name = fields.Char('Customer Type')

class PrivateCustomer(models.Model):
    _name = 'private.customer'

    @api.multi
    def action_view_order(self):
        private_order_ids = self.mapped('private_order_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('kin_private_order_crm.action_private_orders')
        list_view_id = imd.xmlid_to_res_id('kin_private_order_crm.view_private_order_tree')
        form_view_id = imd.xmlid_to_res_id('kin_private_order_crm.view_private_order_form')

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
        if len(private_order_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % private_order_ids.ids
        elif len(private_order_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = private_order_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    def _get_orders(self):
        private_order_ids = self.env['private.order'].search([('partner_id', '=', self.id)])

        self.update({
                'order_count': len(set(private_order_ids.ids)),
                'private_order_ids': private_order_ids.ids ,
            })

    @api.model
    def _lang_get(self):
        languages = self.env['res.lang'].search([])
        return [(language.code, language.name) for language in languages]

    name = fields.Char('Company Name')
    contact_person = fields.Char('Contact Person')
    commence_date = fields.Date('Date of Commencement')
    business_mode = fields.Selection([('credit', 'Credit'), ('cash', 'Cash'),('pod','Pay on Delivery')], string='Mode of Business')
    payment_mode = fields.Selection([('cash', 'Cash'), ('cheque', 'Cheque'), ('cash_cheque', 'Cash/Cheque')], string='Mode of Payment')
    payment_schedule = fields.Selection([('full', 'Full Payment'), ('installment', 'Installmental Payment')], string='Payment Schedule')
    payment_duration = fields.Selection([('day', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], string='Payment Duration')
    address = fields.Text('Address')
    mobile = fields.Char('Phone/Mobile No.')
    email = fields.Char('Email')
    customer_type = fields.Many2many('customer.type', string='Customer Type')
    potential = fields.Selection([('low', 'Low'), ('average', 'Average'), ('high', 'High')], string='Potential')
    function = fields.Char('Job Position')
    active = fields.Boolean('Active',default=True)
    user_id = fields.Many2one('res.users',string='Sales Person',default=lambda self: self.env.user.id)
    # category_ids = fields.Many2many('res.partner.category', id1='partner_id_private', id2='category_id_private', string='Categories')
    order_count = fields.Integer(string='# of Orders', compute='_get_orders', readonly=True)
    private_order_ids = fields.One2many("private.order", string='Private Orders', compute="_get_orders", readonly=True, copy=False)
    lang = fields.Selection(_lang_get, 'Language',
                             help="If the selected language is loaded in the system, all documents related to this contact will be printed in this language. If not, it will be English.")



class MarketingAppointment(models.Model):
    _name = 'marketing.appointment'

    name = fields.Char('Next Appointment')


class MarketingOutcome(models.Model):
    _name = 'marketing.outcome'

    name =  fields.Char('Marketing Outcome')


class MarketingProduct(models.Model):
    _name = 'marketing.product'

    name = fields.Char('Product Detailed')


class MarketingSpeciality(models.Model):
    _name = 'marketing.speciality'

    name = fields.Char('Speciality')


class MarketingTerritory(models.Model):
    _name = 'marketing.territory'

    name =  fields.Char('Address/Institution')

class ActivityType(models.Model):
    _name = 'activity.type'

    name = fields.Char('Activity Type')


class MarketingActivity(models.Model):
    _name = 'marketing.activity'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('Name')
    mobile = fields.Char('Phone/Mobile No.')
    territory_id = fields.Many2one('marketing.territory','Territory')
    speciality_id = fields.Many2one('marketing.speciality', 'Speciality')
    product_id = fields.Many2one('marketing.product', 'Product')
    outcome_id = fields.Many2one('marketing.outcome', 'Outcome')
    appointment_id = fields.Many2one('marketing.appointment', 'Next Appointment')
    activity_type_id = fields.Many2one('activity.type','Activity Type')
    next_app_date = fields.Date('Next Appointment Date')
    date = fields.Date('Date')
    description = fields.Text('Description')
    user_id = fields.Many2one('res.users', string='Sales Person', default=lambda self: self.env.user.id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Confirmed'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')




    @api.model
    def create(self, vals):
        mk_obj = super(MarketingActivity, self).create(vals)
        user_ids = []
        group_obj = self.env.ref('kin_private_order_crm.group_show_private_order_manager')
        for user in group_obj.users:
            user_ids.append(user.id)
            mk_obj.message_subscribe_users(user_ids=user_ids)
            mk_obj.message_post( _('A New Marketing Activity has been Created for %s.') % (mk_obj.name),subject='A New Marketing Activity has been Created ', subtype='mail.mt_comment')

        return mk_obj

    @api.multi
    def unlink(self):
        for mk in self:
            if mk.state not in 'draft':
                raise UserError(_("Cannot delete Activity that is not in draft state."))
        return super(MarketingActivity, self).unlink()

    @api.multi
    def action_draft(self):
        mk = self.filtered(lambda s: s.state in ['cancel'])
        mk.write({
            'state': 'draft'
        })

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_confirm(self):
        self.write({'state': 'done'})
