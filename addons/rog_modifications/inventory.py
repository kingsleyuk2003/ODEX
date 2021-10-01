# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _, SUPERUSER_ID


class StockReading(models.Model):
    _name = 'stock.reading'
    _inherit = ['mail.thread']


    @api.multi
    def button_confirm(self):
        self.state = 'confirm'
        return

    @api.multi
    def button_approve(self):
        self.state = 'approve'
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        return

    @api.multi
    def button_reset(self):
        self.state = 'draft'
        return


    @api.depends('lines_ids.physical_stock')
    def _compute_amount(self):
        total = 0
        for line in self.lines_ids:
            total += line.physical_stock
        self.total_physical_qty = total


    read_date = fields.Date(string='Reading Date')
    user_id = fields.Many2one('res.users',string='User',default=lambda self: self.env.user.id)
    lines_ids = fields.One2many('stock.reading.lines','stock_reading_id',string='Lines')
    company_id = fields.Many2one('res.company', string='Company', select=True,default=lambda self: self.env.user.company_id)
    total_physical_qty = fields.Float(string='Total Daily Physical Qty (ltrs)', compute='_compute_amount',  readonly=True, store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


class StockReadingLines(models.Model):
    _name = 'stock.reading.lines'

    stock_location_id = fields.Many2one('stock.location',string='Stock Location')
    physical_stock = fields.Float(string='Physical Stock (ltrs)')
    product_id = fields.Many2one('product.product',string='Product')
    read_date = fields.Date(related='stock_reading_id.read_date', string='Reading Date',store=True)
    company_id = fields.Many2one('res.company',related='stock_reading_id.company_id' ,string='Company')
    stock_reading_id = fields.Many2one('stock.reading', string='Stock Reading')
    state = fields.Selection(related='stock_reading_id.state', store=True, string='Status')



class StockPicking(models.Model):
    _inherit = "stock.picking"

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
    def button_bank_inspection_on_discharged_product(self):
        self.env.cr.execute("update stock_picking set state = 'bank_inspection_on_discharged_product' where id = %s" % (self.id))
        self.email_dispatch('Bank Inspection on Discharged Product')


    @api.multi
    def button_bank_monitoring_stock(self):
        self.env.cr.execute(
            "update stock_picking set state = 'bank_monitoring_stock' where id = %s" % (self.id))
        self.email_dispatch('Bank Monitoring of Stock')




    state = fields.Selection(selection_add=[
        ('bank_inspection_on_discharged_product', 'Bank Inspection on Discharged Product'),
        ('bank_monitoring_stock', 'Bank Monitoring of Stock')])

