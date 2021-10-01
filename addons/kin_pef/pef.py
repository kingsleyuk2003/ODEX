# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp import SUPERUSER_ID
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_is_zero, float_compare,float_round, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
from openerp.tools import amount_to_text
from dateutil.relativedelta import relativedelta
from datetime import *


class NNPCReceivingPEFDepot(models.Model):
    _name = 'kin.receiving.pef.depot'

    name = fields.Char('Name of Receiving PEF Depot')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one('res.country.state',string='State')
    address = fields.Char('Address')
    retail_station_ids = fields.One2many('kin.retail.pef.station', 'receiving_depot_id', string='Retail Stations')
    bridging_rate_from_depot_ids = fields.One2many('kin.bridging.rate','from_depot_id',string='From Depot Bridging Rate')
    bridging_rate_to_depot_ids = fields.One2many('kin.bridging.rate', 'to_depot_id', string='To Depot Bridging Rate')


class RetailStation(models.Model):
    _name = 'kin.retail.pef.station'

    name = fields.Char('Retail Station Name')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one('res.country.state', 'State')
    address = fields.Char('Address')
    receiving_depot_id = fields.Many2one('kin.receiving.pef.depot', string='Receiving Depot')
    partner_id = fields.Many2one('res.partner',string='Retail Station Account')
    zone = fields.Char(string='Zone')
    contribution_rate = fields.Float('Contribution Rate')
    nta_rate = fields.Float(string='NTA Rate')
    pef_register_ids = fields.One2many('kin.pef.register','retail_station_id',string='PEF Registers')
    partner_ids = fields.One2many('res.partner', 'retail_station_pef_id', string='Partners')


class BridgingRate(models.Model):
    _name = 'kin.bridging.rate'

    from_depot_id = fields.Many2one('kin.receiving.pef.depot',string='From Depot')
    to_depot_id = fields.Many2one('kin.receiving.pef.depot',string='To Depot')
    bridging_rate = fields.Float(string='Bridging Rate')


