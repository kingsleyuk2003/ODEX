# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017 - 2019  Kinsolve Solutions
# Copyright 2017 - 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from openerp.exceptions import UserError, Warning
from openerp.osv import fields as fields2
import openerp.addons.decimal_precision as dp
from urllib import urlencode
from urlparse import urljoin
from openerp.tools import float_is_zero, float_compare, float_round, DEFAULT_SERVER_DATETIME_FORMAT
import time
from datetime import datetime
from psycopg2 import OperationalError
import openerp
from datetime import *
from openerp import SUPERUSER_ID



class StockPicking(models.Model):
    _inherit = "stock.picking"
    _order = 'name desc'

    @api.multi
    def copy(self, default=None):
        group_obj = self.env.ref('kin_stock.group_duplicate_action_menu')
        if self.env.user not in group_obj.users and not default.get('backorder_id',True):
            raise UserError(_('You are not allowed to duplicate this form. Please contact the admin'))
        return super(StockPicking,self).copy(default)

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if self.partner_id.customer and  self.partner_id.active == False :
            raise UserError(_('%s is not approved and active' % (self.partner_id.name)))
        return res

    @api.model
    def create(self,vals):
        po_ref = vals.get('po_ref',False)
        if po_ref :
            vals['shipment_ref'] = po_ref

        vend_ref = vals.get('vend_ref', False)
        if vend_ref:
            vals['shipment_ref'] = vend_ref
        res = super(StockPicking,self).create(vals)
        return res

    @api.multi
    def action_assign(self):

        res = super(StockPicking,self).action_assign()
        return res
        # res1 = {}
        # res1['warning'] = {
        #                       'title' : "Warning: bad value",
        #                       'message' : "Still Waiting to Restock. Please Purchase the Itemff",
        #                       }
        # #return res
        # res2 = {
        #         'type': 'ir.actions.client',
        #         'tag': 'action_client_kin_stock_tag',
        #         # 'name': 'Warning',
        #         # 'params': {
        #         #    'title': 'Warning!',
        #         #    'text': 'Entered Quantity is greater than quantity on source.',
        #         #    'sticky': True
        #         # }
        #     }
        #
        # return  {'type': 'ir.actions.acxddfsrsafsafsfsmts_lose_wizard_and_reload_view'}  # see reference: https://www.odoo.com/forum/help-1/question/how-to-refresh-the-original-view-after-wizard-actions-10268  from Petar





    @api.multi
    def do_unreserve(self):
        super(StockPicking,self).do_unreserve()
        return  {'type': 'ir.actions.act_close_wizard_and_reload_view'}  # see reference: https://www.odoo.com/forum/help-1/question/how-to-refresh-the-original-view-after-wizard-actions-10268  from Petar

    @api.multi
    def close_alert_box(self):
        self.show_alert_box = False
        return

    @api.multi
    def action_cancel(self):
        super(StockPicking,self).action_cancel()
        return  {'type': 'ir.actions.act_close_wizard_and_reload_view'}  # see reference: https://www.odoo.com/forum/help-1/question/how-to-refresh-the-original-view-after-wizard-actions-10268  from Petar


    @api.onchange('location_id')
    def change_location_id(self):
        res = {}
        sale_id = self.sale_id
        status = self.state
        if sale_id and status in ['assigned','partially_available']:

            res['warning'] = {'title' : "Error", 'message' : 'Please click the "Discard" Button, then click "Unreserve" Button, Make the location changes and click "Reserve" button to change the delivery source location', }

            default_rec = self.env['stock.location'].search([('is_default_option','=',True)])
            if len(default_rec) > 1 :
                raise UserError('Please contact your admin to set only one default location in the stock location configuration')

            if not default_rec :
                self.location_id = None
                res['warning'] = {'title' : "Error", 'message' : 'Please set at least one Stock Location in the configuration as "Is default Option" for the system to proceed or click the "Discard" button', }

            else :
                self.location_id = default_rec
            return res

        pack_operation_product_ids = self.pack_operation_product_ids

        for pack_operation_prod in pack_operation_product_ids :
            pack_operation_prod.location_id = self.location_id
            pack_operation_prod.from_loc = self.location_id.name


    @api.onchange('location_dest_id')
    def change_location_dest_id(self):

        pack_operation_product_ids = self.pack_operation_product_ids

        for pack_operation_prod in pack_operation_product_ids :
            pack_operation_prod.location_dest_id = self.location_dest_id
            pack_operation_prod.to_loc = self.location_dest_id.name





    def _get_url(self, module_name,menu_id,action_id, context=None):
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


    def _get_stock_url(self, module_name, menu_id, action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name, menu_id)[1]
        fragment['model'] = 'stock.picking'
        fragment['view_type'] = 'form'
        fragment['action'] = model_data.get_object_reference(module_name, action_id)[1]
        query = {'db': self.env.cr.dbname}
            # for displaying tree view. Remove if you want to display form view
            #         fragment['page'] = '0'
            #         fragment['limit'] = '80'
            #         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


            # For displaying a single record. Remove if you want to display tree view
        fragment['id'] = context.get("picking_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res

# Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line:
            # Load a PO line only once
            if line in self.invoice_line_ids.mapped('purchase_line_id'):
                continue
            if line.product_id.purchase_method == 'purchase':
                qty = line.product_qty - line.qty_invoiced
            else:
                qty = line.qty_received - line.qty_invoiced
            if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                qty = 0.0
            taxes = line.taxes_id or line.product_id.supplier_taxes_id
            invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
            data = {
                'purchase_line_id': line.id,
                'name': line.name,
                'origin': self.purchase_id.origin,
                'uom_id': line.product_uom.id,
                'product_id': line.product_id.id,
                'account_id': self.env['account.invoice.line'].with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
                'price_unit': line.order_id.currency_id.with_context(date=line.order_id.date_order or fields.Date.context_today(self)).compute(line.price_unit, self.currency_id),
                'quantity': qty,
                'discount': 0.0,
                'account_analytic_id': line.account_analytic_id.id,
                'invoice_line_tax_ids': invoice_line_tax_ids.ids,

            }
            account = new_lines.get_invoice_line_account('in_invoice', line.product_id, self.purchase_id.fiscal_position_id, self.env.user.company_id)
            if account:
                data['account_id'] = account.id
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.compute_taxes()
        self.purchase_id = False
        return {}


    # NO NEED AGAIN
    # def _prepare_pack_ops(self, cr, uid, picking, quants, forced_qties, context=None):
    #     """ returns a list of dict, ready to be used in create() of stock.pack.operation.
    #
    #     :param picking: browse record (stock.picking)
    #     :param quants: browse record list (stock.quant). List of quants associated to the picking
    #     :param forced_qties: dictionary showing for each product (keys) its corresponding quantity (value) that is not covered by the quants associated to the picking
    #     """
    #     def _picking_putaway_apply(product):
    #         location = False
    #         # Search putaway strategy
    #         if product_putaway_strats.get(product.id):
    #             location = product_putaway_strats[product.id]
    #         else:
    #             location = self.pool.get('stock.location').get_putaway_strategy(cr, uid, picking.location_dest_id, product, context=context)
    #             product_putaway_strats[product.id] = location
    #         return location or picking.location_dest_id.id
    #
    #     # If we encounter an UoM that is smaller than the default UoM or the one already chosen, use the new one instead.
    #     product_uom = {} # Determines UoM used in pack operations
    #     purchase_lines = {}
    #     sales_lines = {}
    #     location_dest_id = None
    #     location_id = None
    #     for move in [x for x in picking.move_lines if x.state not in ('done', 'cancel')]:
    #         if not product_uom.get(move.product_id.id):
    #             product_uom[move.product_id.id] = move.product_id.uom_id
    #             purchase_lines[move.product_id.id] = move.purchase_order_line_id or False
    #             sales_lines[move.product_id.id] = move.sale_order_line_id or False
    #         if move.product_uom.id != move.product_id.uom_id.id and move.product_uom.factor > product_uom[move.product_id.id].factor:
    #             product_uom[move.product_id.id] = move.product_uom
    #         if not move.scrapped:
    #             if location_dest_id and move.location_dest_id.id != location_dest_id:
    #                 raise UserError(_('The destination location must be the same for all the moves of the picking.'))
    #             location_dest_id = move.location_dest_id.id
    #             if location_id and move.location_id.id != location_id:
    #                 raise UserError(_('The source location must be the same for all the moves of the picking.'))
    #             location_id = move.location_id.id
    #
    #     pack_obj = self.pool.get("stock.quant.package")
    #     quant_obj = self.pool.get("stock.quant")
    #     vals = []
    #     qtys_grouped = {}
    #     lots_grouped = {}
    #     #for each quant of the picking, find the suggested location
    #     quants_suggested_locations = {}
    #     product_putaway_strats = {}
    #     for quant in quants:
    #         if quant.qty <= 0:
    #             continue
    #         suggested_location_id = _picking_putaway_apply(quant.product_id)
    #         quants_suggested_locations[quant] = suggested_location_id
    #
    #     #find the packages we can movei as a whole
    #     top_lvl_packages = self._get_top_level_packages(cr, uid, quants_suggested_locations, context=context)
    #     # and then create pack operations for the top-level packages found
    #     for pack in top_lvl_packages:
    #         pack_quant_ids = pack_obj.get_content(cr, uid, [pack.id], context=context)
    #         pack_quants = quant_obj.browse(cr, uid, pack_quant_ids, context=context)
    #         vals.append({
    #                 'picking_id': picking.id,
    #                 'package_id': pack.id,
    #                 'product_qty': 1.0,
    #                 'location_id': pack.location_id.id,
    #                 'location_dest_id': quants_suggested_locations[pack_quants[0]],
    #                 'owner_id': pack.owner_id.id,
    #             })
    #         #remove the quants inside the package so that they are excluded from the rest of the computation
    #         for quant in pack_quants:
    #             del quants_suggested_locations[quant]
    #     # Go through all remaining reserved quants and group by product, package, owner, source location and dest location
    #     # Lots will go into pack operation lot object
    #     for quant, dest_location_id in quants_suggested_locations.items():
    #         key = (quant.product_id.id, quant.package_id.id, quant.owner_id.id, quant.location_id.id, dest_location_id)
    #         if qtys_grouped.get(key):
    #             qtys_grouped[key] += quant.qty
    #         else:
    #             qtys_grouped[key] = quant.qty
    #         if quant.product_id.tracking != 'none' and quant.lot_id:
    #             lots_grouped.setdefault(key, {}).setdefault(quant.lot_id.id, 0.0)
    #             lots_grouped[key][quant.lot_id.id] += quant.qty
    #
    #     # Do the same for the forced quantities (in cases of force_assign or incomming shipment for example)
    #     for product, qty in forced_qties.items():
    #         if qty <= 0:
    #             continue
    #         suggested_location_id = _picking_putaway_apply(product)
    #         key = (product.id, False, picking.owner_id.id, picking.location_id.id, suggested_location_id)
    #         if qtys_grouped.get(key):
    #             qtys_grouped[key] += qty
    #         else:
    #             qtys_grouped[key] = qty
    #
    #     # Create the necessary operations for the grouped quants and remaining qtys
    #     uom_obj = self.pool.get('product.uom')
    #     prevals = {}
    #     for key, qty in qtys_grouped.items():
    #         product = self.pool.get("product.product").browse(cr, uid, key[0], context=context)
    #         uom_id = product.uom_id.id
    #         purchase_order_line_id = False
    #         sale_order_line_id = False
    #         qty_uom = qty
    #         if product_uom.get(key[0]):
    #             uom_id = product_uom[key[0]].id
    #             purchase_order_line_id = purchase_lines[key[0]] and purchase_lines[key[0]].id
    #             sale_order_line_id = sales_lines[key[0]] and sales_lines[key[0]].id
    #             qty_uom = uom_obj._compute_qty(cr, uid, product.uom_id.id, qty, uom_id)
    #         pack_lot_ids = []
    #         if lots_grouped.get(key):
    #             for lot in lots_grouped[key].keys():
    #                 pack_lot_ids += [(0, 0, {'lot_id': lot, 'qty': 0.0, 'qty_todo': lots_grouped[key][lot]})]
    #         val_dict = {
    #             'picking_id': picking.id,
    #             'product_qty': qty_uom,
    #             'product_id': key[0],
    #             'package_id': key[1],
    #             'owner_id': key[2],
    #             'location_id': key[3],
    #             'location_dest_id': key[4],
    #             'product_uom_id': uom_id,
    #             'pack_lot_ids': pack_lot_ids,
    #             'purchase_order_line_id': purchase_order_line_id,
    #             'sale_order_line_id' : sale_order_line_id
    #         }
    #         if key[0] in prevals:
    #             prevals[key[0]].append(val_dict)
    #         else:
    #             prevals[key[0]] = [val_dict]
    #     # prevals var holds the operations in order to create them in the same order than the picking stock moves if possible
    #     processed_products = set()
    #     for move in [x for x in picking.move_lines if x.state not in ('done', 'cancel')]:
    #         if move.product_id.id not in processed_products:
    #             vals += prevals.get(move.product_id.id, [])
    #             processed_products.add(move.product_id.id)
    #     return vals


    def create_customer_invoice(self, inv_refund=False):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        journal_domain = [
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.user.company_id.id)
        ]
        journal_id = self.env['account.journal'].search(journal_domain, limit=1)

        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))

        sale_order = self.sale_id

        invoice_vals = {
            'name': sale_order.client_order_ref or '',
            'origin': sale_order.name,
            'type': 'out_invoice',
            'reference': sale_order.client_order_ref or self.name,
            'account_id': sale_order.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': sale_order.partner_invoice_id.id,
            'journal_id': journal_id.id,
            'currency_id': sale_order.pricelist_id.currency_id.id,
            'comment': sale_order.note,
            'payment_term_id': sale_order.payment_term_id.id,
            'fiscal_position_id': sale_order.fiscal_position_id.id or sale_order.partner_invoice_id.property_account_position_id.id,
            'company_id': sale_order.company_id.id,
            'user_id': sale_order.user_id and sale_order.user_id.id,
            'team_id': sale_order.team_id.id,
            'incoterms_id': sale_order.incoterm.id or False,
            'is_from_inventory':True

        }

        invoice = inv_obj.create(invoice_vals)

        lines = []
        for picking_line in self.pack_operation_ids:
            move_id = picking_line.linked_move_operation_ids.mapped('move_id')
            sale_order_line_id = move_id.sale_order_line_id

            if not sale_order_line_id:
                raise UserError(_(
                    'Sorry, Dispatch cannot be validated and invoice cannot be generated, since no sales order line is linked to the stock move'))

            if not float_is_zero(picking_line.product_qty, precision_digits=precision):
                account = sale_order_line_id.product_id.property_account_income_id or sale_order_line_id.product_id.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(
                        _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                        sale_order_line_id.product_id.name, sale_order_line_id.product_id.id,
                        sale_order_line_id.product_id.categ_id.name))

                fpos = sale_order_line_id.order_id.fiscal_position_id or sale_order_line_id.order_id.partner_id.property_account_position_id
                if fpos:
                    account = fpos.map_account(account)
                ######### OR
                #account = self.env['account.invoice.line'].get_invoice_line_account('out_invoice', sale_order_line_id.product_id, sale_order_line_id.order_id.fiscal_position_id, self.env.user.company_id)


                default_analytic_account = self.env['account.analytic.default'].account_get(
                    sale_order_line_id.product_id.id, sale_order_line_id.order_id.partner_id.id,
                    sale_order_line_id.order_id.user_id.id, datetime.today())

                inv_line = {
                    'name': sale_order_line_id.name,
                    'sequence': sale_order_line_id.sequence,
                    'origin': sale_order_line_id.order_id.name,
                    'account_id': account.id,
                    'price_unit': sale_order_line_id.price_unit,
                    'quantity': picking_line.product_qty,
                    'discount': sale_order_line_id.discount,
                    'uom_id': picking_line.product_uom_id.id,
                    'product_id': picking_line.product_id.id or False,
                    'invoice_line_tax_ids': [(6, 0, sale_order_line_id.tax_id.ids)],
                    'account_analytic_id': sale_order_line_id.order_id.project_id.id or default_analytic_account and default_analytic_account.analytic_id.id,
                    'invoice_id': invoice.id,
                    'sale_line_ids': [(6, 0, [sale_order_line_id.id])]
                }
                self.env['account.invoice.line'].create(inv_line)

                # Advance Payment Invoice line
                if sale_order_line_id.order_id.is_has_advance_invoice:

                    # since product is selected in the invoice line, the system generates more entries to record COG. We don't want it for advance invoice. so we resort to creating a GL advance account per product
                    # account_id = False
                    # pro_id = self.env['ir.values'].get_default('sale.config.settings', 'deposit_product_id_setting')
                    # if not pro_id:
                    #     raise UserError(_('Please set the advance payment invoice product in the sales settings'))
                    # product_id = self.env['product.product'].browse(pro_id)
                    # unearned_income = picking_line.product_id.unearned_income_id
                    # unearned_taxes = product_id.taxes_id
                    #
                    # if product_id.id:
                    #     account_id = unearned_income.id
                    #
                    # if not account_id:
                    #     raise UserError(
                    #         _(
                    #             'There is no income account defined for this product: "%s". ') % \
                    #         (product_id.name,))

                    account = sale_order_line_id.product_id.account_advance_id or sale_order_line_id.product_id.categ_id.account_advance_id
                    if not account:
                        raise UserError(_(
                            'Please define unearned revenue account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                                        sale_order_line_id.product_id.name, sale_order_line_id.product_id.id,
                                        sale_order_line_id.product_id.categ_id.name))

                    fpos = sale_order_line_id.order_id.fiscal_position_id or sale_order_line_id.order_id.partner_id.property_account_position_id
                    if fpos:
                        account = fpos.map_account(account)
                    account = sale_order_line_id.product_id.account_advance_id or sale_order_line_id.product_id.categ_id.account_advance_id
                    if not account:
                        raise UserError(_(
                            'Please define unearned revenue account for this product: "%s" (id:%d) - or for its category: "%s".') % (
                                            sale_order_line_id.product_id.name, sale_order_line_id.product_id.id,
                                            sale_order_line_id.product_id.categ_id.name))

                    default_analytic_account = self.env['account.analytic.default'].account_get(
                        sale_order_line_id.product_id.id, sale_order_line_id.order_id.partner_id.id,
                        sale_order_line_id.order_id.user_id.id, date.today())

                    amount = sale_order_line_id.price_total / sale_order_line_id.product_uom_qty
                    if amount <= 0.00:
                        raise UserError(_('The value of the down payment amount must be positive.'))

                    unearned_taxes = sale_order_line_id.product_id.taxes_id
                    if sale_order_line_id.order_id.fiscal_position_id and unearned_taxes:
                        tax_ids = sale_order_line_id.order_id.fiscal_position_id.map_tax(unearned_taxes).ids
                    else:
                        tax_ids = unearned_taxes.ids

                    inv_line_adv = {
                         'name': _("%s Advance payment %s (Unearned Revenue) deduction of %s for %s") % (picking_line.product_id.name, picking_line.product_id.name, amount * -picking_line.product_qty,sale_order_line_id.order_id.name),
                        'sequence': sale_order_line_id.sequence,
                        'origin': sale_order_line_id.order_id.name,
                        'account_id': account.id,
                        'price_unit': amount,
                        'quantity': -picking_line.product_qty,
                        'discount': 0.0,
                        'uom_id': picking_line.product_id.uom_id.id,
                        # 'product_id': sale_order_line_id.product_id.id or False, # # This causes the validated invoice to create COG entries from Goods Dispatched
                        'invoice_line_tax_ids': [(6, 0, tax_ids)],
                        'account_analytic_id': sale_order_line_id.order_id.project_id.id or default_analytic_account and default_analytic_account.analytic_id.id,
                        'invoice_id': invoice.id,
                        'sale_line_ids': [(6, 0, [sale_order_line_id.id])]
                    # Never remove this sale_line_ids. This determines the cost of goods sold using the FIFO and not from the product page
                    }
                    invoice.is_has_advance_invoice = True
                    self.env['account.invoice.line'].create(inv_line_adv)

        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
        if invoice.amount_untaxed < 0 or inv_refund:
            invoice.type = 'out_refund'
            # for line in invoice.invoice_line_ids:
            #     line.quantity = -line.quantity  #wrong code for out_refund. i.e. return inwards
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()

        return invoice


    def create_vendor_bill(self,inv_refund=False):

        invoice_obj = self.env['account.invoice']
        invoice_lines = self.env['account.invoice.line']
        partner = self.partner_id
        if partner :
            journal_domain = [
                        ('type', '=', 'purchase'),
                        ('company_id', '=', self.env.user.company_id.id)
                ]
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)

            vals = {
                    'partner_id' : partner.id ,
                    'company_id' : self.company_id.id ,
                    'type' : 'in_invoice' ,
                    'account_id' : partner.property_account_payable_id.id ,
                    'payment_term_id' : partner.property_supplier_payment_term_id.id,
                    'fiscal_position_id' : partner.property_account_position_id.id ,
                    'payment_term_id' : partner.property_supplier_payment_term_id.id ,
                    'partner_bank_id' : partner.bank_ids and partner.bank_ids.ids[0] or False ,
                    'journal_id':default_journal_id.id,
                    'origin': self.purchase_id.name,
            }

            lines = []
            for picking_line in self.pack_operation_ids:
                move_id = picking_line.linked_move_operation_ids.mapped('move_id')
                purchase_order_line_id = move_id.purchase_order_line_id

                if not purchase_order_line_id:
                    raise UserError(_(
                        'Sorry, Dispatch cannot be validated and invoice cannot be generated, since no purchase order line is linked to the stock move'))

                taxes = purchase_order_line_id.taxes_id
                invoice_line_tax_ids = purchase_order_line_id.order_id.fiscal_position_id.map_tax(taxes)
                comp_currency = purchase_order_line_id.currency_id
                account = invoice_lines.get_invoice_line_account('in_invoice', purchase_order_line_id.product_id, purchase_order_line_id.order_id.fiscal_position_id, self.env.user.company_id)

                line = (0,0,{
                        'name': purchase_order_line_id.name,
                        'origin': self.name,
                        'uom_id': purchase_order_line_id.product_uom.id,
                        'product_id': purchase_order_line_id.product_id.id,
                        'account_id': invoice_lines.with_context({'journal_id': default_journal_id.id, 'type': 'in_invoice'})._default_account(),
                        'price_unit': comp_currency.with_context(date=purchase_order_line_id.date_order or fields.Date.context_today(self)).compute(purchase_order_line_id.price_unit, comp_currency),
                        'quantity': picking_line.product_qty,
                        'discount': 0.0,
                        'account_analytic_id': purchase_order_line_id.account_analytic_id.id,
                        'invoice_line_tax_ids': [(6, 0, invoice_line_tax_ids.ids)],
                        'purchase_line_id' :purchase_order_line_id.id,
                        'account_id' : account.id
                })
                lines.append(line)

            vals['invoice_line_ids'] = lines
            purchase_inv = invoice_obj.create(vals)

            if not purchase_inv.invoice_line_ids:
                raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
            if purchase_inv.amount_untaxed < 0 or inv_refund :
                purchase_inv.type = 'in_refund'

        # Use additional field helper function (for account extensions)
            for line in purchase_inv.invoice_line_ids:
                line._set_additional_fields(purchase_inv)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            purchase_inv.compute_taxes()

                    # taxes = picking_line.product_id.supplier_taxes_id
                    # invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
                    # comp_currency = self.env.user.company_id.currency_id

            purchase_inv.purchase_id = False
            # purchase_inv.purchase_id1 = purchase_order_line_id.order_id
            return purchase_inv


    def create_vendor_bill_full(self):
        invoice_obj = self.env['account.invoice']
        purchase_order = self.purchase_id
        partn = self.partner_id
        if partn :
            journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.env.user.company_id.id)
            ]
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
            vals = {
                'partner_id' : partn.id ,
                'company_id' : self.company_id.id ,
                'type' : 'in_invoice' ,
                'account_id' : partn.property_account_payable_id.id ,
                'payment_term_id' : partn.property_supplier_payment_term_id.id,
                'fiscal_position_id' : partn.property_account_position_id.id ,
                'payment_term_id' : partn.property_supplier_payment_term_id.id ,
                'partner_bank_id' : partn.bank_ids and partn.bank_ids.ids[0] or False ,
                'journal_id':default_journal_id.id ,
                'origin': purchase_order.name,
                'reference' : self.shipment_ref or purchase_order.partner_ref,
                'currency_id' : purchase_order.currency_id.id
                }

            purchase_inv = invoice_obj.create(vals)
            purchase_inv.purchase_id = purchase_order
            ans = purchase_inv.purchase_order_change()
            purchase_inv.compute_taxes()
            purchase_inv.purchase_id = False
            return purchase_inv


    @api.multi
    def unlink(self):
        res = super(StockPicking, self).unlink()
        for rec in self:
            try:
                if rec.name:
                    raise UserError(
                        _('Cannot delete a picking document with an id. You may reuse the document or cancel it'))
            except Exception:
                raise UserError(
                    _('Cannot delete a picking document with an id. You may reuse the document or cancel it'))
        return res



    def transfer_to_quality_control(self):
        # Send Email to QC
        company_email = self.env.user.company_id.email.strip()
        if company_email :
            user_ids = []
            mail_template = self.env.ref('kin_stock.mail_templ_quality_control')
            ctx = {}
            ctx.update({'picking_id': self.id})
            the_url = self._get_stock_url('stock', 'all_picking', 'action_picking_tree_all', ctx)

            group_obj = self.env.ref('kin_stock.group_receive_quality_control_email')
            for user in group_obj.users:
                if user.partner_id.email:
                    ctx = {'system_email': company_email,
                           'qc_person_email': user.partner_id.email,
                           'qc_person_name': user.partner_id.name,
                           'url': the_url
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)


    def transfer_create_refund_invoice(self):
        invref_obj = self.create_customer_invoice(inv_refund=True)
        self.invoice_refund_id = invref_obj
        self.invoice_id = invref_obj  # replaces the former invoice with the refund invoice
        # invref_obj.message_post( _('Customer Refund Invoice Created for Returned Inventory %s.') % (self.name),subject='Please See the Created Refund Invoice from Customer Inventory Return', subtype='mail.mt_comment')
        if self.picking_type_id.is_validate_invoice:
            # this one below dis npt work because it could not allow payment allocation after opening the invoice and also it could not allow making a zero total amout invoice to paid automatically
            # invref_obj.action_move_create()
            # invref_obj.invoice_validate()
            invref_obj.signal_workflow('invoice_open')

        # Send Refund Invoice Notification
        is_send_invoice_notification = self.picking_type_id.is_send_invoice_notification
        company_email = self.env.user.company_id.email.strip()
        if is_send_invoice_notification and company_email:

            # Custom Email Template
            mail_template = self.env.ref('kin_stock.mail_templ_invoice_delivery_refund')
            the_url = invref_obj._get_url('account', 'menu_action_invoice_tree1', 'action_invoice_tree1')

            users = []
            group_obj = self.env.ref('kin_stock.group_receive_inventory_invoice_email_refund')
            for user in group_obj.users:
                users.append(user.id)
                if user.partner_id.email and user.partner_id.email.strip():
                    ctx = {'system_email': company_email,
                           'accountant_email': user.partner_id.email,
                           'accountant_name': user.partner_id.name,
                           'url': the_url,
                           'origin': invref_obj.origin,
                           'partner_name': self.partner_id.name
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                    self.show_alert_box = True


    def transfer_create_invoice(self):
        invoice_obj = self.env['account.invoice']
        sale_order = self.sale_id

        # THE SYSTEM ALREADY TAKES CARE OF THE FOLLOWING BY SETTING THE PARAMETER FOR THE "Invoicing Policy" on the product page
        # even the account merge addon merges invoice perfectly after creating invoice as a result of backorder operation with the system out-of-the-box version
        # if self.picking_type_id.is_create_full_invoice :
        #     inv_id = sale_order.action_invoice_create()
        #     inv_obj = invoice_obj.browse(inv_id)[0]
        # else:
        #     #Create invoice based on delivered or fallback to full invoice of the ordered lines
        #     if self.pack_operation_ids[0].sale_line_id :
        #         inv_obj = self.create_customer_invoice()
        #     else:
        #         inv_id = sale_order.action_invoice_create()
        #         inv_obj = invoice_obj.browse(inv_id)[0]
        inv_id = sale_order.action_invoice_create(final=True)
        if inv_id:  # if inv_id is empty , maybe as a result of an already created invoice, thus no invoice may be created here. This can happen when sales order is cancelled and open again with another delivery that creates an invoice
            inv_obj = invoice_obj.browse(inv_id)[0]

            if self.picking_type_id.is_validate_invoice:
                # this one below dis npt work because it could not allow payment allocation after opening the invoice and also it could not allow making a zero total amout invoice to paid automatically
                # inv_obj.action_move_create()
                # inv_obj.invoice_validate()
                inv_obj.signal_workflow('invoice_open')

            inv_obj.sale_id = sale_order
            inv_obj.picking_id = self
            self.invoice_id = inv_obj

            user_ids = []
            if inv_obj.partner_id and inv_obj.partner_id.user_id:
                user_ids.append(inv_obj.partner_id.user_id.id)
            # inv_obj.message_subscribe_users(user_ids=user_ids)
            # inv_obj.message_post( _('Invoice Created for Delivered Inventory %s.') % (self.name),subject='Please See the Created Invoice for Delivered Inventory', subtype='mail.mt_comment')

            # Send Invoice Notification to Selected Users
            is_send_invoice_notification = self.picking_type_id.is_send_invoice_notification
            company_email = self.env.user.company_id.email.strip()
            if is_send_invoice_notification and company_email:
                # Custom Email Template
                mail_template = self.env.ref('kin_stock.mail_templ_invoice_delivery')
                the_url = inv_obj._get_url('account', 'menu_action_invoice_tree1', 'action_invoice_tree1')

                users = []
                group_obj = self.env.ref('kin_stock.group_receive_inventory_invoice_email')
                for user in group_obj.users:
                    users.append(user.id)
                    if user.partner_id.email and user.partner_id.email.strip():
                        ctx = {'system_email': company_email,
                               'accountant_email': user.partner_id.email,
                               'accountant_name': user.partner_id.name,
                               'url': the_url,
                               'origin': inv_obj.origin,
                               'partner_name': self.partner_id.name
                               }
                        mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                        self.show_alert_box = True

                # Also notify uses of items awaiting pickup
                stock_person_email = self.env.user.partner_id.email.strip()
                stock_person_name = self.env.user.name

                if company_email and stock_person_email:
                    # Custom Email Template
                    mail_template = self.env.ref('kin_stock.mail_templ_delivery_awaiting_pickup')
                    ctx = {}
                    ctx.update({'picking_id': self.id})
                    the_url = self._get_stock_url('stock', 'all_picking', 'action_picking_tree_all', ctx)

                    user_ids = []
                    group_obj = self.env.ref('kin_stock.group_receive_stock_delivery_orders_awaiting_pickup_email')
                    for user in group_obj.users:
                        if user.partner_id.email and user.partner_id.email.strip():
                            user_ids.append(user.id)
                            ctx = {'system_email': company_email,
                                   'stock_person_name': stock_person_name,
                                   'stock_person_email': stock_person_email,
                                   'notify_person_email': user.partner_id.email,
                                   'notify_person_name': user.partner_id.name,
                                   'url': the_url
                                   }
                            mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                            # self.message_subscribe_users(user_ids=user_ids)



    def transfer_create_refund_bill(self):
        prev_picking_obj = self.previous_picking_id
        prev_purchase_order = prev_picking_obj.purchase_id or False

        pur_invref_obj = self.create_vendor_bill(inv_refund=True)
        self.invoice_refund_id = pur_invref_obj
        self.invoice_id = pur_invref_obj

        self.supplier_invoice_refund_id = pur_invref_obj
        self.invoice_id = pur_invref_obj  # replaces the former invoice with the refund invoice
        # pur_invref_obj.message_post( _('Vendor Refund Invoice Created for Returned Inventory %s.') % (self.name),subject='Please See the Created Refund Invoice to Vendor Inventory Return',subtype='mail.mt_comment')

        if self.picking_type_id.is_validate_invoice:
            # this one below dis npt work because it could not allow payment allocation after opening the invoice and also it could not allow making a zero total amout invoice to paid automatically
            # pur_invref_obj.action_move_create()
            # put_invref_obj.invoice_validate()
            pur_invref_obj.signal_workflow('invoice_open')

        # Send Email to the Accountant
        company_email = self.env.user.company_id.email.strip()
        if company_email:
            # Custom Email Template
            mail_template = self.env.ref('kin_stock.mail_templ_purchase_bill_created_refund')
            ctx = {}
            ctx.update({'invoice_id': pur_invref_obj.id})
            the_url = self._get_url('account', 'menu_action_invoice_tree2', 'action_invoice_tree2', ctx)

            users = []
            group_obj = self.env.ref('kin_stock.group_receive_purchase_bill_email_refund')
            for user in group_obj.users:
                users.append(user.id)
                if user.partner_id.email and user.partner_id.email.strip():
                    ctx = {'system_email': company_email,
                           'accountant_email': user.partner_id.email,
                           'accountant_name': user.partner_id.name,
                           'url': the_url,
                           'picking_id': self.name,
                           'purchase_id': prev_purchase_order.name,
                           'partner_name': self.partner_id.name

                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                    self.show_alert_box = True


    def transfer_create_bill(self):
        purchase_order = self.purchase_id
        vendor_bill = self.create_vendor_bill_full()

        if self.picking_type_id.is_validate_invoice:
            # this one below dis npt work because it could not allow payment allocation after opening the invoice and also it could not allow making a zero total amout invoice to paid automatically
            # vendor_bill.action_move_create()
            # vendor_bill.invoice_validate()
            vendor_bill.signal_workflow('invoice_open')


        # THE SYSTEM ALREADY TAKES CARE OF THE FOLLOWING BY SETTING THE PARAMETER FOR THE "Control Purchase Bills" on the product page,
        # even the account merge addon merges invoice perfectly after creating invoice as a result of backorder operation with the system out-of-the-box version
        # if self.picking_type_id.is_create_full_invoice :
        #     vendor_bill = self.create_vendor_bill_full()
        # else:
        #     #Create bill based on what was delivered or fall back to the full invoice of what was delivered
        #     if self.pack_operation_ids[0].purchase_line_id :
        #         vendor_bill = self.create_vendor_bill()
        #     else:
        #         vendor_bill = self.create_vendor_bill_full()

        if vendor_bill:
            vendor_bill.purchase_id1 = purchase_order  # store the purchase id
            vendor_bill.picking_id = self
            self.invoice_id = vendor_bill
            self.purchase_id = purchase_order

            # vendor_bill.message_post( _('Invoice Created for Received Inventory %s.') % (self.name),subject='Please See the Created Invoice for Goods Received into the Inventory', subtype='mail.mt_comment')

            # Send Email to the Accountant
            company_email = self.env.user.company_id.email.strip()
            if company_email:
                # Custom Email Template
                mail_template = self.env.ref('kin_stock.mail_templ_purchase_bill_created')
                ctx = {}
                ctx.update({'invoice_id': vendor_bill.id})
                the_url = self._get_url('account', 'menu_action_invoice_tree2', 'action_invoice_tree2', ctx)

                users = []
                group_obj = self.env.ref('kin_stock.group_receive_purchase_bill_email')
                for user in group_obj.users:
                    users.append(user.id)
                    if user.partner_id.email and user.partner_id.email.strip():
                        ctx = {'system_email': company_email,
                               'accountant_email': user.partner_id.email,
                               'accountant_name': user.partner_id.name,
                               'url': the_url,
                               'picking_id': self.name,
                               'purchase_id': purchase_order.name,
                               'partner_name': self.partner_id.name

                               }
                        mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                        self.show_alert_box = True


    @api.multi
    def do_transfer(self):
        if self.state == 'done':
            raise UserError(_('This record has been previously done. Please refresh your browser'))

        res = super(StockPicking,self).do_transfer()

        # The Shipment Date Set after Validation
        self.shipment_date = fields.Datetime.now()

        #Send email to QC for
        if self.picking_type_id.is_send_quality_control_notification :
            self.transfer_to_quality_control()

        is_create_invoice = self.picking_type_id.is_create_invoice
        if is_create_invoice :

            sale_order = self.sale_id
            picking_type_code = self.picking_type_code
            invoic_obj = self.invoice_id or False
            if picking_type_code == "incoming" and sale_order and invoic_obj : # Create a Customer refund invoice
                self.transfer_create_refund_invoice() #return inwards

            is_delivery_invoicing_policy = False
            backorder = self.backorder_id

            for picking_line in self.pack_operation_ids:
                if picking_line.product_id.invoice_policy == "delivery" :
                    is_delivery_invoicing_policy = True  #if at least one picking line product invoicing policy is based on delivered quantity

            if backorder and not is_delivery_invoicing_policy : # Don't create the invoice, if it is a backorder and the invoicing policy is based on ordered quantity
                return res

            if picking_type_code == "outgoing" and sale_order    : # Create a Customer Invoice
                self.transfer_create_invoice()


############################################################################################
        ######   FOR PURCHASES VENDOR BILLS AND PURCHASE RETURNS

            is_received_purchase_method = False
            backorder = self.backorder_id

            for picking_line in self.pack_operation_ids:
                if picking_line.product_id.purchase_method == "receive" :
                    is_received_purchase_method = True

            if backorder and not is_received_purchase_method : # Don't create the invoice, if it is a backorder and the purchase method is based on ordered quantity
                return res

            purchase_order = self.purchase_id
            if picking_type_code == "incoming" and purchase_order  : # Create a Vendor Bill
                self.transfer_create_bill()

            # Create purchase refund bill to supplier
            prev_picking_obj = self.previous_picking_id
            if prev_picking_obj :
                prev_purchase_order = prev_picking_obj.purchase_id or False
                prev_invoice_id = prev_picking_obj.invoice_id or False
                if picking_type_code == "outgoing" and prev_purchase_order and prev_invoice_id  : # Create a Return goods Invoice
                    self.transfer_create_refund_bill()

        return res


    @api.multi
    def btn_view_invoices(self):
        invoice_ids = self.mapped('invoice_id')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'target': 'new',
        }
        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_ids.ids
        elif len(invoice_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.multi
    def btn_view_po(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Purchase Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.purchase_id])],
            #'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            #'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.multi
    def btn_view_so(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Sales Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.sale_id])],
            #'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            #'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.multi
    def btn_view_jnr(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.move_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.one
    @api.depends('invoice_id')
    def _compute_invoice_count(self):
            self.invoice_count = len(self.invoice_id)



    @api.depends('purchase_id')
    def _compute_po_count(self):
        for rec in self :
            rec.po_count = len(rec.purchase_id)


    @api.depends('sale_id')
    def _compute_so_count(self):
        for rec in self :
            rec.so_count = len(rec.sale_id)


    @api.depends('move_ids')
    def _compute_jnr_count(self):
        for rec in self:
            rec.jnr_count = len(rec.move_ids)


    @api.multi
    def action_shipped_notice(self):
        self.shipment_date = fields.Datetime.now()
        self.shipped_confirmed_by_user_id = self.env.user
        self.env.cr.execute("update stock_picking set state = 'shipped' where id = %s" % (self.id))


        #Email Notification to users
        # Send Email
        company_email = self.env.user.company_id.email.strip()
        stock_person_email = self.shipped_confirmed_by_user_id.partner_id.email.strip()
        stock_person_name = self.shipped_confirmed_by_user_id.name

        if company_email and stock_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kin_stock.mail_templ_picking_shipped')
            ctx = {}
            ctx.update({'picking_id': self.id})
            the_url = self._get_stock_url('stock', 'all_picking', 'action_picking_tree_all', ctx)

            user_ids = []
            group_obj = self.env.ref('kin_stock.group_receive_stock_picking_shipped_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'stock_person_name': stock_person_name,
                           'stock_person_email': stock_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                    #self.message_subscribe_users(user_ids=user_ids)

    @api.multi
    def action_delivery_notice(self):
        self.delivered_date = fields.Datetime.now()
        self.delivery_confirmed_by_user_id = self.env.user
        self.env.cr.execute("update stock_picking set state = 'delivered' where id = %s" % (self.id))

        # Email Notification to users
        company_email = self.env.user.company_id.email.strip()
        stock_person_email = self.delivery_confirmed_by_user_id.partner_id.email.strip()
        stock_person_name = self.delivery_confirmed_by_user_id.name

        if company_email and stock_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kin_stock.mail_templ_picking_delivered')
            ctx = {}
            ctx.update({'picking_id': self.id})
            the_url = self._get_stock_url('stock', 'all_picking', 'action_picking_tree_all', ctx)

            user_ids = []
            group_obj = self.env.ref('kin_stock.group_receive_stock_picking_delivered_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'stock_person_name': stock_person_name,
                           'stock_person_email': stock_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)
                    #self.message_subscribe_users(user_ids=user_ids)

        return True


    @api.multi
    def action_reject_notice(self, msg):
        self.rejection_date = fields.Datetime.now()
        self.rejection_confirmed_by_user_id = self.env.user
        self.env.cr.execute("update stock_picking set state = 'rejected' where id = %s" % (self.id))
        reason_for_rejection = msg

        # Email Notification to users
        # Send Email
        company_email = self.env.user.company_id.email.strip()
        stock_person_email = self.rejection_confirmed_by_user_id.partner_id.email.strip()
        stock_person_name = self.rejection_confirmed_by_user_id.name

        if company_email and stock_person_email:
            # Custom Email Template
            mail_template = self.env.ref('kin_stock.mail_templ_picking_rejection')
            ctx = {}
            ctx.update({'picking_id': self.id})
            the_url = self._get_stock_url('stock', 'all_picking', 'action_picking_tree_all', ctx)

            user_ids = []
            group_obj = self.env.ref('kin_stock.group_receive_stock_picking_rejected_email')
            for user in group_obj.users:
                if user.partner_id.email and user.partner_id.email.strip():
                    user_ids.append(user.id)
                    ctx = {'system_email': company_email,
                           'stock_person_name': stock_person_name,
                           'stock_person_email': stock_person_email,
                           'notify_person_email': user.partner_id.email,
                           'notify_person_name': user.partner_id.name,
                           'url': the_url,
                           'reason_for_rejection': reason_for_rejection,
                           }
                    mail_template.with_context(ctx).send_mail(self.id, force_send=False)

            if user_ids :
                self.message_subscribe_users(user_ids=user_ids)

                # Logs a Note
                self.message_post(_("Stock Items Physically Rejected with reason: " + reason_for_rejection + ""),
                                      subject='Stock Items Rejected')

    # def _compute_invoice(self):
    #     for picking in self:
    #         invoices = picking.sale_id.invoice_ids
    #         for line in picking.sale_id.invoice_ids:
    #             invoices |= line.invoice_lines.mapped('invoice_id')
    #         picking.invoice_ids = invoices
    #         picking.invoice_count = len(invoices)


        #source: https://github.com/odoo/odoo/issues/3922#issuecomment-262014118
            #Resolves this error message:  Exception: undefined get method !
    def __init__(self, pool, cr):
        super(StockPicking, self).__init__(pool, cr)
        for model, store in pool._store_function.iteritems():
            pool._store_function[model] = [
                x for x in store
                if x[0] != 'stock.picking' and x[1] != 'state']


    invoice_id = fields.Many2one('account.invoice')
    invoice_refund_id = fields.Many2one('account.invoice')
    supplier_invoice_refund_id = fields.Many2one('account.invoice')
    previous_picking_id = fields.Many2one('stock.picking',string="Parent Transfer Document")
    return_picking_ids = fields.One2many('stock.picking','previous_picking_id',string="Returns Transfer Documents")
    invoice_count = fields.Integer(compute="_compute_invoice_count", string='# of Invoices', copy=False, default=0)
    po_count = fields.Integer(compute="_compute_po_count", string='# of Purchase Orders', copy=False, default=0)
    so_count = fields.Integer(compute="_compute_so_count", string='# of Sales Orders', copy=False, default=0)
    #invoice_ids = fields.Many2many('account.invoice', compute="_compute_invoice", string='Invoices', copy=False)
    operation_type = fields.Selection(related='picking_type_id.code', store=True)
    shipment_ref = fields.Char(string='Shipment Reference')
    shipment_date = fields.Date(string='Shipped Date', help="The Date the Items were physically shipped")
    delivered_date = fields.Date(string="Delivered Date", help="The Date the items was delivered successfully")
    rejection_date = fields.Date(string="Rejection Date", help="The Date the items was rejected")
    shipment_date = fields.Date(string='Returned Date', help="The Date the Items were physically returned by the dispatcher")
    shipped_confirmed_by_user_id = fields.Many2one('res.users', string='Shipped Stock Confirmed By')
    delivery_confirmed_by_user_id = fields.Many2one('res.users', string='Delivery Stock Confirmed By')
    rejection_confirmed_by_user_id = fields.Many2one('res.users', string='Rejected Stock Confirmed By')
    salesperson_id = fields.Many2one('res.users',string="Sales Person", readonly=True)
    show_alert_box  = fields.Boolean(string="Show Alert Box")
    jnr_count = fields.Integer(compute="_compute_jnr_count", string='# of Journal Items', copy=False, default=0)
    move_ids = fields.One2many('account.move','picking_id',string='Journal Entry(s)',readonly=True)
    back_date = fields.Datetime(string='Force Stock Back Date')
    state = fields.Selection(selection_add=[('shipped', 'Shipped'),('delivered', 'Delivered'),('rejected', 'Rejected')])



class Message(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        ctx_copy= self.env.context.copy()
        ctx_copy.update({'mail_notify_force_send':False})
        res = super(Message,self.with_context(ctx_copy)).create(values)
        return res



class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'


    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        result1 = []
        if context is None:
            context = {}
        if context and context.get('active_ids', False):
            if len(context.get('active_ids')) > 1:
                raise UserError(_('Warning!'), _("You may only return one picking at a time!"))
        #res = super(StockReturnPicking, self).default_get(cr, uid, fields, context=context)
        res = {}
        record_id = context and context.get('active_id', False) or False
        uom_obj = self.pool.get('product.uom')
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        quant_obj = self.pool.get("stock.quant")
        chained_move_exist = False
        if pick:
            # if pick.state not in ['done','shipped','delivered','returned']:
            #     raise UserError(_("You may only return pickings that are Done, Shipped, Delivered, Returned States !"))

            for move in pick.move_lines:
                if move.move_dest_id:
                    chained_move_exist = True
                #Sum the quants in that location that can be returned (they should have been moved by the moves that were included in the returned picking)
                qty = 0
                quant_search = quant_obj.search(cr, uid, [('history_ids', 'in', move.id), ('qty', '>', 0.0), ('location_id', 'child_of', move.location_dest_id.id)], context=context)
                for quant in quant_obj.browse(cr, uid, quant_search, context=context):
                    if not quant.reservation_id or quant.reservation_id.origin_returned_move_id.id != move.id:
                        qty += quant.qty
                qty = uom_obj._compute_qty(cr, uid, move.product_id.uom_id.id, qty, move.product_uom.id)
                result1.append((0, 0, {'product_id': move.product_id.id, 'quantity': qty, 'move_id': move.id}))

            if len(result1) == 0:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)!"))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': result1})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': chained_move_exist})
            if 'parent_location_id' in fields and pick.location_id.usage == 'internal':
                res.update({'parent_location_id':pick.picking_type_id.warehouse_id and pick.picking_type_id.warehouse_id.view_location_id.id or pick.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': pick.location_id.id})
            if 'location_id' in fields:
                res.update({'location_id': pick.location_id.id})
        return res


    @api.multi
    def _create_returns(self):
        # Prevent copy of the carrier and carrier price when generating return picking
        # (we have no integration of returns for now)
        new_picking, pick_type_id = super(StockReturnPicking, self)._create_returns()

        prev_picking = self.env.context.get('active_id',False)
        if prev_picking and new_picking :
            picking_obj = self.env['stock.picking'].browse(prev_picking)
            new_picking_obj = self.env['stock.picking'].browse(new_picking)
            # save the previous picking id
            new_picking_obj.previous_picking_id = picking_obj
        return new_picking, pick_type_id




class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_default_option = fields.Boolean(string="Is Default Option", help="This must be set for at least one Stock Location. ")
    is_dont_show_location = fields.Boolean(string="Don't Show in List", help="Don't Show this location in the Stock Picking Form Location List. ")


    @api.model
    def create(self,vals):
        is_default_option = vals.get('is_default_option',False)
        if is_default_option :
            vals['usage'] = 'view'
        res = super(StockLocation,self).create(vals)
        return res


    @api.multi
    def write(self,vals):
        for rec in self :
            is_default_option = vals.get('is_default_option',None)
            if is_default_option == None :
                is_default_option = rec.is_default_option
            if is_default_option :
                vals['usage'] = 'view'
            res = super(StockLocation,rec).write(vals)
            return  res

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"


    is_create_invoice = fields.Boolean(string="Create Invoice after Operation")
    is_validate_invoice = fields.Boolean(string="Validate Invoice after Operation")
    # is_create_full_invoice = fields.Boolean(string="Create Full Invoice",help="Create Full Invoice of what has been ordered rather than what has been delivered")
    is_send_invoice_notification = fields.Boolean(string="Send Invoice Notification",help="This allows the system to automatically send invoice notification to the selected users in the user access right configuration")
    is_send_quality_control_notification = fields.Boolean(string="Send Quality Control Notification",help="This allows the system to automatically send quality control notification to the selected users in the user access right configuration")

class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"


    @api.model
    def create(self, vals):
        product_id = vals.get('product_id', False)
        if product_id:
            product_obj = self.env['product.product'].browse(product_id)
            description_picking = product_obj.description_picking
            if description_picking and len(description_picking.strip()) > 0:
                vals['name'] = description_picking
            else:
                vals['name'] = product_obj.name
        return super(StockPackOperation, self).create(vals)

    @api.onchange('qty_done')
    def change_qty_done(self):
        res = {}
        for rec in self :
            if rec.qty_done > rec.product_qty :
                res['warning'] = {'title' : "Error", 'message' : _('Delivery Qty is higher that the Quantity to be Delivered') }
                self.qty_done = 0
                return  res

    name = fields.Text('Description', required=True)




    # @api.depends('product_qty', 'price_unit', 'tax_ids')
    # def _compute_amount(self):
    #     for picking_line in self:
    #         taxes = picking_line.taxes_ids.compute_all(picking_line.price_unit, picking_line.currency_id, picking_line.product_qty, product=picking_line.product_id, partner=picking_line.partner_id)
    #
    #         self.price_total = taxes['total_included']
    #         self.price_tax = taxes['total_included'] - taxes['total_excluded']
    #         self.price_subtotal = taxes['total_excluded']


    # purchase_line_id = fields.Many2one('purchase.order.line')
    # sale_line_id = fields.Many2one('sale.order.line')
    price_subtotal = fields.Float(string='Subtotal')
    price_total = fields.Float( string='Total')
    price_tax = fields.Float( string='Tax')



class StockQuant(models.Model):
    _inherit = "stock.quant"


    def _create_account_move_line(self, cr, uid, quants, move, credit_account_id, debit_account_id, journal_id, context=None):
        # group quants by cost
        quant_cost_qty = {}
        for quant in quants:
            if quant_cost_qty.get(quant.cost):
                quant_cost_qty[quant.cost] += quant.qty
            else:
                quant_cost_qty[quant.cost] = quant.qty
        move_obj = self.pool.get('account.move')
        for cost, qty in quant_cost_qty.items():
            move_lines = self._prepare_account_move_line(cr, uid, move, qty, cost, credit_account_id, debit_account_id,
                                                         context=context)
            date = context.get('force_period_date', datetime.today().strftime('%Y-%m-%d'))
            new_move = move_obj.create(cr, uid, {'journal_id': journal_id,
                                                 'line_ids': move_lines,
                                                 'date': date,
                                                 'ref': move.picking_id.name,
                                                 'picking_id': move.picking_id.id }, context=context)
            move_obj.post(cr, uid, [new_move], context=context)



    @api.depends('inventory_value','qty')
    def _compute_unit_cost1(self):
        for rec in self :
            rec.cost1 = rec.inventory_value /  rec.qty

    @api.model
    def create(self,vals):
        vals['cost_price'] = vals['cost']
        return super(StockQuant,self).create(vals)


    def quants_reserve(self, cr, uid, quants, move, link=False, context=None):
        '''This function reserves quants for the given move (and optionally given link). If the total of quantity reserved is enough, the move's state
        is also set to 'assigned'

        :param quants: list of tuple(quant browse record or None, qty to reserve). If None is given as first tuple element, the item will be ignored. Negative quants should not be received as argument
        :param move: browse record
        :param link: browse record (stock.move.operation.link)
        '''
        toreserve = []
        reserved_availability = move.reserved_availability
        #split quants if needed
        comp_id = self.pool.get('res.company').search(cr, uid, [])[0]
        company_id = self.pool.get('res.company').browse(cr, uid, comp_id)
        for quant, qty in quants:
            if quant and not quant.is_added_landed_cost and company_id.is_enforce_landed_cost :
                raise UserError(_('Please Set Landed Cost for the Product Receipt'))
            if qty <= 0.0 or (quant and quant.qty <= 0.0):
                raise UserError(_('You can not reserve a negative quantity or a negative quant.'))
            if not quant:
                continue
            self._quant_split(cr, uid, quant, qty, context=context)
            toreserve.append(quant.id)
            reserved_availability += quant.qty
        #reserve quants
        if toreserve:
            self.write(cr, SUPERUSER_ID, toreserve, {'reservation_id': move.id}, context=context)
        #check if move'state needs to be set as 'assigned'
        rounding = move.product_id.uom_id.rounding
        if float_compare(reserved_availability, move.product_qty, precision_rounding=rounding) == 0 and move.state in ('confirmed', 'waiting')  :
            self.pool.get('stock.move').write(cr, uid, [move.id], {'state': 'assigned'}, context=context)
        elif float_compare(reserved_availability, 0, precision_rounding=rounding) > 0 and not move.partially_available:
            self.pool.get('stock.move').write(cr, uid, [move.id], {'partially_available': True}, context=context)




    cost1 = fields.Float(string='Unit Cost',compute="_compute_unit_cost1" )
    cost_price = fields.Float(string="Historical Cost", type='float', readonly=True)
    product_category_id = fields.Many2one('product.category',related='product_id.categ_id', store=True)
    is_added_landed_cost = fields.Boolean(string='Is Added Landed Cost',default=True)
    partner_id = fields.Many2one(related='reservation_id.partner_id',string="Partner",store=True)





class StockMoveExtend(models.Model):
    _inherit = "stock.move"

    @api.model
    def _prepare_picking_assign(self, move):
        """ Prepares a new picking for this move as it could not be assigned to
        another picking. This method is designed to be inherited.
        """
        res = super(StockMoveExtend, self)._prepare_picking_assign(move)
        if move.procurement_id and move.procurement_id.sale_line_id:
            res['po_ref'] = move.procurement_id.sale_line_id.order_id.client_order_ref
            res['salesperson_id'] = move.procurement_id.sale_line_id.order_id.user_id.id
        return res



    @api.multi
    def action_done(self):
        res = super(StockMoveExtend,self).action_done()

        for move in self :
            picking_id = move.picking_id

            if picking_id:
                back_date = picking_id.back_date or False

                if back_date:
                    if back_date > fields.Datetime.now():
                        raise UserError('Only Back-Dating of Stock Moves is Allowed')

                    move.date = back_date
                    for link in move.linked_move_operation_ids:
                        link.operation_id.date = back_date

                    move.quant_ids.sudo().write({'in_date': back_date})

        return res



    @api.model
    def create(self, vals):
        product_id = vals.get('product_id', False)
        if product_id:
            product_obj = self.env['product.product'].browse(product_id)

            description_picking = product_obj.description_picking
            if description_picking and len(description_picking.strip()) > 0:
                vals['name'] = description_picking
            else:
                name = vals.get('name',False)
                if name:
                    vals['name'] = name
                else:
                    vals['name'] = product_obj.name

        purchase_line_id = vals.get('purchase_line_id', False)
        if purchase_line_id:
            vals.update({'purchase_order_line_id': purchase_line_id})
        res = super(StockMoveExtend, self).create(vals)
        return res

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self, prod_id=False, loc_id=False, loc_dest_id=False, partner_id=False):
        res = super(StockMoveExtend,self).onchange_product_id(prod_id=prod_id, loc_id=loc_id, loc_dest_id=loc_dest_id, partner_id=partner_id)

        vals = res.get('value',False)
        product_obj = self.env['product.product'].browse(prod_id)
        if product_obj.description_picking and vals:
            vals['name'] = product_obj.description_picking
            res.update(vals)

        return  res

    name = fields.Text('Description', required=True, select=True)
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')

    #sale_line_id = fields.Many2one('sale.order.line')
    state = fields.Selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('waiting', 'Waiting Another Move'),
                                   ('confirmed', 'Waiting Availability'),
                                   ('assigned', 'Available and Reserved'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True, copy=False,
                 help= "* New: When the stock move is created and not yet confirmed.\n"\
                       "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"\
                       "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to me manufactured...\n"\
                       "* Available: When products are reserved, it is set to \'Available\'.\n"\
                       "* Done: When the shipment is processed, the state is \'Done\'.")





class StockWarehouseOrderPointExtend(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    is_create_procurement = fields.Boolean(string="Create Procurement")
    is_notify_email = fields.Boolean(string="Send Email Notification")


class ProcurementOrderExtend(models.Model):
    _inherit = "procurement.order"


    #The Kin_loading module needs the sale_order_line_id to be set
    @api.model
    def _run_move_create(self, procurement):
        vals = super(ProcurementOrderExtend, self)._run_move_create(procurement)
        if procurement.sale_line_id:
            vals.update({'sale_order_line_id': procurement.sale_line_id.id})
        return vals


    def _get_url(self, module_name,menu_id,action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name,menu_id)[1]
        fragment['model'] =  'purchase.order'
        fragment['view_type'] = 'form'
        fragment['action']= model_data.get_object_reference(module_name,action_id)[1]
        query = {'db': self.env.cr.dbname}

# for displaying tree view. Remove if you want to display form view
#         fragment['page'] = '0'
#         fragment['limit'] = '80'
#         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))

 # For displaying a single record. Remove if you want to display tree view

        fragment['id'] =  context.get("purchase_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


        return res


    def orderpoint_email(self,orderpoint_obj,qty_rounded,qty_available):
        tot_procs = []
        ctx_copy= self.env.context.copy()

        if orderpoint_obj :
            #Send Email Stock Level Notification
            is_notify_email = orderpoint_obj.is_notify_email
            is_create_procurement = orderpoint_obj.is_create_procurement
            company_email = self.env.user.company_id.email.strip()

            if is_create_procurement :
                orderpoint_procurment = self.with_context(ctx_copy)._prepare_orderpoint_procurement(orderpoint_obj, qty_rounded)
                proc_id = self.create(orderpoint_procurment)
                tot_procs.append(proc_id and proc_id.id)
                purchase_order_obj = proc_id.purchase_id

                if is_notify_email and company_email and purchase_order_obj :
                    # Custom Email Template
                    mail_template = self.env.ref('kin_stock.mail_templ_purchase_stock_level_email_with_url')
                    ctx = {}
                    ctx.update({'purchase_id':purchase_order_obj.id})
                    the_url = self._get_url('purchase','menu_purchase_rfq','purchase_rfq',ctx)
                    users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                    for user in users :
                        if user.has_group('kin_stock.group_receive_purchase_stock_level_email') and user.partner_id.email and user.partner_id.email.strip() :
                            ctx = {'system_email': company_email,
                                        'purchase_stock_email':user.partner_id.email,
                                        'partner_name': user.partner_id.name ,
                                        'url':the_url,
                                        'origin': orderpoint_obj.name,
                                        'product_name' : proc_id.product_id.name,
                                        'min_qty': orderpoint_obj.product_min_qty,
                                        'qty' : qty_available ,
                                        'location': orderpoint_obj.location_id.name
                                    }
                            mail_template.with_context(ctx).send_mail(proc_id.id,force_send=False)

            elif is_notify_email and company_email :
                # Custom Email Template
                mail_template = self.env.ref('kin_stock.mail_templ_purchase_stock_level_email')

                users = self.env['res.users'].search([('active','=',True),('company_id', '=', self.env.user.company_id.id)])

                for user in users :
                    if user.has_group('kin_stock.group_receive_purchase_stock_level_email') and user.partner_id.email and user.partner_id.email.strip() :
                        ctx = {'system_email': company_email,
                                'purchase_stock_email':user.partner_id.email,
                                'partner_name': user.partner_id.name ,
                                'origin': orderpoint_obj.name,
                                'product_name' : orderpoint_obj.product_id.name,
                                'min_qty': orderpoint_obj.product_min_qty,
                                'qty' : qty_available ,
                                'location': orderpoint_obj.location_id.name
                            }
                        mail_template.with_context(ctx).send_mail(orderpoint_obj.id,force_send=False)

        return  [tot_procs,self.env.cr]

    # This is still raising error for MTO
    # @api.model
    # def _procure_orderpoint_confirm(self,  use_new_cursor=False, company_id=False):
    #     '''
    #     Create procurement based on Orderpoint
    #
    #     :param bool use_new_cursor: if set, use a dedicated cursor and auto-commit after processing each procurement.
    #         This is appropriate for batch jobs only.
    #     '''
    #
    #     if self.env.context is None:
    #         ctx = {}
    #     ctx = self.env.context.copy()
    #     cr = self.env.cr
    #     if use_new_cursor:
    #         cr = openerp.registry(self.env.cr.dbname).cursor()
    #     orderpoint_obj = self.env['stock.warehouse.orderpoint']
    #     orderpoint_ids = []
    #     dom = company_id and [('company_id', '=', company_id)] or []
    #     orderpoint_ids = [ordp.id for ordp in orderpoint_obj.search( dom, order="location_id")]
    #
    #     prev_ids = []
    #     tot_procs = []
    #     while orderpoint_ids:
    #         ids = orderpoint_ids[:1000]
    #         del orderpoint_ids[:1000]
    #         product_dict = {}
    #         ops_dict = {}
    #         ops = orderpoint_obj.with_context(ctx).browse(ids)
    #
    #         #Calculate groups that can be executed together
    #         for op in ops:
    #             key = (op.location_id.id,)
    #             if not product_dict.get(key):
    #                 product_dict[key] = [op.product_id]
    #                 ops_dict[key] = [op]
    #             else:
    #                 product_dict[key] += [op.product_id]
    #                 ops_dict[key] += [op]
    #
    #         for key in product_dict.keys():
    #             ctx.update({'location': ops_dict[key][0].location_id.id})
    #             prod_qty =  product_dict[key][0].with_context(ctx)._product_available()
    #             #subtract_qty = self.env['stock.warehouse.orderpoint'].browse( [x.id for x in ops_dict[key]]).with_context(ctx).subtract_procurements_from_orderpoints()
    #             subtract_qty = self.pool.get('stock.warehouse.orderpoint').subtract_procurements_from_orderpoints(cr, self.env.user.id, [x.id for x in ops_dict[key]], context=ctx)
    #             for op in ops_dict[key]:
    #                 try:
    #                     prods = prod_qty[op.product_id.id]['virtual_available']
    #                     if prods is None:
    #                         continue
    #                     if float_compare(prods, op.product_min_qty, precision_rounding=op.product_uom.rounding) <= 0:
    #                         qty = max(op.product_min_qty, op.product_max_qty) - prods
    #                         reste = op.qty_multiple > 0 and qty % op.qty_multiple or 0.0
    #                         if float_compare(reste, 0.0, precision_rounding=op.product_uom.rounding) > 0:
    #                             qty += op.qty_multiple - reste
    #
    #                         if float_compare(qty, 0.0, precision_rounding=op.product_uom.rounding) < 0:
    #                             continue
    #
    #                         qty -= subtract_qty[op.id]
    #
    #                         qty_rounded = float_round(qty, precision_rounding=op.product_uom.rounding)
    #                         if qty_rounded > 0:
    #
    #                             res = self.with_context(ctx).orderpoint_email(op,qty_rounded,prod_qty[op.product_id.id]['qty_available'])
    #                             tot_procs = res[0]
    #                             cr = res[1]
    #                         if use_new_cursor:
    #                             cr.commit()
    #                 except OperationalError:
    #                     if use_new_cursor:
    #                         orderpoint_ids.append(op.id)
    #                         cr.rollback()
    #                         continue
    #                     else:
    #                         raise
    #         try:
    #             tot_procs.reverse()
    #             self.browse(tot_procs).run()
    #             tot_procs = []
    #             if use_new_cursor:
    #                 cr.commit()
    #         except OperationalError:
    #             if use_new_cursor:
    #                 cr.rollback()
    #                 continue
    #             else:
    #                 raise
    #
    #         if use_new_cursor:
    #             cr.commit()
    #         if prev_ids == ids:
    #             break
    #         else:
    #             prev_ids = ids
    #
    #     if use_new_cursor:
    #         cr.commit()
    #         cr.close()
    #     return {}


class AccountMoveStockExtend(models.Model):
    _name = 'account.move'
    _inherit = ['account.move','mail.thread']


    @api.model
    def create(self, vals):
        res = super(AccountMoveStockExtend,self).create(vals)
        picking_id = vals.get('picking_id', False)

        if picking_id:
            picking_obj = self.env['stock.picking'].browse(picking_id)
            picking_obj.move_id = res.id
            res.date = picking_obj.back_date or res.date

        return res

    picking_id = fields.Many2one('stock.picking', string="Inventory Transfer", track_visibility='onchange',
                                 readonly=True)


class AccountMoveLineExtend(models.Model):
    _inherit = 'account.move.line'

    picking_id = fields.Many2one(related='move_id.picking_id',string="Inventory Transfer",  store=True)


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'



    def _check_sum(self, cr, uid, landed_cost, context=None):
        """
        Will check if each cost line its valuation lines sum to the correct amount
        and if the overall total amount is correct also
        """
        costcor = {}
        tot = 0
        for valuation_line in landed_cost.valuation_adjustment_lines:
            if costcor.get(valuation_line.cost_line_id):
                costcor[valuation_line.cost_line_id] += valuation_line.additional_landed_cost
            else:
                costcor[valuation_line.cost_line_id] = valuation_line.additional_landed_cost
            tot += valuation_line.additional_landed_cost

        prec = self.pool['decimal.precision'].precision_get(cr, uid, 'Account')
        # float_compare returns 0 for equal amounts
        res = not bool(float_compare(tot, landed_cost.amount_total, precision_digits=prec))
        # for costl in costcor.keys():
        #     if float_compare(costcor[costl], costl.price_unit, precision_digits=prec):
        #         res = False
        return res


    def button_validate(self, cr, uid, ids, context=None):
        quant_obj = self.pool.get('stock.quant')

        for cost in self.browse(cr, uid, ids, context=context):
            if cost.state != 'draft':
                raise UserError(_('Only draft landed costs can be validated'))
            if not cost.valuation_adjustment_lines or not self._check_sum(cr, uid, cost, context=context):
                raise UserError(_('You cannot validate a landed cost which has no valid valuation adjustments lines. Did you click on Compute?'))
            move_id = self._create_account_move(cr, uid, cost, context=context)
            for line in cost.valuation_adjustment_lines:
                if not line.move_id:
                    continue
                per_unit = line.final_cost / line.quantity
                diff = per_unit - line.former_cost_per_unit

                # If the precision required for the variable diff is larger than the accounting
                # precision, inconsistencies between the stock valuation and the accounting entries
                # may arise.
                # For example, a landed cost of 15 divided in 13 units. If the products leave the
                # stock one unit at a time, the amount related to the landed cost will correspond to
                # round(15/13, 2)*13 = 14.95. To avoid this case, we split the quant in 12 + 1, then
                # record the difference on the new quant.
                # We need to make sure to able to extract at least one unit of the product. There is
                # an arbitrary minimum quantity set to 2.0 from which we consider we can extract a
                # unit and adapt the cost.
                curr_rounding = line.move_id.company_id.currency_id.rounding
                diff_rounded = float_round(diff, precision_rounding=curr_rounding)
                diff_correct = diff_rounded
                quants = line.move_id.quant_ids.sorted(key=lambda r: r.qty, reverse=True)
                quant_correct = False
                if quants\
                        and float_compare(quants[0].product_id.uom_id.rounding, 1.0, precision_digits=1) == 0\
                        and float_compare(line.quantity * diff, line.quantity * diff_rounded, precision_rounding=curr_rounding) != 0\
                        and float_compare(quants[0].qty, 2.0, precision_rounding=quants[0].product_id.uom_id.rounding) >= 0:
                    # Search for existing quant of quantity = 1.0 to avoid creating a new one
                    quant_correct = quants.filtered(lambda r: float_compare(r.qty, 1.0, precision_rounding=quants[0].product_id.uom_id.rounding) == 0)
                    if not quant_correct:
                        quant_correct = quant_obj._quant_split(cr, uid, quants[0], quants[0].qty - 1.0, context=context)
                    else:
                        quant_correct = quant_correct[0]
                        quants = quants - quant_correct
                    diff_correct += (line.quantity * diff) - (line.quantity * diff_rounded)
                    diff = diff_rounded

                quant_dict = {}
                for quant in quants:
                    quant_dict[quant.id] = quant.cost + diff
                if quant_correct:
                    quant_dict[quant_correct.id] = quant_correct.cost + diff_correct
                for key, value in quant_dict.items():
                    quant_obj.write(cr, SUPERUSER_ID, key, {'cost': value,'is_added_landed_cost': True}, context=context)
                qty_out = 0
                for quant in line.move_id.quant_ids:
                    if quant.location_id.usage != 'internal':
                        qty_out += quant.qty
                self._create_accounting_entries(cr, uid, line, move_id, qty_out, context=context)
            self.write(cr, uid, cost.id, {'state': 'done', 'account_move_id': move_id}, context=context)
            self.pool.get('account.move').post(cr, uid, [move_id], context=context)
        return True





class StockMoveOperationLinkExtend(models.Model):

    _inherit = "stock.move.operation.link"

    @api.model
    def create(self,vals):
        stock_move_obj = self.env["stock.move"]
        stock_pack_oper_obj = self.env['stock.pack.operation']

        oper_id = vals.get('operation_id')
        pack_oper = stock_pack_oper_obj.browse(oper_id)

        move_id = vals.get('move_id')
        move_obj = stock_move_obj.browse(move_id)
        # This is for Stock locations that have parent-child relationship hierarchy.
        # Corrects the issue of using the parent location instead of the child location that was used in the child stock operation.
        move_obj.location_id = pack_oper.location_id

        res = super(StockMoveOperationLinkExtend,self).create(vals)
        return res



class ResCompany(models.Model):
    _inherit = "res.company"

    is_enforce_landed_cost = fields.Boolean(string='Enforce Landed Cost before Goods Delivery',default=1)