class PEFRegister(models.Model):
    _name = 'kin.pef.register'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'PEF Register'


    def _compute_invoice_count(self):
        self.invoice_count = len(self.invoice_id)


    @api.multi
    def action_view_invoice(self):
        invoice_id = self.mapped('invoice_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'target': 'new'
        }
        if len(invoice_id) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_id.id
        elif len(invoice_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    def create_invoice(self,rate=0,qty=0,inv_type='out_invoice'):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        company = self.env.user.company_id
        partner_pef_id = company.partner_pef_id
        if not partner_pef_id :
            raise UserError(_("Please Set the PEF Entity in this Companies' Configuration Page"))

        if not company.product_id :
            raise UserError(_("Please Set the PEF Accounting Product in this Companies' Configuration Page"))


        invoice_vals = {
            'name': self.waybill_no + " , " + self.name or '',
            'origin': self.waybill_no + " , " + self.name or '',
            'type': inv_type,
            'reference': self.waybill_no or self.name,
            'account_id': partner_pef_id.property_account_receivable_id.id,
            'partner_id': partner_pef_id.id,
            'journal_id': journal_id,
            'is_pef_invoice': True,
            # 'company_id': sale_order.company_id.id,
            'user_id': self.env.user.id,
        }

        invoice = inv_obj.create(invoice_vals)

        lines = []

        if not float_is_zero(1, precision_digits=precision):
            account = company.product_id.property_account_income_id or company.product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(
                    _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                        company.product_id.name, company.product_id.id,
                        company.product_id.categ_id.name))


            default_analytic_account = self.env['account.analytic.default'].account_get(
                company.product_id.id, partner_pef_id.id,
                self.env.user.id, date.today())

            inv_line = {
                'name': self.waybill_no,
                # 'sequence': self.sequence,
                'origin': self.waybill_no,
                'account_id': account.id,
                'price_unit': rate,
                'quantity': qty,
                'uom_id': company.product_id.uom_id.id,
                'product_id': company.product_id.id or False,
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
        group_obj = self.env.ref('account.group_account_invoice')
        for user in group_obj.users:
            user_ids.append(user.id)
            invoice.message_unsubscribe_users(user_ids=user_ids)
            invoice.message_subscribe_users(user_ids=user_ids)
            invoice.message_post(_(
                'A New PEF Invoice has been created from  %s for the PEF Clearance Document with Waybill number %s.') % (
                                  self.env.user.name, self.waybill_no),
                              subject='A New PEF Invoice has been created ', subtype='mail.mt_comment')
        return invoice


        # ../odoo-9.0/addons/custom/mine/kin_pef/pef.py:188
        # store=True allows the field to be computed ONCE and saved, except you use the @api.depends() to recompute it and always use the self.UPDATE() to update the interface rather than self.write() which does not work in this case
        # Note that @api.depends does the work of @api.onchange. Also not @api.onchange does not persist  store=True fields
    @api.depends('retail_station_id', 'quantity', 'from_depot_id', 'to_depot_id')
    def _compute_rate(self):
        bridging_rate_obj = self.env['kin.bridging.rate']
        bridging_rate = bridging_rate_obj.search(
            [('from_depot_id', '=', self.from_depot_id.id), ('to_depot_id', '=', self.to_depot_id.id)]).bridging_rate
        if str(bridging_rate) != 'False':
            nta_rate = self.retail_station_id.nta_rate
            contribution_rate = self.retail_station_id.contribution_rate
            claim_rate = nta_rate + bridging_rate
            rate = claim_rate - contribution_rate
            if rate < contribution_rate:
                rate = contribution_rate
            elif self.from_depot_id == self.to_depot_id:
                rate = contribution_rate

            claim_total = claim_rate * self.quantity
            contribution_total = contribution_rate * self.quantity
            net_claim = claim_total - contribution_total

            #Always use the self.update() if you want the changes to reflect on the interface. I suppose direct assignment to the field should also work. see example on the snippets.py
            self.update(
                {   'contribution_total': contribution_total,
                    'claim_total': claim_total,
                    'claim_rate': claim_rate,
                    'nta_rate': nta_rate,
                    'contribution_rate': contribution_rate,
                    'bridging_rate': bridging_rate,
                    'net_claim' : net_claim
                    })
            return rate

    @api.multi
    def action_cleared(self):
        rate = self._compute_rate()
        if rate == self.retail_station_id.contribution_rate:
            inv = self.create_invoice(abs(rate), qty=self.quantity, inv_type='in_invoice')  # cPef is a creditor
        else:
            inv = self.create_invoice(abs(rate), qty=self.quantity, inv_type='out_invoice')  # Pef is a debtor

        self.invoice_id = inv.id
        self.state = 'cleared'


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('pef_id_code') or 'New'
        res = super(PEFRegister, self).create(vals)
        return res

    @api.multi
    def action_cancel(self):
        self.invoice_id.unlink()
        self.state = 'cancel'


    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_transit(self):
        self.state = 'transit'

    @api.multi
    def unlink(self):
        for rec in self:
            rec.invoice_id.unlink()
        return super(PEFRegister, self).unlink()

    @api.multi
    def action_view_loading_ticket(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Loading Ticket'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.loading_ticket_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('loading_ticket_id')
    def _compute_lt_count(self):
        for rec in self:
            rec.lt_count = len(rec.loading_ticket_id)


    name = fields.Char('Name')
    waybill_no = fields.Char('Waybill No')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity')
    from_depot_id = fields.Many2one('kin.receiving.pef.depot',string='From Depot')
    to_depot_id = fields.Many2one('kin.receiving.pef.depot',string='To Depot')
    retail_station_id = fields.Many2one('kin.retail.pef.station', string='Retail Station')
    state = fields.Selection([('draft', 'Draft'), ('transit', 'Truck In Transit'), ('cleared', 'Truck Cleared'), ('cancel', 'Cancel')], default='draft',track_visibility='onchange')
    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)
    invoice_id = fields.Many2one('account.invoice')
    pef_date = fields.Date('Date',default=fields.Datetime.now)
    product_uom = fields.Many2one('product.uom',related='product_id.uom_id', string='Unit of Measure')
    contribution_rate = fields.Float('Contribution Rate',compute='_compute_rate')
    nta_rate = fields.Float('NTA Rate')
    bridging_rate = fields.Float('Bridging Rate')
    claim_rate = fields.Float('Claim Rate',help='NTA Rate + Bridging Rate')
    claim_total = fields.Float('Total Claim Amount',help='Claim Rate * Quantity')
    contribution_total =fields.Float('Total Contribution Amount',help='Contribution Rate * Quantity')
    net_claim  = fields.Float(string='Net Claim',help='Total Claim Amount + Total Contribution Amount')
    driver_id = fields.Many2one('res.partner', string="Driver's  Name")
    from_stock_location_id = fields.Many2one('stock.location', string='From Stock Location')
    truck_no = fields.Char('Truck No')
    ticket_ref = fields.Char('Loading Ticket Reference')
    other_ref = fields.Char('Other Reference')
    user_id = fields.Many2one('res.users', string='User')
    loading_ticket_id = fields.Many2one('stock.picking', string='Loading Tickets')
    lt_count = fields.Integer(compute="_compute_lt_count", string='# of Loading Ticket', copy=False, default=0)
    comment = fields.Text("Comment")



class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def btn_view_pef(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('PEF Register'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.pef.register',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.pef_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.one
    @api.depends('pef_id')
    def _compute_pef_count(self):
        self.pef_count = len(self.pef_id)


    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()


        if self.partner_id and self.partner_id.is_company_station and self.partner_id.retail_station_id :
            #create the product received register
            pef = self.env['kin.pef.register']
            pack_operation_line = self.pack_operation_product_ids[0]


            vals = {
                'driver_id' : self.driver_id and self.driver_id.id,
                 'product_id' : pack_operation_line.product_id.id,
                 'quantity' : pack_operation_line.product_qty,
                'from_stock_location_id' : pack_operation_line.location_id.id,
                'retail_station_id': self.partner_id.retail_station_pef_id.id,
                'ticket_ref' : self.name,
                'loading_ticket_id' : self.id,
                'state' : 'draft',
                'truck_no': self.truck_no


            }
            pef_obj = pef.create(vals)
            self.pef_id = pef_obj

            #Notify the PEF Manager
            user_ids = []
            group_obj = self.env.ref('kin_pef.group_pef_manager')
            for user in group_obj.users:
                user_ids.append(user.id)
                self.message_subscribe_users(user_ids=user_ids)
                self.message_post(_('A New PEF Record from %s has been Created with ID %s.') % (
                    self.env.user.name, pef_obj.name),
                                  subject='A New PEF Record has been Created ', subtype='mail.mt_comment')

        return  res


    pef_id = fields.Many2one('kin.pef.register',string='PEF Register')
    pef_count = fields.Integer(compute="_compute_pef_count", string='# of PEF', copy=False, default=0)




class ResCompanyPef(models.Model):
    _inherit = "res.company"

    partner_pef_id = fields.Many2one('res.partner', string='Petroleum Equalization Fund')
    product_id = fields.Many2one('product.product', string='PEF Account Product')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_pef_invoice = fields.Boolean(string='PEF Invoice')


class ResPartner(models.Model):
    _inherit = 'res.partner'


    retail_station_pef_id = fields.Many2one('kin.retail.pef.station',string='Retail Station for PEF')


