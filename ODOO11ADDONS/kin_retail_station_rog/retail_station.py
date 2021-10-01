# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
#import  time





#Just as a memo, to help people memorize/remember the bank lodgements
class BankLodgement(models.Model):
    _name = 'kin.bank.lodgement'

    @api.multi
    def action_validate(self):
        account_payment_obj = self.env['account.payment']
        retail_station_id = self.retail_station_id

        if not retail_station_id.partner_ids:
            raise UserError(_('Please Set a Partner for this retail Station - %s. Contact the Admin' % retail_station_id.name ))

        if self.stock_control_id and self.stock_control_id.state not in ('approve','open') :
            raise UserError(_('Please wait for the Stock Control to be approved first, before posting the bank lodgements'))


        acc_pay = {
            'payment_type': 'inbound',
            'payment_type_copy': 'inbound',
            'journal_id': self.journal_id.id,
            'payment_date': self.lodge_date,
            'amount': self.amount,
            'ref_no': self.teller_no,
            'payment_method_id': 1,  # Manual payment
            'partner_id': retail_station_id.partner_ids[0].id,
            'partner_type': 'customer',
            'stock_control_id': self.stock_control_id.id,
        }
        pg = account_payment_obj.create(acc_pay)

        pg.post()
        self.payment_group_id = pg.id
        return pg

    @api.multi
    def action_cancel(self):
        self.payment_group_id.cancel()
        res = self.payment_group_id.unlink()
        if self.stock_control_id:
            self.stock_control_id._compute_posted_payment()
        return res

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('bl_code') or 'New'
        res = super(BankLodgement, self).create(vals)
        return res

    @api.multi
    def btn_view_stock_control(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Control'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.stock.control',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_control_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.multi
    def btn_view_payment_group(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Payment Group'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.payment_group_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_control_id')
    def _compute_stock_control_count(self):
        for rec in self:
            rec.stock_control_count = len(rec.stock_control_id)


    @api.depends('payment_group_id')
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_group_id)

    def _get_user_retail_station(self):
        user = self.env.user
        retail_station_obj = self.env['kin.retail.station']
        retail_station = retail_station_obj.search([('retail_station_manager_id','=',user.id)])
        return retail_station and retail_station[0].id

    @api.onchange('amount')
    def populate_date(self):
        self.lodge_date = self.env.context.get('stock_control_date')


    name = fields.Char(string='ID',readonly=True)
    lodge_date = fields.Date(string='Date')
    amount = fields.Monetary(string='Amount (NGN)')
    journal_id = fields.Many2one('account.journal',string='Payment Method',domain=[('type', 'in', ['bank','cash'])],ondelete='restrict')
    teller_no = fields.Char(string='Teller / ID No.')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,ondelete='restrict')
    stock_control_id = fields.Many2one('kin.stock.control','Stock Control',required=True,ondelete='cascade')
    payment_group_id = fields.Many2one('account.payment',string='Payment')
    stock_control_count = fields.Float(digits=dp.get_precision('Product Price'),compute="_compute_stock_control_count", string='# of Stock Control',
                                         copy=False, default=0)
    payment_count = fields.Float(digits=dp.get_precision('Product Price'),compute="_compute_payment_count", string='# of Payment Group',
                                         copy=False, default=0)
    retail_station_id = fields.Many2one('kin.retail.station', string='Retail Station',default=_get_user_retail_station,ondelete='restrict')



class RetailStationExpense(models.Model):
    _name = 'kin.retail.station.expense'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft' and not self.env.user.has_group('base.group_no_one'):
                # Don't allow deletion of stock control
                raise UserError(_('Sorry, this Retail Station Expenses cannot be deleted. Please contact your admin'))

        return super(RetailStationExpense, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('rex_code') or 'New'
        res = super(RetailStationExpense, self).create(vals)

        return res

    @api.multi
    def btn_view_stock_control(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Control'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.stock.control',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_control_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_control_id')
    def _compute_stock_control_count(self):
        for rec in self:
            rec.stock_control_count = len(rec.stock_control_id)

    @api.onchange('amount')
    def populate_date(self):
        self.exp_date = self.env.context.get('stock_control_date')

    name = fields.Char(string='ID',readonly=True)
    exp_date = fields.Date(string='Date')
    description = fields.Char(string='Description')
    amount =  fields.Monetary(string='Amount')
    expense_type = fields.Selection([
        ('gmd_consumption', 'GMD Consumption'),
        ('ago_generator', 'AGO for Generator'),
        ('maintenance_charges', 'Maintenance Charges'),
        ('station_car_fueling', 'Station Car Fueling'),
        ('other_expenses', 'Other Expenses')
    ], string='Expenses' )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done','Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    retail_station_id = fields.Many2one('kin.retail.station',string='Retail Station',ondelete='restrict')
    retail_station_manager_id = fields.Many2one('res.users', related='retail_station_id.retail_station_manager_id',
                                                string='Retail Station Manager', store=True,ondelete='restrict')
    stock_control_id = fields.Many2one('kin.stock.control',string='Stock Control',ondelete='cascade')
    stock_control_count = fields.Integer(compute="_compute_stock_control_count", string='# of Stock Control',
                                         copy=False, default=0)
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,ondelete='restrict')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def btn_view_bank_lodgement(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Bank lodgements'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.bank.lodgement',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.bank_lodgement_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.multi
    def btn_view_stock_control(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Control'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.stock.control',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_control_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_control_id')
    def _compute_stock_control_count(self):
        for rec in self:
            rec.stock_control_count = len(rec.stock_control_id)

    @api.depends('bank_lodgement_ids')
    def _compute_bank_lodgement_count(self):
        for rec in self:
            rec.bank_lodgement_count = len(rec.bank_lodgement_ids)


    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        if self.stock_control_id :
            self.stock_control_id._compute_posted_payment()
        return res


    bank_lodgement_ids = fields.One2many('kin.bank.lodgement', 'payment_group_id' , string='Bank Lodgements')
    bank_lodgement_count = fields.Integer(compute="_compute_bank_lodgement_count", string='# of Bank Lodgements',copy=False, default=0)
    stock_control_id = fields.Many2one('kin.stock.control',string='Stock Control',ondelete='cascade')
    stock_control_count = fields.Integer(compute="_compute_stock_control_count", string='# of Stock Control',
                                         copy=False, default=0)


class RetailShiftSales(models.Model):
    _name = 'kin.retail.sale'
    _inherit = ['mail.thread']
    _description = 'Retail Station Sale'
    _order = 'retail_sale_date desc'

    @api.multi
    def copy(self, default=None):
        raise UserError(_('Duplication not allowed. Please use the create button'))


    @api.multi
    def unlink(self):
        for rec in self:
            if  rec.state not in ['draft','cancel'] :
                raise UserError(_('Sorry, Non-draft/cancelled shift sales cannot be deleted'))

        return super(RetailShiftSales, self).unlink()

    @api.multi
    def btn_view_stock_control(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Control'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.stock.control',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_control_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_control_id')
    def _compute_stock_control_count(self):
        for rec in self:
            rec.stock_control_count = len(rec.stock_control_id)


    @api.depends('total_cash_collected','total_pos_card','total_voucher','other_payment','pump_sale_ids.price_subtotal')
    def _amount_all(self):
        for retail_sale in self:
            total_ago_sales_qty = 0
            total_kero_sales_qty = 0
            total_pms_sales_qty = 0
            total_pump_sales_price_pms = 0
            total_pump_sales_price_ago = 0
            total_pump_sales_price_kero = 0

            for ps in retail_sale.pump_sale_ids:
                if ps.product_id.white_product == 'pms':
                    total_pms_sales_qty += ps.sale_qty
                    total_pump_sales_price_pms += ps.price_subtotal
                elif ps.product_id.white_product == 'ago':
                    total_ago_sales_qty += ps.sale_qty
                    total_pump_sales_price_ago += ps.price_subtotal
                elif ps.product_id.white_product == 'kero':
                    total_kero_sales_qty += ps.sale_qty
                    total_pump_sales_price_kero += ps.price_subtotal

                total_pump_sales_price = total_pump_sales_price_pms + total_pump_sales_price_ago + total_pump_sales_price_kero

                retail_sale.update({
                'total_pms_sales_qty': total_pms_sales_qty,
                'total_pms_cash_collected': total_pump_sales_price_pms,
                'total_ago_sales_qty': total_ago_sales_qty,
                'total_ago_cash_collected': total_pump_sales_price_ago,
                'total_kero_sales_qty': total_kero_sales_qty,
                'total_kero_cash_collected': total_pump_sales_price_kero,
                'total_cash_sales' : total_pump_sales_price,
                'cash_difference' : total_pump_sales_price - retail_sale.total_cash_collected - retail_sale.total_pos_card - retail_sale.total_voucher - retail_sale.other_payment
            })


    @api.onchange('retail_station_id')
    def populate_lines(self):
        fuel_pump_obj = self.env['kin.fuel.pump']
        self.pump_sale_ids.unlink()
        self.shift_id = False
        fuel_pumps = fuel_pump_obj.search([('retail_station_id', "=", self.retail_station_id.id)])

        line_pumps = []
        for fuel_pump in fuel_pumps:
            line_pumps += [(0, 0, {
                'pump_id': fuel_pump.id,
                'product_price': fuel_pump.selling_price,
                'meter_start': fuel_pump.totalizer
            })
                           ]
        self.pump_sale_ids = line_pumps
        return


    @api.multi
    def action_confirm(self):


        if self.total_cash_collected<= 0 :
            raise UserError(_('Please put the amount you collected during the pump sales'))

        for pump_sale in self.pump_sale_ids :
            if pump_sale.meter_end < pump_sale.meter_start:
                raise UserError(_(
                    'Meter End Reading for Pump Meter -%s with value (%s) Cannot be lower than Meter Start Reading with value (%s).') % (
                                pump_sale.pump_id.name, pump_sale.meter_end, pump_sale.meter_start))

            # if meter end does not match totalizer before approving, then let the user delete and recreat
            if pump_sale.meter_start != pump_sale.pump_id.totalizer :
                raise UserError(_('Meter Start for pump - %s, does not match the totalizer value. Please delete this shift sale record and re-create a new record to get the updated totalizer value as the meter start value' % (pump_sale.pump_id.name)))

        user_ids = []
        station_manager = self.retail_station_manager_id
        if station_manager:
            user_ids.append(station_manager.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_('A New Shift Pump Sales Record from %s has been Created with ID %s.') % (
                self.shift_supervisor_id.name, self.name),
                              subject='A New Stock Control Record has been Created ', subtype='mail.mt_comment')

        return self.write({'state': 'confirm'})


    @api.multi
    def action_approve(self):
        if self.state == 'approve':
            raise UserError(_('This record has been previously approved. Please refresh your browser'))

        for pump_sale in self.pump_sale_ids :
            pump_sale.pump_id.totalizer = pump_sale.meter_end

        return self.write({'state': 'approve'})


    @api.multi
    def action_draft(self):
        sales = self.filtered(lambda s: s.state in ['cancel'])
        sales.populate_lines()
        sales.write({'state': 'draft'})

    @api.multi
    def action_cancel(self):

        if self.state == 'cancel':
            raise UserError(_('This record has been previously cancelled. Please refresh your browser'))

        # No cancellation of current shift sale before the latest shift sale record, in other to prevent wrong value in the meter start reading
        retail_sale_recent = self.search(
            [('retail_station_id', '=', self.retail_station_id.id), ('retail_sale_date', '>', self.retail_sale_date)])
        if retail_sale_recent:
            raise UserError(
                _(
                    "Sorry, You cannot cancel this pump sale record because there is a more recent pump sale record that has been created already"))

        if self.stock_control_id :
            raise UserError(_('Sorry, An Existing Day Pump Sales with Stock Control Record already Exist. You may contact the retail manager to delete the day pump sales before you can edit this shift sales record'))

        # for pump_sale in self.pump_sale_ids:
        #     if pump_sale.meter_start < pump_sale.pump_id.totalizer : #possibly try to cancel a shift pump sale after a recent one has been approved to update the totalizer
        #         raise UserError(_('The Totalizer has been previously updated by a more recent shift pump sale. Ensure you delete all the following pump sales before cancelling this record'))
        #     pump_sale.pump_id.totalizer = pump_sale.meter_start

        #reverse the totalizer value
        for ps in self.pump_sale_ids :
            if ps.meter_end != ps.pump_id.totalizer :
                raise UserError(_('Meter End for pump - %s, does not match the totalizer value (%s). Please cancel other previous shift sale record for the day, before cancelling this record ' % (ps.pump_id.name,ps.pump_id.totalizer)))

            ps.pump_id.totalizer = ps.meter_start


        self.write({'state': 'cancel'})

    @api.multi
    def action_cancel_retail_station_manager(self):
        self.action_cancel()

    @api.model
    def create(self, vals):
        retail_station_id = vals.get('retail_station_id')
        date = vals.get('retail_sale_date')

        # No Backdating of a retail shift sales before the most recent ones
        retail_sale_obj = self.env['kin.retail.sale']
        retail_sales_later = retail_sale_obj.search([('retail_station_id', '=', retail_station_id), ('retail_sale_date', '>', date)])
        if retail_sales_later:
            raise UserError(
                _("Sorry, You cannot back-date a retail pump sales shift before the most recent sales shift"))


        shift_id = vals.get('shift_id')
        retail_sales = self.search([('retail_station_id','=',retail_station_id),('retail_sale_date','=',date),('shift_id','=',shift_id)])
        if len(retail_sales) > 0 : #since it is still new shift sales
            raise UserError(_("Sorry, There is a pump shift sales record with ID - %s for %s for %s for shift %s" % (retail_sales[0].name,retail_sales[0].retail_station_id.name,datetime.strptime(retail_sales[0].retail_sale_date , "%Y-%m-%d").strftime("%d-%m-%Y"),retail_sales[0].shift_id.name)))

        retail_sales_close = self.search([('retail_station_id', '=', retail_station_id), ('state', '!=', 'approve')])
        if retail_sales_close:
            raise UserError(_("Sorry, There is still an On-going Shift with ID - %s for %s for %s for shift %s, that should be approved and closed by the retail manager, before starting your new shift"  % (retail_sales_close[0].name,retail_sales_close[0].retail_station_id.name,datetime.strptime(retail_sales_close[0].retail_sale_date , "%Y-%m-%d").strftime("%d-%m-%Y"),retail_sales_close[0].shift_id.name) ))

        pump_sale_ids = vals.get('pump_sale_ids', False)
        if pump_sale_ids:
            l = []
            for pump_line in pump_sale_ids:
                l.append(pump_line[2]['pump_id'])
            if set([x for x in l if l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
                raise UserError(_(
                    'Duplicate Sales Pump detected. Only One Pump is allowed at a time for each retail sales'))

        #Retail Station allowed by user
        user = self.env.user
        retail_station_obj = self.env['kin.retail.station']
        retail_station = retail_station_obj.search([('shift_supervisor_ids', '=', user.id),('id', '=', retail_station_id)])
        if not retail_station :
            raise UserError(_('Sorry, %s is not a supervisor for %s' % (user.name,self.env['kin.retail.station'].browse(retail_station_id).name)))

        vals['name'] = self.env['ir.sequence'].next_by_code('rs_code') or 'New'
        res = super(RetailShiftSales, self).create(vals)

        return res

    @api.multi
    def write(self, vals):
        res = super(RetailShiftSales, self).write(vals)

        # Retail Station allowed by user
        #user = self.env.user  ##TODO Crosscheck this because user cannot always be admin. Temporary fix is below
        user = self.shift_supervisor_id
        retail_station_obj = self.env['kin.retail.station']
        retail_station = retail_station_obj.search([('shift_supervisor_ids', '=', user.id), ('id', '=', self.retail_station_id.id)])
        if not retail_station  :
            raise UserError(_('Sorry, %s is not a supervisor for %s' % (user.name, self.retail_station_id.name)))

        retail_sales = self.search([('retail_station_id', '=', self.retail_station_id.id), ('retail_sale_date', '=', self.retail_sale_date),
                                      ('shift_id', '=', self.shift_id.id)])
        if len(retail_sales) > 1: #since this is the only record
            raise UserError(_("Sorry, There is a pump shift sales record with ID - %s for %s for %s for shift %s" % (
            retail_sales[0].name, retail_sales[0].retail_station_id.name,
            datetime.strptime(retail_sales[0].retail_sale_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
            retail_sales[0].shift_id.name)))

        l = []
        for sale in self.pump_sale_ids :
            l.append(sale.pump_id.id)
        if set([x for x in l if l.count(x) > 1]):  #see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
            raise  UserError(_('Duplicate Pump detected. Only One Pump is allowed at a time for each daily sales'))

        return res


    @api.multi
    def action_disapprove(self, msg):
        user_ids = []
        shift_supervisor = self.shift_supervisor_id
        if shift_supervisor:
            user_ids.append(shift_supervisor.id)
            self.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            user = self.env.user
            self.message_post(_(
                'The Retail Sales %s has been DisApproved by %s. Reason for Disapproval: %s. You may correct and Re-Submit again for approval ') % (
                                  self.name, user.name, msg),
                              subject='The Retail Sales (%s) has been Dis-Approved by %s' % (self.name, user.name),
                              subtype='mail.mt_comment')

        return self.write({'state': 'draft', 'disapprove_id': user.id,
                           'disapprove_date': datetime.today(), 'reason_disapprove': msg})

    @api.depends('retail_station_id')
    def _compute_retail_station_manager(self):
        self.retail_station_manager_id = self.retail_station_id.retail_station_manager_id

    def _get_user_retail_station(self):
        user = self.env.user
        retail_station_obj = self.env['kin.retail.station']
        retail_station = retail_station_obj.search([('shift_supervisor_ids','=',user.id)])
        return retail_station and retail_station[0].id

    @api.depends('retail_sale_time_end','retail_sale_time_start')
    def _compute_time_interval(self):
        if self.retail_sale_time_end  and self.retail_sale_time_start :
            self.time_interval = datetime.strptime(self.retail_sale_time_end , DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(self.retail_sale_time_start , DEFAULT_SERVER_DATETIME_FORMAT)


    name = fields.Char('ID')
    retail_sale_date = fields.Date('Date')
    retail_sale_time_start = fields.Datetime('Start DateTime')
    retail_sale_time_end = fields.Datetime('End DateTime')
    time_interval = fields.Char('Time Interval',compute='_compute_time_interval',store=True)
    total_cash_sales = fields.Monetary('Total Cash Sales (NGN)', compute='_amount_all', store=True,
                                           help="Total Cash Sales for All White Products + Cash In Till")
    total_cash_collected = fields.Monetary('Total Cash Collected (NGN)',  help="Total Cash Collected from the Sales")
    total_pos_card = fields.Monetary('Total Card POS Payment (NGN)', help="Total Card Payment through POS from the Sales")
    total_voucher = fields.Monetary('Total Voucher Payment (NGN)', help="Total Voucher Received for Sales")
    other_payment = fields.Monetary('Other form of Payment (NGN)', help="Other form of Payment")
    cash_difference = fields.Monetary('Variance/Cash Difference (NGN)',  compute='_amount_all', help="Total Cash Sales - Total Cash Collected - Total Card POS Payment - Other Payment")
    pump_sale_ids = fields.One2many('kin.pump.sale', 'retail_sale_id', string='Pump Sales')
    tank_dipping_ids = fields.One2many('kin.tank.dipping', 'retail_sale_id', string='Tank Dippings')
    retail_station_id = fields.Many2one('kin.retail.station', string='Retail Station',default=_get_user_retail_station,ondelete='restrict')
    retail_station_manager_id = fields.Many2one('res.users', compute='_compute_retail_station_manager',
                                                string='Retail Station Manager', store=True,ondelete='restrict')
    shift_supervisor_id = fields.Many2one('res.users',  string='Shift Supervisor', default=lambda self: self.env.user.id,ondelete='restrict')
    shift_id = fields.Many2one('kin.shift', string='Sales Shift',ondelete='restrict')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed and Submitted by Supervisor'),
        ('approve', 'Approved and Closed by Retail Manager'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    reason_disapprove = fields.Text(string='Reason for Dis-Approval')
    disapprove_id = fields.Many2one('res.users', string='Disapproved By',ondelete='restrict')
    disapprove_date = fields.Datetime(string='Disapproved Date')

    # store=True allows the field to be computed once and saved. It does not allow further computation on record read. But removing it will allow computation on record read
    # But you can use @api.depends (NOT @api.onchange) to calculate the fields that are with store=True
    # Note that @api.depends does the work of @api.onchange. Also not @api.onchange does not persist  store=True fields
    # @api.depends() should be used together with .update() and compute=''. While the @api.depends() with .update() allows computation on the client browser for readonly fields, but does not get saved on the database because the fields are readonly, The compute='' does the RE-computation on the server side, which allows the readonly field to be RE-calculated and saved on the database
    total_pms_sales_qty = fields.Float('Total Sales Qty. (ltrs)',digits=dp.get_precision('Product Price'), compute='_amount_all', store=True)
    total_pms_cash_collected = fields.Monetary('Total Cash Sales (NGN)', compute='_amount_all', store=True,
                                               help="Total PMS Pump Sales Qty. * PMS Selling Price")
    total_ago_sales_qty = fields.Float('Total Sales Qty. (ltrs)',digits=dp.get_precision('Product Price'), compute='_amount_all', store=True)
    total_ago_cash_collected = fields.Monetary('Total Cash Sales (NGN)', compute='_amount_all', store=True,
                                               help="Total AGO Pump Sales Qty. * AGO Selling Price")
    total_kero_sales_qty = fields.Float('Total Sales Qty (ltrs).',digits=dp.get_precision('Product Price'), compute='_amount_all', store=True)
    total_kero_cash_collected = fields.Monetary('Total KERO Sales (NGN)' , compute='_amount_all', store=True,
                                               help="Total KERO Pump Sales Qty. * KERO Selling Price")
    stock_control_id = fields.Many2one('kin.stock.control',string='Stock Control')
    stock_control_count = fields.Integer(compute="_compute_stock_control_count", string='# of Stock Controls', copy=False, default=0)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id,readonly=True,ondelete='restrict')

#The Day Sales with Stock Control and Other things
class StockControl(models.Model):
    _name = 'kin.stock.control'
    _inherit = ['mail.thread']
    _description = 'Stock Control'
    _order = 'stock_control_date desc'

    @api.multi
    def copy(self, default=None):
        raise UserError(_('Duplication not allowed. Please use the create button'))

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft','cancel']:
                raise UserError(_('Sorry, Non-draft/Cancelled Stock Control cannot be deleted'))

        return super(StockControl, self).unlink()

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

    @api.depends('move_ids')
    def _compute_jnr_count(self):
        for rec in self:
            rec.jnr_count = len(rec.move_ids)


    @api.multi
    def btn_view_shift_sale(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Shift Sales'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.retail.sale',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.retail_sale_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('retail_sale_ids')
    def _compute_shift_count(self):
        for rec in self:
            rec.shift_sale_count = len(rec.retail_sale_ids)

    @api.multi
    def action_create_journal_entry(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('account.action_move_journal_line')
        form_view_id = model_data_obj.xmlid_to_res_id('account.view_move_form')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'domain': action.domain,
            'context': {'default_stock_control_id': self.id},
            'res_model': action.res_model,
            'target': 'new'
        }

    @api.multi
    def btn_view_payment_group(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Payment Group'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.payment_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }


    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)


    @api.multi
    def action_register_payment(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('account.action_account_payments')
        form_view_id = model_data_obj.xmlid_to_res_id('account.view_account_payment_form')


        partner_id = self.retail_station_id.partner_ids[0].id
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'domain':action.domain,
            'context': {'default_partner_id':partner_id,'default_partner_type':'customer','default_stock_control_id':self.id,'default_payment_type': 'inbound'},
            'res_model': action.res_model,
            'target': 'new'
        }


    def action_approved(self):
        if self.state == 'approve' :
            raise UserError(_('This record has been previously approved. Please refresh your browser'))

        #no Pending Product Received Record
        retail_station_id  = self.retail_station_id
        pending_prr_obj = self.env['product.received.register'].search(
            [('to_stock_location_id', '=', retail_station_id.id), ('state', 'in', ['draft', 'transit'])])

        for pending_prr in pending_prr_obj:
            if pending_prr and not pending_prr.is_company_product:
                receiving_date = pending_prr.receiving_date
                pending_prr_name = pending_prr.name
                retail_station_name = retail_station_id.name
                #in order to avoid wrong closing stock for the tank
                raise UserError(
                    _(
                        "Sorry, there is a previously created product received record in %s state, with ID - %s for %s with date %s, that is still pending validation by the retail manager. Please contact the retail manager to validate/delete the product received record" % (
                            pending_prr.state,pending_prr_name, retail_station_name,
                            datetime.strptime(receiving_date, "%Y-%m-%d").strftime("%d-%m-%Y"))))


        # No pending un-approved previous stock control for each retail station, so that there is no wrong update of the stock value for the tanks
        pending_stock_control_obj = self.search(
            [('retail_station_id', '=', self.retail_station_id.id), ('state', 'in', ['draft', 'confirm','cancel'])])
        if len(pending_stock_control_obj) > 1:
            raise UserError(_('Please delete any other draft/confirmed/cancelled day report, before this record can be approved'))

        user_ids = []
        group_obj = self.env.ref('account.group_account_invoice')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_('Dear Accountant, The Stock Control Record with ID (%s) for the Retail Station %s has been Approved by %s. You may now Register Payment for the Cash Received') % (
        self.name, self.retail_station_id.name,self.env.user.name),
                              subject='Stock Control Record has been Approved ', subtype='mail.mt_comment')

        #save latest cash in till
        self.retail_station_id.previous_cash_in_till = self.retail_station_id.latest_cash_in_till
        self.retail_station_id.latest_cash_in_till = self.cash_in_till

        # Post the stock gain and loss
        self.post_stock_gain_loss()

        stock_move_obj = self.env['stock.move']

        for td in self.tank_dipping_ids:
            if td.stock_at_hand != td.tank_id.stock_level :
                raise UserError(_(
                    'Sorry, the tank %s current stock level %s qty, does not match the report stock at hand %s qty, which may have been due to another process. Please use the cancel button to reset and update the tank dipping records to the current values') % (
                                td.tank_id.name,td.tank_id.stock_level,td.stock_at_hand))

            # update the Stock Level for the tanks
            td.tank_id.current_stock_received = 0
            td.tank_id.current_int_transfer_in = 0
            td.tank_id.current_int_transfer_out = 0
            td.tank_id.stock_level = td.closing_stock
            td.tank_id.current_closing_stock = td.closing_stock



            # create the stock move
            tank_location_id = td.tank_id.stock_location_tmpl_id

            customer_location_id = td.tank_id.retail_station_id.retail_station_customer_location_id or False
            if not customer_location_id:
                raise UserError(_('Please Contact the Admin to Set a Customer Location for the Retail Station'))

            if td.throughput > 0 :
                vals = {
                    'name': td.tank_id.name,
                    'product_id': td.product_id.id,
                    'product_uom': td.product_id.uom_id.id,
                    'date': self.stock_control_date,
                    'location_id': tank_location_id.id,
                    'location_dest_id': customer_location_id.id,
                    'product_uom_qty': td.throughput,
                    'origin': self.name
                }

                move_id = stock_move_obj.create(vals)
                move_id._action_confirm()
                move_id._force_assign()
                move_id._action_done()
                move_id.stock_control_id = self.id

        return self.write({'state': 'approve'})

    @api.multi
    def action_approve(self):
        # Approve the Net difference
        if self.net_difference != 0:
            model_data_obj = self.env['ir.model.data']
            action = self.env['ir.model.data'].xmlid_to_object(
                'kin_retail_station_rog.action_net_difference_approval')
            form_view_id = model_data_obj.xmlid_to_res_id(
                'kin_retail_station_rog.view_net_difference_approval')

            return {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[form_view_id, 'form']],
                'target': action.target,
                'domain': action.domain,
                'context': {'default_net_difference': self.net_difference},
                'res_model': action.res_model,
                'target': 'new'
            }
        else:
            self.action_approved()


    @api.multi
    def action_disapprove(self, msg):
        user_ids = []
        retail_station_manager = self.retail_station_manager_id
        if retail_station_manager:
            user_ids.append(retail_station_manager.id)
            self.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            user = self.env.user
            self.message_post(_(
                'The Stock Control (%s) has been DisApproved by %s. Reason for Disapproval: %s. You may correct and Re-Submit again for approval ') % (
                                  self.name, user.name, msg),
                              subject='The Stock Control (%s) has been Dis-Approved by %s' % (self.name, user.name),
                              subtype='mail.mt_comment')

        # update the expenses back to confirm state
        for exp in self.expense_ids:
                exp.write({'state': 'confirm'})
        return self.write({'state': 'draft', 'disapprove_id': user.id,
                           'disapprove_date': datetime.today(), 'reason_disapprove': msg})

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.state != 'draft' and not self.env.user.has_group('base.group_no_one'):
    #             # Don't allow deletion of stock control
    #             raise UserError(_('Sorry, this Stock Control cannot be deleted. Please contact your admin'))
    #
    #     return super(StockControl, self).unlink()



    @api.model
    def create(self, vals):
        retail_station_id = vals.get('retail_station_id')
        date = vals.get('stock_control_date')

        #No Pending Product Received Record
        pending_prr_obj = self.env['product.received.register'].search(
            [('to_stock_location_id', '=', retail_station_id), ('state', 'in', ['draft', 'transit'])])

        for pending_prr in pending_prr_obj:
            if pending_prr and not pending_prr.is_company_product:
                receiving_date = pending_prr.receiving_date
                pending_prr_name = pending_prr.name
                retail_station_name = self.env['kin.retail.station'].browse(retail_station_id).name
                # in order to avoid wrong closing stock for the tank
                raise UserError(
                    _(
                        "Sorry, there is a previously created product received record in %s state, with ID - %s for %s with date %s, that is still pending validation by the retail manager. Please contact the retail manager to validate/delete the product received record" % (
                            pending_prr.state,pending_prr_name, retail_station_name,
                            datetime.strptime(receiving_date, "%Y-%m-%d").strftime("%d-%m-%Y"))))


        # No pending un-approved stock control for each retail station
        pending_stock_control_obj = self.search(
            [('retail_station_id', '=', retail_station_id), ('state', 'in', ['draft', 'confirm'])])
        if pending_stock_control_obj:
            pending_stock_control_date = pending_stock_control_obj.stock_control_date
            pending_stock_control_name = pending_stock_control_obj.name
            retail_station_name = pending_stock_control_obj.retail_station_id.name
            raise UserError(
                _(
                    "Sorry, The stock control record with ID - %s for %s with date %s, is still pending approval by the head office. Please contact the head office to approve/disapprove/delete the pending stock control" % (
                        pending_stock_control_name, retail_station_name, datetime.strptime(pending_stock_control_date , "%Y-%m-%d").strftime("%d-%m-%Y"))))

        # Stop backdating day pump sales and stock control before the last previous one
        day_sale_stock_obj = self.env['kin.stock.control']
        sale_stock_control_later = day_sale_stock_obj.search([('retail_station_id', '=', retail_station_id), ('stock_control_date', '>', date)])
        if sale_stock_control_later:
            raise UserError(_('Sorry, You cannot back-date a Day Pump Sales with Stock Control Record before the most recent one'))

        #Dont allow duplicate stock control by station per shift
        shift_id = vals.get('stock_control_shift_ids')
        stock_controls = self.search([('retail_station_id','=',retail_station_id),('stock_control_date','=',date)])
        if len(stock_controls) > 1 :
            raise UserError(_("Sorry, You can only have one Day Pump Sales with Stock Control Record per Retail station per Date"))

        pump_sale_ids = vals.get('pump_sale_ids', False)
        if pump_sale_ids:
            l = []
            for pump_line in pump_sale_ids:
                l.append(pump_line[2]['pump_id'])
            if set([x for x in l if l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
                raise UserError(_(
                    'Duplicate Sales Pump detected. Only One Pump is allowed at a time for each retail sales'))

        tank_dipping_ids = vals.get('tank_dipping_ids', False)
        if tank_dipping_ids:
            l = []
            for tank_line in tank_dipping_ids:
                l.append(tank_line[2]['tank_id'])
            if set([x for x in l if l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
                raise UserError(_(
                    'Duplicate Sales Tank Storage detected. Only One Tank is allowed at a time for each tank dippings'))

        vals['name'] = self.env['ir.sequence'].next_by_code('ssc_code') or 'New'
        res = super(StockControl, self).create(vals)

        # Update the expense with the retail station
        for exp in res.expense_ids:
            exp.write({'retail_station_id': res.retail_station_id.id})

        return res


    @api.multi
    def write(self, vals):

        # No pending un-approved stock control for each retail station
        pending_stock_control_obj = self.search([('retail_station_id', '=', self.retail_station_id.id),('state', 'in', ['draft', 'confirm'])])
        if len(pending_stock_control_obj) > 1:
            raise UserError(_("Sorry, There is a stock control record with ID - %s, for %s, is still pending approval by the head office management. Please contact the head office management to approve the pending stock control" % (pending_stock_control_obj[0].name,datetime.strptime(pending_stock_control_obj[0].stock_control_date , "%Y-%m-%d").strftime("%d-%m-%Y"))))

        res = super(StockControl, self).write(vals)
        # Stop creation of more than one stock control per station per date
        stock_controls = self.search([('retail_station_id', '=', self.retail_station_id.id), ('stock_control_date', '=', self.stock_control_date)])
        if len(stock_controls) > 1:
            raise UserError(
                _("Sorry, You can only have one Day Pump Meter Sales and Control Record per Retail station per Date"))


        l = []
        for sale in self.pump_sale_ids :
            l.append(sale.pump_id.id)
        if set([x for x in l if l.count(x) > 1]):  #see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
            raise  UserError(_('Duplicate Pump Meter detected. Only One Pump Meter is allowed at a time for each daily sales'))

        t = []
        for td in self.tank_dipping_ids:
            t.append(td.tank_id.id)
        if set([x for x in l if
                l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
            raise UserError(_('Duplicate Tank detected. Only One Tank is allowed at a time for each Tank Dippings'))

        #Update the expense with the retail station
        for exp in self.expense_ids:
            exp.write({'retail_station_id': self.retail_station_id.id})

        return res




    @api.onchange('retail_station_id')
    def populate_lines(self):
        fuel_pump_obj = self.env['kin.fuel.pump']
        self.pump_sale_ids.unlink()
        self.stock_control_shift_ids = False

        #populate tank lines
        tank_storage_obj = self.env['kin.tank.storage']
        self.tank_dipping_ids.unlink()
        tanks = tank_storage_obj.search([('retail_station_id', "=", self.retail_station_id.id)])

        line_tanks = []
        for tank in tanks:
            line_tanks += [(0, 0, {
                'tank_id': tank.id,
                'opening_stock': tank.current_closing_stock,
                'stock_received' : tank.current_stock_received,
                'current_int_transfer_in': tank.current_int_transfer_in,
                'current_int_transfer_out': tank.current_int_transfer_out

            })
                      ]
        self.tank_dipping_ids = line_tanks



    @api.multi
    def post_stock_gain_loss(self):
        journal_id = self.env.ref('kin_retail_station_rog.retail_station_stock_gain_loss_journal')
        company = self.env.user.company_id
        inventory_change_account_id = company.inventory_change
        gain_account = company.gain_account
        loss_account = company.loss_account

        partner_id= self.retail_station_id.partner_ids and self.retail_station_id.partner_ids[0] or False


        if not inventory_change_account_id and not gain_account and not loss_account :
            raise UserError(_('Please Set the Inventory Change Account, Gain Account or Loss Account for the company at the configuration page'))

        if not journal_id:
            raise UserError(_('The Stock Gain/Loss Journal is Not Present'))

        mv_lines = []

        total_cost = self.stock_loss_gain_pms_cost + self.stock_loss_gain_ago_cost + self.stock_loss_gain_kero_cost

        if total_cost > 0  :
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': datetime.today(),
                'stock_control_id': self.id
            })
            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'account_id': gain_account.id,
                'partner_id': partner_id.id,
                'debit': abs(total_cost),
                'credit': 0,
                'ref': self.name,
            })
            mv_lines.append(move_line)

            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'account_id': inventory_change_account_id.id,
                'partner_id': partner_id.id,
                'debit': 0,
                'credit': abs(total_cost),
                'ref': self.name,
            })
            mv_lines.append(move_line)
        elif total_cost < 0 :
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': datetime.today(),
                'stock_control_id': self.id
            })
            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'account_id': inventory_change_account_id.id,
                'partner_id': partner_id.id,
                'debit': abs(total_cost),
                'credit': 0,
                'ref': self.name,
            })
            mv_lines.append(move_line)

            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'account_id': loss_account.id,
                'partner_id': partner_id.id,
                'debit': 0,
                'credit': abs(total_cost),
                'ref': self.name,
            })
            mv_lines.append(move_line)

        if mv_lines:
            move_id.write({'line_ids': mv_lines})
            move_id.post()

        return




    @api.depends('cash_in_till','pump_sale_ids.price_subtotal','bank_lodgement_ids.amount','tank_dipping_ids.throughput')
    def _amount_all(self):
        for sale_stock_control in self:
            total_ago_sales_qty = 0
            total_kero_sales_qty = 0
            total_pms_sales_qty = 0
            total_cash_deposited = 0
            total_pump_sales_price_pms = 0
            total_pump_sales_price_ago = 0
            total_pump_sales_price_kero = 0
            sell_price_pms = 0
            sell_price_ago = 0
            sell_price_kero = 0
            cash_brought_forward = sale_stock_control.retail_station_id.latest_cash_in_till

            for ps in sale_stock_control.pump_sale_ids:
                if ps.product_id.white_product == 'pms':
                    total_pms_sales_qty += ps.sale_qty
                    total_pump_sales_price_pms += ps.price_subtotal
                    sell_price_pms = ps.product_price
                elif ps.product_id.white_product == 'ago':
                    total_ago_sales_qty += ps.sale_qty
                    total_pump_sales_price_ago += ps.price_subtotal
                    sell_price_ago = ps.product_price
                elif ps.product_id.white_product == 'kero':
                    total_kero_sales_qty += ps.sale_qty
                    total_pump_sales_price_kero += ps.price_subtotal
                    sell_price_kero = ps.product_price

            total_pms_throughput = 0 #This is dispensed/delivered Stock.
            total_ago_throughput = 0
            total_kero_throughput = 0

            for td in sale_stock_control.tank_dipping_ids:
                if td.product_id.white_product == 'pms':
                    total_pms_throughput += td.throughput
                elif td.product_id.white_product == 'ago':
                    total_ago_throughput += td.throughput
                elif td.product_id.white_product == 'kero':
                    total_kero_throughput += td.throughput


            for bl in sale_stock_control.bank_lodgement_ids :
                total_cash_deposited += bl.amount

            # cash_to_be_collected =sale_stock_control.currency_id.round(total_pump_sales_price)
            sale_stock_control.update({
                'total_pms_sales_qty': total_pms_sales_qty,
                'total_pms_throughput': total_pms_throughput,
                'stock_loss_gain_pms': total_pms_sales_qty - total_pms_throughput,
                'stock_loss_gain_pms_cost' : (total_pms_sales_qty - total_pms_throughput) * sell_price_pms ,
                'total_ago_sales_qty': total_ago_sales_qty,
                'total_ago_throughput': total_ago_throughput,
                'stock_loss_gain_ago': total_ago_sales_qty - total_ago_throughput,
                'stock_loss_gain_ago_cost': (total_ago_sales_qty - total_ago_throughput) * sell_price_ago ,
                'total_kero_sales_qty': total_kero_sales_qty,
                'total_kero_throughput': total_kero_throughput,
                'stock_loss_gain_kero': total_kero_sales_qty - total_kero_throughput,
                'stock_loss_gain_kero_cost' : (total_kero_sales_qty - total_kero_throughput) * sell_price_kero,
                'total_pms_cash_collected': total_pump_sales_price_pms ,
                'total_ago_cash_collected': total_pump_sales_price_ago,
                'total_kero_cash_collected': total_pump_sales_price_kero,
                'total_cash_collected' : sale_stock_control.total_cash_collected_shift_sale ,
                'cash_brought_forward': cash_brought_forward ,
                'total_cash_to_bank' : total_cash_deposited,
                'cash_difference' : (sale_stock_control.total_cash_collected_shift_sale + cash_brought_forward) - total_cash_deposited - sale_stock_control.cash_in_till,

            })


    @api.depends('pump_sale_ids.price_subtotal','tank_dipping_ids.throughput')
    def _amount_all_others(self):
        for sale_stock_control in self:
            total_pump_sales_qty = 0
            total_rtt = 0

            for ps in sale_stock_control.pump_sale_ids:
                total_pump_sales_qty += ps.sale_qty
                total_rtt += ps.rtt

            total_opening_stock = 0
            total_stock_received = 0
            total_internal_transfer_in = 0
            total_internal_transfer_out = 0
            total_stock_at_hand = 0
            total_closing_stock = 0
            total_throughput = 0

            for td in sale_stock_control.tank_dipping_ids:
                total_opening_stock += td.opening_stock
                total_stock_received += td.stock_received
                total_internal_transfer_in += td.current_int_transfer_in
                total_internal_transfer_out += td.current_int_transfer_out
                total_stock_at_hand += td.stock_at_hand
                total_closing_stock += td.closing_stock
                total_throughput += td.throughput

            sale_stock_control.update({
                'total_pump_sales_qty': total_pump_sales_qty,
                'total_rtt' : total_rtt,
                'total_opening_stock': total_opening_stock,
                'total_stock_received': total_stock_received,
                'total_internal_transfer_in': total_internal_transfer_in,
                'total_internal_transfer_out': total_internal_transfer_out,
                'total_stock_at_hand': total_stock_at_hand,
                'total_closing_stock':total_closing_stock,
                'total_throughput': total_throughput,
            })




    @api.multi
    def action_draft(self):
        # populate tank lines
        tank_storage_obj = self.env['kin.tank.storage']
        self.tank_dipping_ids.unlink()
        tanks = tank_storage_obj.search([('retail_station_id', "=", self.retail_station_id.id)])

        line_tanks = []
        for tank in tanks:
            line_tanks += [(0, 0, {
                'tank_id': tank.id,
                'opening_stock': tank.current_closing_stock ,
                'stock_received': tank.current_stock_received,
                'current_int_transfer_in': tank.current_int_transfer_in,
                'current_int_transfer_out': tank.current_int_transfer_out
            })
                           ]
        self.tank_dipping_ids = line_tanks
        self.state = 'draft'


    @api.multi
    def action_cancel(self):

        if self.state == 'cancel':
            raise UserError(_('This record has been previously cancelled. Please refresh your browser'))

        retail_station_id  = self.retail_station_id
        prr_obj = self.env['product.received.register']
        prr_later = prr_obj.search([('to_stock_location_id', '=', retail_station_id.id), ('create_date', '>', self.create_date)])
        for prr in prr_later:
            if not prr.is_company_product:
                the_date = datetime.strptime(self.create_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y  %H:%M:%S")
                prr_name = prr.name
                retail_station_name = retail_station_id.name
                raise UserError(_('Sorry, please the  product received record with ID %s created after %s must be cancelled and deleted for the retail station (%s) to update the stock qty.') % (prr_name,the_date,retail_station_name))

        #no Pending Product Received Record
        pending_prr_obj = prr_obj.search(
            [('to_stock_location_id', '=', retail_station_id.id), ('state', 'in', ['draft', 'transit'])])
        for pending_prr in pending_prr_obj:
            if not pending_prr.is_company_product:
                receiving_date = pending_prr.receiving_date
                pending_prr_name = pending_prr.name
                retail_station_name = retail_station_id.name
                #in order to avoid wrong closing stock for the tank
                raise UserError(
                    _(
                        "Sorry, there is a previously created product received record in %s state, with ID - %s for %s with date %s, that is still pending validation by the retail manager. Please contact the retail manager to validate/delete the product received record" % (
                            pending_prr.state,pending_prr_name, retail_station_name,
                            datetime.strptime(receiving_date, "%Y-%m-%d").strftime("%d-%m-%Y"))))


        # No cancellation of current stock control before the latest stock control. in other to prevent wrong value in the opening stock
        stock_control_recent = self.search(
            [('retail_station_id', '=', self.retail_station_id.id), ('stock_control_date', '>', self.stock_control_date)])
        if stock_control_recent:
            raise UserError(
                _("Sorry, You cannot cancel this stock control record because there is a more recent stock control record with ID - %s for %s,  that has been created already" % (stock_control_recent[0].name,datetime.strptime(stock_control_recent[0].stock_control_date , "%Y-%m-%d").strftime("%d-%m-%Y"))))

        self.write({'state': 'cancel'})
        self.move_ids.button_cancel()
        self.move_ids.unlink()

        for payg in self.payment_ids:
            payg.cancel()
            payg.unlink()

        # update the expenses back to confirm state
        for exp in self.expense_ids:
            exp.write({'state': 'confirm'})

        for pump_sale in self.pump_sale_ids:
            # commenting the following because it blocks the day stock control report from being cancelled because the shift retail sales have already updated the totalizer
            # if pump_sale.meter_end != pump_sale.pump_id.totalizer and pump_sale.meter_start != pump_sale.pump_id.totalizer : #possibly try to cancel a shift pump sale after a recent one has been approved to update the totalizer
            #     raise UserError(_('The Totalizer has been previously updated by a more recent shift Pump Meter sale. Ensure you delete all the following Pump Meter meter sales before cancelling this record'))
            pump_sale.pump_id.totalizer = pump_sale.meter_start


    @api.multi
    def action_cancel_approver(self):
        self.action_cancel()

        # save latest cash in till
        self.retail_station_id.latest_cash_in_till = self.cash_brought_forward

        #reverse the stock level
        for td in self.tank_dipping_ids :
            td.tank_id.current_closing_stock = td.opening_stock
            td.tank_id.current_int_transfer_in = td.tank_id.current_int_transfer_in +  td.current_int_transfer_in
            td.tank_id.current_int_transfer_out =  td.tank_id.current_int_transfer_out + td.current_int_transfer_out
            td.tank_id.current_stock_received = td.tank_id.current_stock_received + td.stock_received
            td.tank_id.stock_level = td.tank_id.current_closing_stock + td.tank_id.current_stock_received + td.tank_id.current_int_transfer_in - td.tank_id.current_int_transfer_out

        #populate tank lines
        tank_storage_obj = self.env['kin.tank.storage']
        self.tank_dipping_ids.unlink()
        tanks = tank_storage_obj.search([('retail_station_id', "=", self.retail_station_id.id)])

        line_tanks = []
        for tank in tanks:
            line_tanks += [(0, 0, {
                'tank_id': tank.id,
                'opening_stock': tank.current_closing_stock,
                'stock_received' : tank.current_stock_received,
                'current_int_transfer_in': tank.current_int_transfer_in,
                'current_int_transfer_out': tank.current_int_transfer_out
            })
                      ]
        self.tank_dipping_ids = line_tanks

        #Reverse Stock moves because the system cannot allow cancellation of done stock moves
        stock_move_obj = self.env['stock.move']
        for stock_move in  self.stock_move_ids:
            if stock_move.location_dest_id.id == stock_move.location_dest_id.id: #erp stock modu;e does not create stock move when the source and destination are thesame
                stock_move.stock_control_id = False
            else :
                # create the reverse stock move
                vals = {
                        'name': 'Reversal for: ' + stock_move.origin,
                        'product_id': stock_move.product_id.id,
                        'product_uom': stock_move.product_uom.id,
                        'date': datetime.today(),
                        'location_id': stock_move.location_dest_id.id,
                        'location_dest_id': stock_move.location_id.id,
                        'product_uom_qty': stock_move.product_uom_qty,
                        'origin': stock_move.origin
                }
                stock_move.stock_control_id = False  # exempts the record incase of more reversals
                move_id = stock_move_obj.create(vals)
                move_id._action_confirm()
                move_id._force_assign()
                move_id._action_done()
                move_id.stock_control_id = self.id






    def action_submit(self):

        #Check if Net difference is allowed  not be equal to Zero
        if self.retail_station_id.is_net_difference_zero and self.net_difference != 0 :
            raise UserError(_('Please the Net Difference with value %s , in the Cash Control Must be Equal to Zero' % (self.net_difference)))

        if self.total_cash_to_bank <= 0 and self.cash_in_till <= 0:
            raise UserError(_('Please Enter Bank Lodgements or Cash in Till Amount'))
        # if self.cash_difference != self.total_expenses :
        #     raise UserError(_('Cash Difference is not equal to Total Expenses. Please cross-check your entries.'))
        # update the totalizer

        for pump_sale in self.pump_sale_ids:
            # pump_sale.pump_id.totalizer = pump_sale.meter_end
            if pump_sale.meter_end < pump_sale.meter_start:
                raise UserError(_(
                    'Meter End Reading for Pump Meter -%s with value (%s) Cannot be lower than Meter Start Reading with value (%s).') % (
                                pump_sale.pump_id.name, pump_sale.meter_end, pump_sale.meter_start))

        for td in self.tank_dipping_ids:
            if (td.stock_at_hand != 0 and td.closing_stock == 0):
                raise UserError(_(
                    "Please check your closing stock value for the tank %s. A Storage Tank may not have zero stock quantity. Please consider dead stock when entering closing stock" % (
                    td.tank_id.name)))
            if (td.stock_at_hand == 0 and td.closing_stock < 0):
                raise UserError(_(
                    "Please check your closing stock value for the tank %s. A Storage Tank may not have negative stock quantity. Please consider dead stock when entering closing stock" % (
                    td.tank_id.name)))

            # if opening dip does not match the current closing stock  then let the user delete and rec-reate a new stock ccontrol
            if td.opening_stock != td.tank_id.current_closing_stock:
                raise UserError(_(
                        'Opening dip for - %s, does not match the current closing dip value for the tank storage. Please delete this day pump sales and control record, then re-create a new record to get the updated last previous closing dip value as the opening stock value' % (
                        td.tank_id.name)))

        # update the expenses to done state
        for exp in self.expense_ids:
            exp.write({'state': 'done'})

        user_ids = []
        group_obj = self.env.ref('kin_retail_station_rog.group_stock_control_submitted_notification')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_('A New Stock Control Record from %s has been Created with ID %s.') % (
            self.retail_station_manager_id.name, self.name),
                          subject='A New Stock Control Record has been Created ', subtype='mail.mt_comment')

        # operational loss/gain alert
        olg_percentage = self.retail_station_id.operational_loss_gain_percentage
        user_ids_1 = []
        group_obj = self.env.ref('kin_retail_station_rog.group_operational_loss_gain_alert')
        for user in group_obj.users:
            user_ids_1.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids_1)

        # PMS
        if self.stock_loss_gain_pms and self.total_pms_sales_qty:
            the_perc_pms = (self.stock_loss_gain_pms / self.total_pms_sales_qty) * 100
            if the_perc_pms > olg_percentage:
                # send pms gain notification
                self.message_post(_(
                    'The Stock PMS Gain Qty. %s ltr(s), for the Stock Control record %s, has exceeded the %s percentage Operational Gain Allowance for the Retail Station %s.') % (
                                      self.stock_loss_gain_pms, self.name, olg_percentage, self.retail_station_id.name),
                                  subject='Stock Gain PMS Qty. Exceeds the Operational Gain Allowance for Retail Station ',
                                  subtype='mail.mt_comment')

            if the_perc_pms < -olg_percentage:
                # send pms loss notification
                self.message_post(_(
                    'The Stock PMS Loss Qty. %s ltr(s), for the Stock Control record %s, is below the %s percentage Operational Loss Allowance for the Retail Station %s.') % (
                                      self.stock_loss_gain_pms, self.name, olg_percentage, self.retail_station_id.name),
                                  subject='Stock Loss PMS Qty. is below the Operational Loss Allowance for Retail Station ',
                                  subtype='mail.mt_comment')

        # AGO
        if self.stock_loss_gain_ago and self.total_ago_sales_qty:
            the_perc_ago = (self.stock_loss_gain_ago / self.total_ago_sales_qty) * 100
            if the_perc_ago > olg_percentage:
                # send ago gain notification
                self.message_post(_(
                    'The Stock AGO Gain Qty. %s ltr(s), for the Stock Control record %s, has exceeded the %s percentage Operational Gain Allowance for the Retail Station %s.') % (
                                      self.stock_loss_gain_ago, self.name, olg_percentage, self.retail_station_id.name),
                                  subject='Stock Gain AGO Qty. Exceeds the Operational Gain Allowance for Retail Station ',
                                  subtype='mail.mt_comment')

            if the_perc_ago < -olg_percentage:
                # send  ago loss notification
                self.message_post(_(
                    'The Stock AGO Loss Qty. %s ltr(s), for the Stock Control record %s, is below the %s percentage Operational Loss Allowance for the Retail Station %s.') % (
                                      self.stock_loss_gain_ago, self.name, olg_percentage, self.retail_station_id.name),
                                  subject='Stock Loss AGO Qty. is below the Operational Loss Allowance for Retail Station ',
                                  subtype='mail.mt_comment')

        # DPK
        if self.stock_loss_gain_kero and self.total_kero_sales_qty:
            the_perc_dpk = (self.stock_loss_gain_kero / self.total_kero_sales_qty) * 100
            if the_perc_dpk > olg_percentage:
                # send dpk gain notification
                self.message_post(_(
                    'The Stock DPK Gain Qty. %s ltr(s), for the Stock Control record %s, has exceeded the %s percentage Operational Gain Allowance for the Retail Station %s.') % (
                                      self.stock_loss_gain_kero, self.name, olg_percentage,
                                      self.retail_station_id.name),
                                  subject='Stock Gain DPK Qty. Exceeds the Operational Gain Allowance for Retail Station ',
                                  subtype='mail.mt_comment')

            if the_perc_dpk < -olg_percentage:
                # send dpk loss notification
                self.message_post(_(
                    'The Stock DPK Loss Qty. %s ltr(s), for the Stock Control record %s, is below the %s percentage Operational Loss Allowance for the Retail Station %s.') % (
                                      self.stock_loss_gain_kero, self.name, olg_percentage,
                                      self.retail_station_id.name),
                                  subject='Stock Loss DPK Qty. is below the Operational Loss Allowance for Retail Station ',
                                  subtype='mail.mt_comment')

        return self.write({'state': 'confirm'})

    @api.multi
    def action_confirm(self):
        # Confirm Net difference
        if self.net_difference != 0:
            model_data_obj = self.env['ir.model.data']
            action = self.env['ir.model.data'].xmlid_to_object(
                'kin_retail_station_rog.action_net_difference_confirmation')
            form_view_id = model_data_obj.xmlid_to_res_id(
                'kin_retail_station_rog.view_net_difference_confirmation')

            return {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[form_view_id, 'form']],
                'target': action.target,
                'domain': action.domain,
                'context': {'default_net_difference': self.net_difference},
                'res_model': action.res_model,
                'target': 'new'
            }
        else:
            self.action_submit()





    @api.multi
    def button_dummy(self):
        return True

    @api.onchange('payment_ids','bank_lodgement_ids')
    def _compute_posted_payment(self):
        for rec in self:
            total_amt = 0
            for pg in rec.payment_ids:
                if pg.state == 'posted':
                    total_amt += pg.amount

            if self.state not in ['draft', 'confirm','cancel'] :
                if total_amt and total_amt == rec.total_cash_to_bank:
                    rec.write({'state': 'done'})  # rec.state = done is not working here, rather use the write()
                elif len(rec.payment_ids) == 0 :
                    rec.write({'state': 'approve'}) # rec.state = 'approve' is not working here, rather use the write()
                else :
                    rec.write({'state': 'open'})

            rec.posted_payment = total_amt
            rec.balance_to_be_posted = rec.total_cash_to_bank - rec.posted_payment
        return



    @api.depends('expense_ids','total_cash_to_bank')
    def _compute_expenses(self):
        for rec in self:
            total_exp_gmd = 0
            total_exp_gen = 0
            total_exp_maint = 0
            total_exp_fuel = 0
            total_exp_other = 0

            for exp in rec.expense_ids:
                if exp.expense_type == 'gmd_consumption':
                    total_exp_gmd += exp.amount

                if exp.expense_type == 'ago_generator':
                    total_exp_gen += exp.amount

                if exp.expense_type == 'maintenance_charges':
                    total_exp_maint += exp.amount

                if exp.expense_type == 'station_car_fueling':
                    total_exp_fuel += exp.amount

                if exp.expense_type == 'other_expenses':
                    total_exp_other += exp.amount

            rec.gmd_consumption = total_exp_gmd
            rec.ago_for_generator = total_exp_gen
            rec.maintenance_charges = total_exp_maint
            rec.station_car_fueling = total_exp_fuel
            rec.other_expenses = total_exp_other

            rec.total_expenses = rec.gmd_consumption + rec.ago_for_generator + rec.maintenance_charges + rec.station_car_fueling + rec.other_expenses
            rec.net_difference = rec.cash_difference - rec.total_expenses

    @api.depends('retail_station_id')
    def _compute_retail_station_manager(self):
        self.retail_station_manager_id = self.retail_station_id.retail_station_manager_id

    @api.multi
    def btn_view_stock_move(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_move_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_move_ids')
    def _compute_stock_move_count(self):
        for rec in self:
            rec.stock_move_count = len(rec.stock_move_ids)


    name = fields.Char('ID')
    stock_control_date = fields.Date('Date')

    total_cash_sales_shift_sale= fields.Monetary('Total Cash Sales from Shift Pump Sales (NGN)',  help="Total Cash Sales for All White Products from Shift Pump Sales + Cash In Till from Shift Pump Sales")
    total_cash_collected_shift_sale = fields.Monetary('Total Cash Collected from Shift Pump Sales (NGN)', help="Total Cash Collected from Shift Pump Sales")
    total_pos_card_shift_sale = fields.Monetary('Total Card POS Payment from Shift Pump Sales (NGN)', help="Total Card Payment through POS from Shift Pump Sales")
    total_voucher_shift_sale = fields.Monetary('Total Voucher Payment from Shift Pump Sales (NGN)' ,help="Total Voucher Payment for Pump Sales")
    other_payment_shift_sale = fields.Monetary('Other form of Payment from Shift Pump Sale (NGN)', help="Other form of Payment from Shift Pump Sales")
    cash_difference_shift_sale= fields.Monetary('Variance (Cash Difference) from Shift Pump Sales (NGN)', help="Total Cash Sales from Shift Pump Sales- Total Cash Collected from Shift Pump Sales- Total Card POS Payment from Shift Pump Sales- Other Payment from Shift Pump Sales")

    total_cash_collected = fields.Monetary('Total Cash Collected (NGN)',compute='_amount_all',store=True,help="Total Cash Collected from Shift Supervisors for All White Products")
    cash_brought_forward = fields.Monetary('Cash Brought Forward (NGN)', compute='_amount_all', store=True,help="Cash Brought Forward")
    total_cash_to_bank = fields.Monetary('Total Cash Deposited (NGN)',compute='_amount_all',store=True,help="Total Bank Lodgements")
    cash_difference = fields.Monetary('Variance/Cash Difference (NGN)',compute='_amount_all',store=True,help="(Total Cash Collected + Cash Brought Forward) - Total Cash Deposited")
    variance_explanation = fields.Text('Explanation of Variance (Stock & Cash)')
    pump_sale_ids = fields.One2many('kin.pump.sale','stock_control_id',string='Pump Sales')
    tank_dipping_ids = fields.One2many('kin.tank.dipping','stock_control_id',string='Tank Dippings')
    bank_lodgement_ids = fields.One2many('kin.bank.lodgement','stock_control_id', 'Bank Lodgements')
    retail_station_id = fields.Many2one('kin.retail.station',string='Retail Station',ondelete='restrict')
    retail_station_manager_id = fields.Many2one('res.users',compute='_compute_retail_station_manager',string='Retail Station Manager',store=True,ondelete='restrict')
    stock_control_shift_ids = fields.Many2many('kin.shift','shift_stock_control_rel','stock_control_field','shift_field',string='Sales Shift',ondelete='restrict')
    retail_station_ids = fields.Many2many('kin.retail.station', 'stock_control_retail_station', 'stock_control_id',
                                          'retail_station_id', string='Retail Stations',ondelete='restrict')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed and Submitted by Retail Manager'),
        ('approve','Approved by Head Office'),
        ('open', 'Lodgments Partially Reconciled'),
        ('done','Done'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    reason_disapprove = fields.Text(string='Reason for Dis-Approval')
    disapprove_id = fields.Many2one('res.users',string='Disapproved By',ondelete='restrict')
    disapprove_date = fields.Datetime(string='Disapproved Date')
    payment_ids = fields.One2many('account.payment','stock_control_id',string='Account Payments')
    payment_count = fields.Integer(compute="_compute_payment_count", string='# of Payment Group', copy=False, default=0)
    posted_payment = fields.Monetary(string='Posted Payment (NGN)',compute='_compute_posted_payment') #store=True allows the field to be computed once and saved. It does not allow further computation on record read. But removing it will allow computation on record read. But you can use @api.depends (NOT @api.onchange) to calculate the fields that are with store=True. Note that @api.depends does the work of @api.onchange. Also not @api.onchange does not persist  store=True fields
    balance_to_be_posted = fields.Monetary(string="Balance Yet To Be Posted (NGN)",compute='_compute_posted_payment')

    # store=True allows the field to be computed once and saved. It does not allow further computation on record read. But removing it will allow computation on record read
    # But you can use @api.depends (NOT @api.onchange) to calculate the fields that are with store=True
    # Note that @api.depends does the work of @api.onchange. Also not @api.onchange does not persist  store=True fields
    # @api.depends() should be used together with .update() and compute=''. While the @api.depends() with .update() allows computation on the client browser for readonly fields, but does not get saved on the database because the fields are readonly, The compute='' does the RE-computation on the server side, which allows the readonly field to be RE-calculated and saved on the database
    total_pms_sales_qty = fields.Float('Total PMS Sales Qty. (ltrs)',digits=dp.get_precision('Product Price'),compute='_amount_all',store=True)
    total_pms_throughput = fields.Float('Total PMS ThroughPut Qty. (ltrs)',digits=dp.get_precision('Product Price'),compute='_amount_all',store=True, help='Total dispensed/delivered Stock out of the tank')
    stock_loss_gain_pms = fields.Float('Stock PMS Gain/(-Loss) Qty. (ltrs)',digits=dp.get_precision('Product Price'),compute='_amount_all',store=True, help='Total PMS Pump Sales Qty. - Throughput or dispensed or delivered Stock)')  # If througput >Sales. It ,mean
    stock_loss_gain_pms_cost = fields.Monetary('Stock PMS Gain/(-Loss) Cost (NGN)' , compute='_amount_all', store=True, help='Stock Gain/(-Loss PMS) Qty.  * PMS Selling Price' )
    total_pms_cash_collected = fields.Monetary('Total PMS Cash Sales (NGN)',compute='_amount_all',store=True,help="Total PMS Pump Sales Qty. * PMS Selling Price")

    total_ago_sales_qty = fields.Float('Total AGO Sales Qty. (ltrs)', digits=dp.get_precision('Product Price'),compute='_amount_all',store=True)
    total_ago_throughput = fields.Float('Total AGO ThroughPut Qty. (ltrs)',digits=dp.get_precision('Product Price'), compute='_amount_all',store=True, help='Total dispensed/delivered Stock out of the tank')
    stock_loss_gain_ago = fields.Float('Stock AGO Gain/(-Loss) Qty. (ltrs)',digits=dp.get_precision('Product Price'), compute='_amount_all',store=True, help='Total AGO Pump Sales Qty. - Throughput or dispensed or delivered Stock)')  # If througput >Sales. It ,mean
    stock_loss_gain_ago_cost = fields.Monetary('Stock AGO Gain/(-Loss) Cost (NGN)', compute='_amount_all', store=True, help='Stock Gain/(-Loss AGO) Qty.  * AGO Selling Price' )
    total_ago_cash_collected = fields.Monetary('Total AGO Cash Sales (NGN)', compute='_amount_all', store=True,help="Total AGO Pump Sales Qty. * AGO Selling Price")

    total_kero_sales_qty = fields.Float('Total DPK Sales Qty. (ltrs)',digits=dp.get_precision('Product Price'),compute='_amount_all',store=True)
    total_kero_throughput = fields.Float('Total DPK ThroughPut Qty. (ltrs)',digits=dp.get_precision('Product Price'),compute='_amount_all',store=True, help='Total dispensed/delivered Stock out of the tank')
    stock_loss_gain_kero = fields.Float('Stock DPK Gain/(-Loss) Qty. (ltrs)',digits=dp.get_precision('Product Price'), compute='_amount_all',store=True,help='Total DPK Pump Sales Qty. - Throughput or dispensed or delivered Stock)')  # If througput >Sales. It ,mean
    stock_loss_gain_kero_cost = fields.Monetary('Stock DPK Gain/(-Loss) Cost (NGN)', compute='_amount_all', store=True, help='Stock Gain/(-Loss DPK) Qty.  * DPK Selling Price' )
    total_kero_cash_collected = fields.Monetary('Total DPK Cash Sales (NGN)', compute='_amount_all', store=True, help="Total DPK Pump Sales Qty. * DPK Selling Price")

    gmd_consumption =  fields.Monetary(string='GMD Consumption (NGN)',compute='_compute_expenses',store=True)
    ago_for_generator = fields.Monetary(string='AGO for Generator (NGN)',compute='_compute_expenses',store=True)
    maintenance_charges = fields.Monetary(string='Maintenance Charges (NGN)',compute='_compute_expenses',store=True)
    station_car_fueling = fields.Monetary(string='Station Car Fueling (NGN)',compute='_compute_expenses',store=True)
    other_expenses = fields.Monetary(string='Other Expenses (NGN)',compute='_compute_expenses',store=True)
    total_expenses = fields.Monetary(string='Total Expenses (NGN)',compute='_compute_expenses',store=True)
    net_difference = fields.Monetary(string='Net Difference (NGN)',compute='_compute_expenses',store=True,help='Variance - Total Expenses.  (-) = Cash Surplus; (+) = Cash Shortfall')
    expense_ids = fields.One2many('kin.retail.station.expense','stock_control_id',string='Expense Type')
    cash_in_till = fields.Monetary(string='Cash In Till (NGN)')

    jnr_count = fields.Integer(compute="_compute_jnr_count", string='# of Journal Items', copy=False, default=0)
    move_ids = fields.One2many('account.move', 'stock_control_id', string='Journal Entry(s)')

    shift_sale_count = fields.Integer(compute="_compute_shift_count", string='# of  Shift Sales', copy=False, default=0)
    retail_sale_ids = fields.One2many('kin.retail.sale', 'stock_control_id', string='Shift Sales')

    bank_journal_ids = fields.Many2many(related='retail_station_id.bank_journal_ids',string='Bank Journals',ondelete='restrict')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id,ondelete='restrict')

    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False, default=0)
    stock_move_ids = fields.One2many('stock.move', 'stock_control_id', string='Stock Moves')

    total_pump_sales_qty = fields.Float('Total Pump Sales Qty.',compute='_amount_all_others',store=True)
    total_opening_stock = fields.Float('Total Opening Stock.', compute='_amount_all_others', store=True)
    total_stock_received = fields.Float('Total Stock Received.', compute='_amount_all_others', store=True)
    total_internal_transfer_in = fields.Float('Total Internal Transfer IN', compute='_amount_all_others', store=True)
    total_internal_transfer_out = fields.Float('Total Internal Transfer OUT', compute='_amount_all_others', store=True)
    total_rtt = fields.Float('Total Return to Tank', compute='_amount_all_others', store=True)
    total_stock_at_hand = fields.Float('Total Stock at Hand', compute='_amount_all_others', store=True)
    total_closing_stock = fields.Float('Total Closing Stock.', compute='_amount_all_others', store=True)
    total_throughput = fields.Float('Total Throughput', compute='_amount_all_others', store=True)


class PumpSale(models.Model):
    _name = 'kin.pump.sale'

    @api.multi
    def write(self, vals):
        is_merge = self.env.context.get('is_merge',False)
        if not is_merge and not self.env.user.has_group('kin_retail_station_rog.group_station_shift_supervisor') :
            raise UserError(_("Sorry, You Don't Have the Right to Edit Pump Sales"))

        meter_end = vals.get('meter_end',self.meter_end)
        rtt = vals.get('rtt',self.rtt)
        sale_qty = meter_end - self.meter_start - rtt
        if meter_end < self.meter_start:
            raise UserError(_(
                'Sorry, meter end reading for meter pump %s with value (%s), cannot be lower than Meter Start Reading (%s). Check All the Meter End Reading for Each Pump Meter and Correct them before Saving this Form') % (
                            self.pump_id.name, meter_end, self.meter_start))
        if rtt > (meter_end - self.meter_start)  :
            raise UserError('Sorry, You cannot Return to tank more than the Sales Qty. Check All the RTT for Each Pump and Correct them before Saving this Form')
        res = super(PumpSale, self).write(vals)

        return res


    @api.model
    def create(self,vals):
        res = super(PumpSale,self).create(vals)
        return res

    @api.depends('meter_end','rtt','sale_qty','product_price')
    def _compute_sale_qty(self):
        for rec in self :
            if rec.meter_end  < rec.meter_start :
                warning_mess = {
                    'title': _('Totalizer End Value < Totalizer Start Value!'),
                    'message': _('Sorry, Meter End Reading (%s) for the pump meter %s, Cannot be lower than Meter Start Reading (%s).') % (rec.meter_end,rec.pump_id.name,rec.meter_start)
                }

                return {'warning': warning_mess}
            elif rec.rtt  > (rec.meter_end - rec.meter_start) :
                warn_mess = {
                    'title': _('RTT value > Sales Qty.!'),
                    'message': _('Sorry, You cannot Return to tank more than the Sales Qty.')
                }

                return {'warning': warn_mess}
            else:
                rec.sale_qty = rec.meter_end - rec.meter_start - rec.rtt
                rec.price_subtotal = rec.sale_qty * rec.product_price

    #using related="" is a loophole to reset the parent model without a state
    @api.depends('stock_control_id.state')
    def _compute_state(self):
        for rec in self:
            rec.status = rec.stock_control_id.state




    pump_sale_date = fields.Date(related='stock_control_id.stock_control_date', store=True)
    product_id = fields.Many2one('product.product',related='pump_id.product_id',string='Product',ondelete='restrict',store=True)
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    product_price = fields.Monetary(string='Selling Price (NGN)')
    product_price_readonly =  fields.Monetary(related='product_price')
    meter_start = fields.Float(string='Meter Start (ltrs)',digits=dp.get_precision('Product Price'),help='Equal to Last/Current Totalizer Meter Reading')
    meter_start_readonly = fields.Float(related='meter_start')
    meter_end = fields.Float('Meter End (ltrs)',digits=dp.get_precision('Product Price'))
    rtt = fields.Float('Return to Tank (ltrs)',digits=dp.get_precision('Product Price'))
    sale_qty = fields.Float(string='Pump Sales Qty. (ltrs)', digits=dp.get_precision('Product Price'),compute='_compute_sale_qty',help='Meter End - Meter Start - RTT',store=True)
    price_subtotal = fields.Monetary(string='Subtotal Price (NGN)',compute='_compute_sale_qty',help='Pump Sales Qty. * Selling price of Product',store=True )
    pump_id = fields.Many2one('kin.fuel.pump', 'Pump',ondelete='restrict')
    stock_control_id = fields.Many2one('kin.stock.control','Stock Control')
    retail_sale_id = fields.Many2one('kin.retail.sale', 'Retail Sales',ondelete='cascade')
    retail_station_id = fields.Many2one('kin.retail.station',related='stock_control_id.retail_station_id',store=True,string='Retail Station',ondelete='restrict')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,ondelete='restrict')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed and Submitted by Retail Manager'),
        ('approve','Approved by Head Office'),
        ('open', 'Lodgments Partially Reconciled'),
        ('done','Done'),
        ('cancel', 'Cancel')
    ], string='Status', compute='_compute_state', store=True)

    # stock_control_date = fields.Date(related='stock_control_id.stock_control_date',string='Stock Control Date',store=True)
    # retail_sale_date = fields.Date(related='retail_sale_id.retail_sale_date', string='Shift Sale Date',store=True)


class TankDipping(models.Model):
    _name = 'kin.tank.dipping'



    @api.model
    def create(self, vals):
        res = super(TankDipping, self).create(vals)
        if res.stock_at_hand < 0 :
            raise UserError(_('Stock at hand cannot go negative (%s) for %s dipping'%(res.stock_at_hand,res.tank_id.name)))
        if res.closing_stock > res.stock_at_hand:
            raise UserError(_('Closing Stock (%s) cannot be greater than Stock at Hand (%s) for %s dipping'%(res.closing_stock,res.stock_at_hand,res.tank_id.name)))


        return res

    @api.multi
    def write(self, vals):
        res = super(TankDipping, self).write(vals) #since the stock_at_hand field is readonly, it means the val field cannot get new changes for this field, thus the only option is to do write() first before accessing the field value. Accessing the value first before write() will give you the outdated field value, which is wrong for the calculation
        if self.stock_at_hand < 0 :
            raise UserError(_('Stock at hand  cannot go negative'))
        if self.closing_stock > self.stock_at_hand:
            raise UserError(_('Closing Stock cannot be greater than Stock at Hand'))

        return res



    @api.depends('closing_stock','stock_at_hand')
    def _check_stock_values(self):
        for rec in self:
            if rec.closing_stock > rec.stock_at_hand:
                warning_mess = {
                    'title': _('Closing Stock > Stock at Hand!'),
                    'message': _('Closing Stock cannot be greater that Stock at Hand')
                }
                return {'warning': warning_mess}

    @api.depends('opening_stock', 'stock_at_hand', 'stock_received','current_int_transfer_in','current_int_transfer_out', 'closing_stock')
    def _compute_measures(self):
        for rec in self:
            rec.stock_at_hand = rec.opening_stock + rec.stock_received + rec.current_int_transfer_in - rec.current_int_transfer_out
            rec.throughput = rec.stock_at_hand - rec.closing_stock

    #using related="" is a loophole to reset the parent model without a state
    @api.depends('stock_control_id.state')
    def _compute_state(self):
        for rec in self:
            rec.status = rec.stock_control_id.state

    tank_dip_date = fields.Date(related='stock_control_id.stock_control_date', store=True)
    tank_id = fields.Many2one('kin.tank.storage', string='Tank',ondelete='restrict')
    product_id = fields.Many2one('product.product', related='tank_id.product_id', string='Product',ondelete='restrict',store=True)
    product_uom = fields.Many2one('product.uom', related='tank_id.product_id.uom_id', string='Unit')
    opening_stock = fields.Float('Opening Stock (ltrs)',digits=dp.get_precision('Product Price'))
    stock_received = fields.Float('Stock Received (ltrs)',digits=dp.get_precision('Product Price'))
    current_int_transfer_in = fields.Float('Internal Transfer IN (ltrs)', digits=dp.get_precision('Product Price'))
    current_int_transfer_out = fields.Float('Internal Transfer OUT (ltrs)', digits=dp.get_precision('Product Price'))
    stock_at_hand = fields.Float('Stock at Hand (ltrs)',digits=dp.get_precision('Product Price'),compute='_compute_measures',help='Opening Stock + Stock Received + Internal Transfer IN - Internal Transfer OUT',store=True)
    closing_stock = fields.Float('Closing Stock (ltrs)',digits=dp.get_precision('Product Price'))
    throughput = fields.Float('Throughput (ltrs)',digits=dp.get_precision('Product Price'),compute='_compute_measures',help='This is the dispensed/delivered stock. i.e.  Stock at Hand - Closing Stock',store=True)
    stock_control_id = fields.Many2one('kin.stock.control', 'Stock Control',ondelete='cascade')
    retail_sale_id = fields.Many2one('kin.retail.sale', 'Retail Sales')
    retail_station_id = fields.Many2one('kin.retail.station', related='stock_control_id.retail_station_id',
                                        store=True, string='Retail Station', ondelete='restrict')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed and Submitted by Retail Manager'),
        ('approve','Approved by Head Office'),
        ('open', 'Lodgments Partially Reconciled'),
        ('done','Done'),
        ('cancel', 'Cancel')
    ], string='Status', compute='_compute_state', store=True)



class FuelPumpPriceHistory(models.Model):
    _name = 'kin.fuel.pump.history'
    _order = 'date_change desc'

    product_id = fields.Many2one('product.product', 'Product', required=True, ondelete='restrict')
    uom_id = fields.Many2one(string='Unit', related='product_id.uom_id')
    user_id = fields.Many2one('res.users',string='Changed By',ondelete='restrict')
    date_change = fields.Datetime(string='Changed Date and Time',default=lambda self: datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    previous_price = fields.Monetary(string='Previous Price')
    new_price = fields.Monetary(string='New Price')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,ondelete='restrict')
    fuel_pump_id = fields.Many2one('kin.fuel.pump',string='Fuel Pump',ondelete='restrict')
    retail_station_id = fields.Many2one('kin.retail.station',string='Retail Station',related='fuel_pump_id.retail_station_id',store=True,ondelete='restrict')

class FuelPumpTotalizerHistory(models.Model):
    _name = 'kin.fuel.totalizer.history'
    _order = 'date_change desc'

    product_id = fields.Many2one('product.product', 'Product', required=True, ondelete='restrict')
    uom_id = fields.Many2one(string='Unit', related='product_id.uom_id',ondelete='restrict')
    user_id = fields.Many2one('res.users', string='Changed By',ondelete='restrict')
    date_change = fields.Datetime(string='Changed Date and Time',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    previous_totalizer = fields.Float(string='Previous Totalizer Value')
    new_totalizer = fields.Float(string='New Totalizer Value')
    fuel_pump_id = fields.Many2one('kin.fuel.pump', string='Fuel Pump Meter',ondelete='restrict')
    retail_station_id = fields.Many2one('kin.retail.station', string='Retail Station',
                                        related='fuel_pump_id.retail_station_id', store=True,ondelete='restrict')



class FuelPump(models.Model):
    _name = 'kin.fuel.pump'
    _inherit = ['mail.thread']



    @api.multi
    def change_prices(self,new_price):
        fuel_pump_history = self.env['kin.fuel.pump.history']
        for rec in self:
            rec.selling_price = new_price

            # Send Email Notification for Price Change
            user_ids = []
            group_obj = self.env.ref('kin_retail_station_rog.group_change_price')
            for user in group_obj.users:
                user_ids.append(user.id)
            rec.message_subscribe_users(user_ids=user_ids)
            rec.message_post(_('Fuel Pump Price change alert for the fuel pump - %s in %s, was changed from %s to %s') % (
                rec.name, rec.retail_station_id.name,rec.selling_price,new_price),
                              subject='Fuel Pump Price Change Notification Created', subtype='mail.mt_comment')

            # Record the Price Change History
            fuel_pump_history.create({
                'product_id':rec.product_id.id,
                'user_id':self.env.user.id,
                'previous_price': rec.selling_price,
                'new_price' : new_price ,
                'fuel_pump_id':rec.id
            })



    @api.multi
    def change_totalizer_value(self,new_totalizer):

        fuel_totalizer_history = self.env['kin.fuel.totalizer.history']


        # Send Email Notification for Totalizer Value
        user_ids = []
        group_obj = self.env.ref('kin_retail_station_rog.group_change_totalizer_value')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(
            _('Fuel Pump Meter Totalizer Value change alert for the fuel Pump Meter - %s in %s, was changed from %s to %s') % (
                self.name, self.retail_station_id.name, self.totalizer, new_totalizer),
            subject='Fuel Pump Meter Totalizer Change Notification Created', subtype='mail.mt_comment')

        # Record the Price Change History
        fuel_totalizer_history.create({
            'product_id': self.product_id.id,
            'user_id': self.env.user.id,
            'previous_totalizer': self.totalizer,
            'new_totalizer': new_totalizer,
            'fuel_pump_id': self.id
        })

        self.totalizer = new_totalizer


    name = fields.Char('Pump No.',track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product',ondelete='restrict')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    totalizer = fields.Float('Totalizer (ltrs)',digits=dp.get_precision('Product Price'),track_visibility='onchange')
    tank_ids = fields.Many2many('kin.tank.storage', 'tank_fuel_rel', 'tank_id', 'fuel_id', string='Tanks',help='Tank Supplying to the Pump',track_visibility='onchange')
    retail_station_id = fields.Many2one(related='tank_ids.retail_station_id', store=True, string='Retail Station',ondelete='restrict')
    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    selling_price = fields.Monetary(string='Selling Price (NGN)',digits=dp.get_precision('Product Price'))
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,ondelete='restrict')
    pump_price_history_ids = fields.One2many('kin.fuel.pump.history','fuel_pump_id',string='Fuel Pump History')
    pump_totalizer_history_ids = fields.One2many('kin.fuel.totalizer.history', 'fuel_pump_id',
                                                 string='Fuel Pump Meter Totalizer Value History')


class Shift(models.Model):
    _name = 'kin.shift'

    name = fields.Char('Shift')
    retail_station_ids = fields.Many2many('kin.retail.station','shift_retail_station','shift_id','retail_station_id',string='Retail Stations')
    shift_stock_control_ids = fields.Many2many('kin.stock.control','shift_stock_control_rel','shift_field','stock_control_field',string='Stock Controls')
    retail_sale_ids = fields.One2many('kin.retail.sale', 'shift_id', string='Retail Sales')


class TankStorage(models.Model):
    _name = 'kin.tank.storage'
    _inherit = ['mail.thread']
    _inherits = {'stock.location': 'stock_location_tmpl_id'}



    @api.model
    def run_notify_minimum_stock_level_dead_stock(self):

        tanks = self.search([])
        for tank in tanks:
            if tank.stock_level < tank.minimum_stock_level:
                    # Notify the Retail Manager
                retail_manager = tank.retail_station_id and tank.retail_station_id.retail_station_manager_id or False

                if retail_manager and retail_manager.email:
                    user_ids = []
                    user_ids.append(retail_manager.id)
                    tank.message_unsubscribe_users(user_ids=user_ids)
                    tank.message_subscribe_users(user_ids=user_ids)
                    tank.message_post(_(
                            'For your Information. The Storage Tank (%s) Stock level has reached the dead stock zone') % (
                                              tank.name),
                                          subject='Tank at Dead Stock Level Zone ',
                                          subtype='mail.mt_comment')

        return True


    @api.multi
    def btn_view_stock_location(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Location'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.location',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_location_tmpl_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_location_tmpl_id')
    def _compute_stock_location_count(self):
        for rec in self:
            rec.stock_location_count = len(rec.stock_location_tmpl_id)

    @api.depends('capacity','stock_level')
    def _compute_available_space(self):
        for rec in self:
            rec.available_space = rec.capacity - rec.stock_level
#
    # name = fields.Char('Tank No.')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    capacity = fields.Float('Capacity (ltrs)',digits=dp.get_precision('Product Price'))
    available_space = fields.Float('Available Space (ltrs)',digits=dp.get_precision('Product Price'),compute="_compute_available_space",store=True)
    stock_level = fields.Float('Stock at Hand (ltrs)',digits=dp.get_precision('Product Price'))
    current_stock_received = fields.Float('Current Stock Received (ltrs)',digits=dp.get_precision('Product Price'))
    current_int_transfer_in = fields.Float('Current Internal Transfer IN (ltrs)', digits=dp.get_precision('Product Price'))
    current_int_transfer_out = fields.Float('Current Internal Transfer OUT (ltrs)', digits=dp.get_precision('Product Price'))
    current_closing_stock = fields.Float('Current Closing Stock (ltrs)', digits=dp.get_precision('Product Price'))
    retail_station_id = fields.Many2one('kin.retail.station',string='Retail Station')
    pump_ids = fields.Many2many('kin.fuel.pump','tank_fuel_rel', 'fuel_id','tank_id', string='Pumps')
    prr_line_ids = fields.One2many('product.received.register.lines','tank_id',string='Product Received Batches')
    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    minimum_stock_level = fields.Float('Dead Stock Level (Minimum Stock Level) (ltrs)',digits=dp.get_precision('Product Price'),
                                       help='Allows notification of the people responsible for the Dead Stock')
    remark = fields.Text('Note')

    stock_location_count = fields.Integer(compute="_compute_stock_location_count", string='# of Stock Locations',
                                          copy=False, default=0)
    stock_location_tmpl_id = fields.Many2one('stock.location', 'Stock Location Template', required=True,ondelete="cascade", select=True, auto_join=True)






class ProductReorderLevel(models.Model):
    _name = 'kin.product.reorder.level'

    product_id = fields.Many2one('product.product', string='Product',domain="[('white_product','in',['pms','ago','kero'])]")
    reorder_level = fields.Float(string='Amount (ltrs)',digits=dp.get_precision('Product Price'))
    retail_station_id = fields.Many2one('kin.retail.station', string='Retail Station')


class RetailStation(models.Model):
    _name = 'kin.retail.station'
    _inherit = ['mail.thread']
    _inherits = {'stock.location': 'stock_location_tmpl_id'}


    def send_email_notification(self,retail_station,product_name,stock_level,re_order_level):
        user_ids = []
        group_obj = self.env.ref('kin_retail_station_rog.group_minimum_stock_level')
        for user in group_obj.users:
            user_ids.append(user.id)
        retail_station.message_unsubscribe_users(user_ids=user_ids)
        retail_station.message_subscribe_users(user_ids=user_ids)
        retail_station.message_post(_(
                'For your information, The %s Retail Station %s product stock level with %s qty, is below the set re-order level of %s qty. You may proceed with the product request for the respective retail station') % (
                retail_station.name, product_name, stock_level, re_order_level),
                                        subject='Retail Station Total Stock Below Re-Order Level',
                                        subtype='mail.mt_comment')

    @api.model
    def run_notify_reorder_level_stock(self):

        retail_stations = self.search([])
        tank_obj = self.env['kin.tank.storage']
        reorder_obj = self.env['kin.product.reorder.level']

        for retail_station in retail_stations:
            total_tank_stock_level_pms = total_tank_stock_level_ago = total_tank_stock_level_dpk = 0
            tank_pms = tank_obj.search([('product_id.white_product', '=', 'pms'), ('retail_station_id', '=', retail_station.id)])
            tank_ago = tank_obj.search([('product_id.white_product', '=', 'ago'), ('retail_station_id', '=', retail_station.id)])
            tank_kero = tank_obj.search([('product_id.white_product', '=', 'kero'), ('retail_station_id', '=', retail_station.id)])

            for tank in tank_pms:
                total_tank_stock_level_pms += tank.stock_level
            retail_station.total_stock_level_pms = total_tank_stock_level_pms

            for tank in tank_ago:
                total_tank_stock_level_ago += tank.stock_level
            retail_station.total_stock_level_ago = total_tank_stock_level_ago

            for tank in tank_kero:
                total_tank_stock_level_dpk += tank.stock_level
            retail_station.total_stock_level_dpk = total_tank_stock_level_dpk

            reorder_level_pms = reorder_obj.search([('product_id.white_product', '=', 'pms'), ('retail_station_id', '=', retail_station.id)])
            for product_reorder in reorder_level_pms :
                if total_tank_stock_level_pms < product_reorder.reorder_level:
                    self.send_email_notification(retail_station, product_reorder.product_id.name,total_tank_stock_level_pms, product_reorder.reorder_level)

            reorder_level_ago = reorder_obj.search(
                [('product_id.white_product', '=', 'ago'), ('retail_station_id', '=', retail_station.id)])
            for product_reorder in reorder_level_ago:
                if total_tank_stock_level_ago < product_reorder.reorder_level:
                    self.send_email_notification(retail_station, product_reorder.product_id.name,
                                                 total_tank_stock_level_ago, product_reorder.reorder_level)


            reorder_level_dpk = reorder_obj.search(
                [('product_id.white_product', '=', 'kero'), ('retail_station_id', '=', retail_station.id)])
            for product_reorder in reorder_level_dpk:
                if total_tank_stock_level_dpk < product_reorder.reorder_level:
                    self.send_email_notification(retail_station,product_reorder.product_id.name,
                                                 total_tank_stock_level_dpk, product_reorder.reorder_level)

        return True


    def _compute_total_stock_level(self):
        tank_obj = self.env['kin.tank.storage']
        for rec in self:
            total_tank_stock_level_pms = total_tank_stock_level_ago = total_tank_stock_level_dpk =  0
            tank_pms = tank_obj.search([('product_id.white_product','=','pms'),('retail_station_id','=', rec.id)])
            tank_ago = tank_obj.search([('product_id.white_product', '=', 'ago'), ('retail_station_id', '=', rec.id)])
            tank_kero = tank_obj.search([('product_id.white_product', '=', 'kero'), ('retail_station_id', '=', rec.id)])

            for tank in tank_pms:
                total_tank_stock_level_pms += tank.stock_level
            rec.total_stock_level_pms = total_tank_stock_level_pms

            for tank in tank_ago:
                total_tank_stock_level_ago += tank.stock_level
            rec.total_stock_level_ago = total_tank_stock_level_ago

            for tank in tank_kero:
                total_tank_stock_level_dpk += tank.stock_level
            rec.total_stock_level_dpk = total_tank_stock_level_dpk



    @api.multi
    def btn_view_stock_location(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Location'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.location',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_location_tmpl_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_location_tmpl_id')
    def _compute_stock_location_count(self):
        for rec in self:
            rec.stock_location_count = len(rec.stock_location_tmpl_id)


    # name = fields.Char('Retail Station Name')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one('res.country.state', 'State')
    address = fields.Char('Address')
    # pef_zone_id = fields.Many2one('kin.pef.zone','PEF Zone')
    # receiving_depot_id = fields.Many2one('kin.receiving.depot',string='Receiving Depot')
    retail_station_manager_id = fields.Many2one('res.users', string='Retail Station Manager')
    shift_supervisor_ids = fields.Many2many('res.users', string='Shift Supervisors')
    partner_ids = fields.One2many('res.partner','retail_station_id',string='Partners')
    tank_ids = fields.One2many('kin.tank.storage','retail_station_id',string='Storage Tanks')
    stock_control_ids = fields.Many2many('kin.stock.control', 'stock_control_retail_station', 'retail_station_id',
                                         'stock_control_id', string='Stock Controls')
    shift_ids = fields.Many2many('kin.shift', 'shift_retail_station', 'retail_station_id','shift_id', string='Shifts')

    total_stock_level_pms = fields.Float(digits=dp.get_precision('Product Price'),string='PMS Total Stock Level (ltrs)',compute='_compute_total_stock_level')
    total_stock_level_ago = fields.Float(digits=dp.get_precision('Product Price'),string='AGO Total Stock Level (ltrs)', compute='_compute_total_stock_level')
    total_stock_level_dpk = fields.Float(digits=dp.get_precision('Product Price'),string='DPK Total Stock Level (ltrs)', compute='_compute_total_stock_level')
    latest_cash_in_till = fields.Float('Latest Cash in Till (ltrs)',digits=dp.get_precision('Product Price'),help='Most Recent Cash In Till')
    previous_cash_in_till = fields.Float('Previous Cash in Till (ltrs)',digits=dp.get_precision('Product Price'), help='Previous Cash In Till is needed to reverse the latest cash in till on cancellation of the day pump sales')
    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    analytical_account_id = fields.Many2one('account.analytic.account',string='Analytic Account (Cost Center)')
    bank_lodgement_ids = fields.One2many('kin.bank.lodgement', 'retail_station_id', string='Bank Lodgements')
    bank_journal_ids = fields.Many2many('account.journal', 'kin_retail_station_rog_bank_journal_rel','retail_station_id','journal_id',string='Bank Journal', domain=[('type', 'in', ['bank','cash'])])

    stock_location_count = fields.Integer(compute="_compute_stock_location_count", string='# of Stock Locations', copy=False, default=0)
    stock_location_tmpl_id = fields.Many2one('stock.location', 'Stock Location Template', required=True, ondelete="cascade",select=True, auto_join=True)

    retail_station_customer_location_id = fields.Many2one('stock.location', "Retail Station Customer's Location")
    threshold_for_notification = fields.Float(digits=dp.get_precision('Product Price'),string='Threshold for Notification (ltrs)',default=100)
    product_reorder_ids = fields.One2many('kin.product.reorder.level','retail_station_id',string='Product Re-Order Levels')
    operational_loss_gain_percentage = fields.Float(string='Operational Loss/Gain Percentage (%)', help='Allows notification of the people responsible for operational loss/gain')
    is_net_difference_zero = fields.Boolean(string='Net Difference must be Zero',help='Ensure that the Net Difference for the Cash Control Equals to Zero', default=True)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def btn_view_prr(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Product Received Register'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.received.register',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.prr_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.one
    @api.depends('prr_id')
    def _compute_prr_count(self):
        self.prr_count = len(self.prr_id)


    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()


        if self.partner_id and self.partner_id.is_company_station and self.partner_id.retail_station_id :
            #create the product received register
            prr = self.env['product.received.register']
            pack_operation_line = self.pack_operation_product_ids[0]

            dn = ''
            if self.driver_id :
                dn = self.driver_id.name

            vals = {
                'driver_name' : dn,
                 'product_id' : pack_operation_line.product_id.id,
                 'quantity_loaded' : pack_operation_line.product_qty,
                'from_stock_location_id' : pack_operation_line.location_id.id,
                'to_stock_location_id': self.partner_id.retail_station_id.id,
                'is_company_product' : True,
                'ticket_ref' : self.name,
                'loading_ticket_id' : self.id,
                'state' : 'transit' ,
                'truck_no' :  self.truck_no,
                'loading_date' : self.loaded_date,


            }
            prr_obj = prr.create(vals)
            self.prr_id = prr_obj

            #Notify the Retail Manager
            retail_station = self.partner_id #the retail station
            retail_manager = retail_station.retail_station_id and retail_station.retail_station_id.retail_station_manager_id or False

            if not retail_manager:
                raise UserError(_('Please contact your admin, to create a retail manager and attach to the retail station. Then the retail station should be linked to the respective partner'))

            prr_obj.user_id  = retail_manager

            if retail_manager.email :
                user_ids = []
                user_ids.append(retail_manager.id)
            prr_obj.message_unsubscribe_users(user_ids=user_ids)
            prr_obj.message_subscribe_users(user_ids=user_ids)
            prr_obj.message_post(_(
                    'This is to notify you that some products will be coming into your retail station from %s, and a Product Received Register with ID (%s) has been Created.') % (
                                      self.location_id.name,prr_obj.name),
                                  subject='A Product Received register in transit has been Created ', subtype='mail.mt_comment')

        return  res


    prr_id = fields.Many2one('product.received.register',string='Product Received Register')
    prr_count = fields.Integer(compute="_compute_prr_count", string='# of PRR', copy=False, default=0)


class StockMove(models.Model):
    _inherit = 'stock.move'

    prr_id = fields.Many2one('product.received.register', string="Product Received Record",  track_visibility='onchange',readonly=True)
    stock_control_id = fields.Many2one('kin.stock.control', string="Stock Control", track_visibility='onchange', readonly=True)
    internal_movement_id = fields.Many2one('kin.internal.movement', string="Internal Movement",
                             track_visibility='onchange', readonly=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'


    @api.onchange('retail_station_id')
    def set_customer_location(self):
        if self.retail_station_id.stock_location_tmpl_id:
            self.property_stock_customer = self.retail_station_id.stock_location_tmpl_id

    is_company_station = fields.Boolean('Is Company Retail Station')
    retail_station_id = fields.Many2one('kin.retail.station',string='Retail Station',ondelete='restrict')


class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.multi
    def btn_view_prr(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Product Received Register'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.received.register',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.prr_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('prr_ids')
    def _compute_prr_count(self):
        for rec in self:
            rec.prr_count = len(rec.prr_ids)

    @api.multi
    def btn_view_retail_stations(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Retail Stations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.retail.station',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.retail_station_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }


    @api.depends('retail_station_ids')
    def _compute_retail_station_count(self):
        for rec in self:
            rec.retail_station_count = len(rec.retail_station_ids)

    @api.multi
    def btn_view_tank_storages(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Tank Storages'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.tank.storage',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.tank_storage_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }


    @api.depends('tank_storage_ids')
    def _compute_tank_storage_count(self):
        for rec in self:
            rec.tank_storage_count = len(rec.tank_storage_ids)


    prr_ids = fields.One2many('product.received.register','from_stock_location_id',string='Product Received Registers')
    prr_count = fields.Float(compute="_compute_prr_count", string='# of Product Received Register', copy=False, default=0)
    retail_station_count = fields.Integer(compute="_compute_retail_station_count", string='# of Retail Stations', copy=False, default=0)
    retail_station_ids = fields.One2many('kin.retail.station','stock_location_tmpl_id',string='Retail Stations')
    tank_storage_count = fields.Integer(compute="_compute_tank_storage_count", string='# of Tank Storages',
                                          copy=False, default=0)
    tank_storage_ids = fields.One2many('kin.tank.storage','stock_location_tmpl_id',string='Tank Storages')


class InternalMovement(models.Model):
    _name = 'kin.internal.movement'
    _inherit = ['mail.thread']
    _order = 'date_move desc'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft' :
                # Don't allow deletion of internal moves
                raise UserError(_('Sorry, Non-Draft Internal Movement cannot be deleted.'))

        return super(InternalMovement, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('int_move_code') or 'New'
        return super(InternalMovement, self).create(vals)

    @api.multi
    def action_confirm(self):
        if self.state == 'validate':
            raise UserError(_('This record has been previously validated. Please refresh your browser'))

        #check the current qty
        if self.qty > self.from_tank_storage_id.stock_level :
            raise UserError(_('Transfer Qty - %s is more than stock at hand - %s , for the tank storage - %s' % (self.qty,self.from_tank_storage_id.stock_level,self.from_tank_storage_id.name)))

        # create the stock move
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_move,
            'location_id': self.from_tank_storage_id.stock_location_tmpl_id.id,
            'location_dest_id': self.to_tank_storage_id.stock_location_tmpl_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id._action_confirm()
        move_id._force_assign()
        move_id._action_done()
        move_id.internal_movement_id = self.id

        self.from_tank_storage_id.stock_level -= self.qty
        self.to_tank_storage_id.stock_level += self.qty
        self.from_tank_storage_id.current_int_transfer_out += self.qty
        self.to_tank_storage_id.current_int_transfer_in += self.qty
        self.state = 'validate'


    @api.multi
    def action_cancel(self):
        if self.state == 'cancel':
            raise UserError(_('This record has been previously cancelled. Please refresh your browser'))

        #reverse the moves
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': 'Reversal for: ' + self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_move,
            'location_id': self.to_tank_storage_id.stock_location_tmpl_id.id,
            'location_dest_id':self.from_tank_storage_id.stock_location_tmpl_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id._action_confirm()
        move_id._force_assign()
        move_id._action_done()
        move_id.internal_movement_id = self.id

        self.from_tank_storage_id.stock_level += self.qty
        self.to_tank_storage_id.stock_level -= self.qty
        self.from_tank_storage_id.current_int_transfer_out -= self.qty
        self.to_tank_storage_id.current_int_transfer_in -= self.qty
        self.state = 'cancel'

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def btn_view_stock_move(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_move_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_move_ids')
    def _compute_stock_move_count(self):
        for rec in self:
            rec.stock_move_count = len(rec.stock_move_ids)




    name = fields.Char(string='Name',track_visibility='onchange')
    date_move = fields.Datetime(string='Moved Date and Time',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    from_tank_storage_id = fields.Many2one('kin.tank.storage', string='From Tank Storage', ondelete='restrict',track_visibility='onchange')
    to_tank_storage_id = fields.Many2one('kin.tank.storage', string='To Tank Storage', ondelete='restrict',track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict',track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    qty = fields.Float('Qty. (ltrs)', digits=dp.get_precision('Product Price'),track_visibility='onchange')
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False,default=0)
    stock_move_ids = fields.One2many('stock.move', 'internal_movement_id', string='Stock Moves Entry(s)')
    state = fields.Selection( [('draft', 'Draft'), ('validate', 'Done'), ('cancel', 'Cancel')],  default='draft', track_visibility='onchange')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True,
                              ondelete='restrict')

class ProductReceivedRegister(models.Model):
    _name = 'product.received.register'
    _inherit = ['mail.thread']
    _description = 'Product Received Register'
    _order = 'receiving_date desc'

    @api.multi
    def write(self, vals):
        qty_loaded = vals.get('quantity_loaded',False)
        if self.is_company_product == True and qty_loaded :
            raise UserError(_('Sorry, The Qty. Loaded cannot be changed'))

        product_id = vals.get('product_id',False)
        if self.is_company_product == True and product_id  :
            raise UserError(_('Sorry, The product cannot be changed'))

        # stop unauthorized user from accepting into a wrong station
        rid = vals.get('to_stock_location_id',False)
        if rid :
            user = self.env.user
            retail_station_obj = self.env['kin.retail.station']
            retail_station = retail_station_obj.search([('retail_station_manager_id', '=', user.id), ('id', '=', rid)])
            if not retail_station:
                raise UserError(_('You are not allowed to receive products into this retail station.'))

        res = super(ProductReceivedRegister, self).write(vals)
        l = []
        product_allocation = 0
        product_id = self.product_id
        for prr_line in self.prr_line_ids:
            l.append(prr_line.tank_id.id)
            product_allocation += prr_line.product_allocation

            if product_id != prr_line.product_id and prr_line.product_allocation != 0 :
                product_name = product_id.name
                wrong_product_name = prr_line.product_id.name
                raise UserError(_(
                    'Sorry, You want to receive %s in a %s Tank. You can only receive %s into the tanks. Please check your product discharged field for the %s tank, to ensure you are putting the quantity into the right tank' % (
                    wrong_product_name, product_name, product_name,wrong_product_name)))

        if set([x for x in l if l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
            raise UserError(_('Duplicate Tank detected. Only One Tank is allowed at a time for each product received register'))

        return res



    @api.onchange('to_stock_location_id')
    def populate_lines(self):

        tank_obj = self.env['kin.tank.storage']
        self.prr_line_ids.unlink()
        tanks = tank_obj.search([('retail_station_id', "=", self.to_stock_location_id.id)])

        lines = []
        for tank in tanks:
            lines += [(0, 0, {
                'tank_id': tank.id,
                'tank_capacity':tank.capacity,
                'current_stock_level':tank.stock_level,
            })
                      ]
        self.prr_line_ids = lines


    @api.model
    def create(self, vals):
        # No pending un-approved previous stock control for each retail station, so that there is no wrong update of the stock value for the tanks
        is_company_product = vals.get('is_company_product', False)
        rid = vals.get('to_stock_location_id', False)

        pending_stock_control_obj = self.env['kin.stock.control'].search(
            [('retail_station_id', '=', rid), ('state', 'in', ['draft', 'confirm','cancel'])])
        if pending_stock_control_obj and not is_company_product:
            pending_stock_control_date = pending_stock_control_obj.stock_control_date
            pending_stock_control_name = pending_stock_control_obj.name
            retail_station_name = pending_stock_control_obj.retail_station_id.name
            raise UserError(
                _(
                    "Sorry, there is a previously created day report with ID - %s for %s with date %s, that is still pending approval by the head office. Please contact the head office to approve/disapprove/delete the pending day report, before you can select the product. Approval of the day report is important to update the current stock at hand. " % (
                        pending_stock_control_name, retail_station_name,
                        datetime.strptime(pending_stock_control_date, "%Y-%m-%d").strftime("%d-%m-%Y"))))

        # stop unauthorized user from accepting into a wrong station
        retail_station_obj = self.env['kin.retail.station']
        user = self.env.user
        retail_station = retail_station_obj.search([('retail_station_manager_id', '=', user.id),('id', '=', rid)])
        if not retail_station:
            raise UserError(_('You are not allowed to receive products into this retail station.'))


        vals['name'] = self.env['ir.sequence'].next_by_code('prr_code') or 'New'
        res = super(ProductReceivedRegister, self).create(vals)
        l = []
        product_allocation = 0
        product_id = res.product_id
        for prr_line in res.prr_line_ids:
            l.append(prr_line.tank_id.id)
            product_allocation += prr_line.product_allocation

            if product_id != prr_line.product_id and prr_line.product_allocation != 0:
                product_name = product_id.name
                wrong_product_name = prr_line.product_id.name
                raise UserError(_(
                    'Sorry, You want to receive %s in a %s Tank. You can only receive %s into the tanks. Please check your product allocation field for the %s tank, to ensure you are putting the quantity into the right tank' % (
                        wrong_product_name, product_name, product_name, wrong_product_name)))

        if set([x for x in l if
                l.count(x) > 1]):  # see https://stackoverflow.com/questions/9835762/find-and-list-duplicates-in-a-list
            raise UserError(
                _('Duplicate Tank detected. Only One Tank is allowed at a time for each product received register'))


        return res


    @api.multi
    def action_resolution_message(self, msg):

        # Notify the Retail Manager
        retail_manager = self.user_id

        if retail_manager.email:
            user_ids = []
            user_ids.append(retail_manager.id)
            self.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'For your information the Product Received Record with ID (%s) for the retail station (%s), has been marked as resolved by %s. Resolution Message: %s.') % (
                                     self.name, self.to_stock_location_id.name,self.env.user.name,msg),
                                 subject='Product Received Register Resolution  ',
                                 subtype='mail.mt_comment')

        return self.write({'state': 'resolved',
                           'resolution_notice_date': datetime.today(), 'resolution_message': msg})


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


    def change_destination(self,new_destination):
        self.to_stock_location_id = new_destination
        # Notify the Retail Manager
        retail_station = new_destination  # the retail station
        retail_manager = retail_station and retail_station.retail_station_manager_id or False

        if not retail_manager:
            raise UserError(_(
                'Please contact your admin, to create a retail manager and attach to the retail station. Then the retail station should be linked to the respective partner'))

        if retail_manager.email:
            user_ids = []
            user_ids.append(retail_manager.id)
            self.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'This is to notify you that some products will be coming into your retail station %s, with Product Received Register ID (%s).') % (
                new_destination.name, self.name),
                                 subject='An Incoming Product Received register ',
                                 subtype='mail.mt_comment')




    def issue_notification(self):
        # Notify the issue management people
        user_ids = []
        group_obj = self.env.ref('kin_retail_station_rog.group_product_received_register_resolution')
        for user in group_obj.users:
            user_ids.append(user.id)

        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                'For your information, there is an Product Received Discrepancy with the product received quantity for the %s document. This Product Received Discrepancy is being initiated by %s, for the %s retail Station.') % (
                                  self.name, self.env.user.name, self.to_stock_location_id.name),
                              subject='Product Received Discrepancy has been Raised',
                              subtype='mail.mt_comment')



    @api.multi
    def post_issue_account(self,var_qty):
        journal_id = self.env.ref('kin_retail_station_rog.product_discrepancy_journal')
        account_id = self.product_id.discrepancy_account
        stock_output_account_id = self.product_id.categ_id.property_stock_account_output_categ_id
        analytic_account_id  = self.to_stock_location_id.analytical_account_id
        product_id = self.product_id
        partner_id= self.to_stock_location_id.partner_ids and self.to_stock_location_id.partner_ids[0] or False


        if not account_id :
            raise UserError(_('Please Set the Discrepancy Account for the Product - %s' % self.product_id.name))

        if not stock_output_account_id :
            raise UserError(_('Please Set the Stock Output account for the product in its category - %s' % self.product_id.name))

        if not journal_id:
            raise UserError(_('The Discrepancy Journal is Not Present'))

        # if not analytic_account_id :
        #     raise UserError(_('Please set the cost center account for the retail station - %s ' % self.to_stock_location_id.name))

        mv_lines = []


        if var_qty > 0 :
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': datetime.today(),
            })
            move_line = (0,0,{
                'name': self.name.split('\n')[0][:64],
                'price_unit': product_id.standard_price,
                'quantity': var_qty,
                'price': product_id.standard_price,
                'account_id': account_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                # 'analytic_account_id': analytic_account_id.id,
                'partner_id': partner_id.id,
                'debit': abs(product_id.standard_price * var_qty),
                'credit': 0,
                'ref': self.name,
            })
            mv_lines.append(move_line)

            move_line = (0,0, {
                'name': self.name.split('\n')[0][:64],
                'price_unit': product_id.standard_price,
                'quantity': var_qty,
                'price': product_id.standard_price,
                'account_id': stock_output_account_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                # 'analytic_account_id': analytic_account_id.id,
                'partner_id': partner_id.id,
                'debit': 0,
                'credit': abs(product_id.standard_price * var_qty),
                'ref': self.name,
            })
            mv_lines.append(move_line)
        elif var_qty < 0 :
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': datetime.today(),
            })
            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'price_unit': product_id.standard_price,
                'quantity': var_qty,
                'price': product_id.standard_price,
                'account_id': account_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                # 'analytic_account_id': analytic_account_id.id,
                'partner_id': partner_id.id,
                'debit': 0 ,
                'credit': abs(product_id.standard_price * var_qty),
                'ref': self.name,
            })
            mv_lines.append(move_line)

            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'price_unit': product_id.standard_price,
                'quantity': var_qty,
                'price': product_id.standard_price,
                'account_id': stock_output_account_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                # 'analytic_account_id': analytic_account_id.id,
                'partner_id': partner_id.id,
                'debit': abs(product_id.standard_price * var_qty),
                'credit': 0,
                'ref': self.name,
            })
            mv_lines.append(move_line)

        if mv_lines :
            move_id.write({'line_ids': mv_lines})

            move_id.post()
            move_id.prr_id = self.id

        return

    def issue_discharged_discrepancy_notification(self):
        # Notify the issue management people
        user_ids = []
        group_obj = self.env.ref('kin_retail_station_rog.group_product_received_register_resolution')
        for user in group_obj.users:
            user_ids.append(user.id)

        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                'For your information, there is a Product Discharged Discrepancy with the product discharged quantity for the %s document. This Product Discharged Discrepancy is being initiated by %s, for the %s retail Station.') % (
                                  self.name, self.env.user.name, self.to_stock_location_id.name),
                              subject='Product Discharged Discrepancy has been Raised',
                              subtype='mail.mt_comment')


    @api.multi
    def post_discharged_discrepancy_account(self,var_qty):
        journal_id = self.env.ref('kin_retail_station_rog.product_discrepancy_journal')
        account_id = self.product_id.discharged_discrepancy_account
        stock_output_account_id = self.product_id.categ_id.property_stock_account_output_categ_id
        analytic_account_id  = self.to_stock_location_id.analytical_account_id
        product_id = self.product_id
        partner_id= self.to_stock_location_id.partner_ids and self.to_stock_location_id.partner_ids[0] or False


        if not account_id :
            raise UserError(_('Please Set the Discharged Discrepancy Account for the Product - %s' % self.product_id.name))

        if not stock_output_account_id :
            raise UserError(_('Please Set the Stock Output account for the product in its category - %s' % self.product_id.name))

        if not journal_id:
            raise UserError(_('The Discharged Discrepancy Journal is Not Present'))

        # if not analytic_account_id :
        #     raise UserError(_('Please set the cost center account for the retail station - %s ' % self.to_stock_location_id.name))

        mv_lines = []

        if var_qty > 0:
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': datetime.today(),
            })
            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'price_unit': product_id.standard_price,
                'quantity': var_qty,
                'price': product_id.standard_price,
                'account_id': account_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                # 'analytic_account_id': analytic_account_id.id,
                'partner_id': partner_id.id,
                'debit': abs(product_id.standard_price * var_qty),
                'credit': 0,
                'ref': self.name,
            })
            mv_lines.append(move_line)

            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'price_unit': product_id.standard_price,
                'quantity': var_qty,
                'price': product_id.standard_price,
                'account_id': stock_output_account_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                # 'analytic_account_id': analytic_account_id.id,
                'partner_id': partner_id.id,
                'debit': 0,
                'credit': abs(product_id.standard_price * var_qty),
                'ref': self.name,
            })
            mv_lines.append(move_line)
        elif var_qty < 0:
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': datetime.today(),
            })
            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'price_unit': product_id.standard_price,
                'quantity': var_qty,
                'price': product_id.standard_price,
                'account_id': account_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                # 'analytic_account_id': analytic_account_id.id,
                'partner_id': partner_id.id,
                'debit': 0,
                'credit': abs(product_id.standard_price * var_qty),
                'ref': self.name,
            })
            mv_lines.append(move_line)

            move_line = (0, 0, {
                'name': self.name.split('\n')[0][:64],
                'price_unit': product_id.standard_price,
                'quantity': var_qty,
                'price': product_id.standard_price,
                'account_id': stock_output_account_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                # 'analytic_account_id': analytic_account_id.id,
                'partner_id': partner_id.id,
                'debit': abs(product_id.standard_price * var_qty),
                'credit': 0,
                'ref': self.name,
            })
            mv_lines.append(move_line)

        if mv_lines:
            move_id.write({'line_ids': mv_lines})

            move_id.post()
            move_id.prr_id = self.id

        return

    @api.multi
    def action_create_journal_entry(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('account.action_move_journal_line')
        form_view_id = model_data_obj.xmlid_to_res_id('account.view_move_form')
        journal_id = self.env.ref('kin_retail_station_rog.product_discrepancy_journal')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'domain': action.domain,
            'context': {'default_prr_id': self.id,'default_journal_id':journal_id.id},
            'res_model': action.res_model,
            'target': 'new'
        }

    @api.multi
    def action_confirm(self):
        for rec in self:
            product_allocation = 0
            for prr_line in rec.prr_line_ids:
                product_allocation += prr_line.product_allocation
            if product_allocation <= 0:
                raise UserError(_(
                        'Product should be discharged to at least one of the tanks or product discharged to each tank cannot be lesser than 0'))

            if product_allocation != rec.qty_received:
                model_data_obj = self.env['ir.model.data']
                action = self.env['ir.model.data'].xmlid_to_object('kin_retail_station_rog.action_discharged_discrepancy_confirmation')
                form_view_id = model_data_obj.xmlid_to_res_id('kin_retail_station_rog.view_discharged_discrepancy_confirmation')

                return {
                    'name': action.name,
                    'help': action.help,
                    'type': action.type,
                    'views': [[form_view_id, 'form']],
                    'target': action.target,
                    'domain': action.domain,
                    'context': {'default_prod_alloc': product_allocation, 'default_qty_rec': rec.qty_received,'default_prod_uom_name': self.product_id.name + ' ' + self.product_uom.name },
                    'res_model': action.res_model,
                    'target': 'new'
                }
            else:
                self.action_validate()


    @api.multi
    def action_validate(self):
        for rec in self:
            if rec.state in ['validate','issue']:
                raise UserError(_('This record has been previously validated. Please refresh your browser'))

            # No pending un-approved previous stock control for each retail station, so that there is no wrong update of the stock value for the tanks
            rid = self.to_stock_location_id
            pending_stock_control_obj = self.env['kin.stock.control'].search(
                [('retail_station_id', '=', rid.id), ('state', 'in', ['draft', 'confirm','cancel'])])
            if pending_stock_control_obj:
                pending_stock_control_date = pending_stock_control_obj.stock_control_date
                pending_stock_control_name = pending_stock_control_obj.name
                retail_station_name = pending_stock_control_obj.retail_station_id.name
                raise UserError(
                    _(
                        "Sorry, there is a previously created day report with ID - %s for %s with date %s, that is still pending approval by the head office. Please contact the head office to approve/disapprove/delete  the pending day report, before you can select the product. Approval of the day report is important to update the current stock at hand. " % (
                            pending_stock_control_name, retail_station_name,
                            datetime.strptime(pending_stock_control_date, "%Y-%m-%d").strftime("%d-%m-%Y"))))

            #check if all the fields have zero value
            product_allocation = 0
            for prr_line in rec.prr_line_ids:
                if not prr_line.product_allocation <= 0:
                    current_stock_level = prr_line.tank_id.stock_level
                    tank_capacity = prr_line.tank_id.capacity
                    available_capacity = tank_capacity - current_stock_level
                    if prr_line.product_allocation > available_capacity:
                        raise UserError(_('Discharged qty %s for %s is more than the available capacity of %s for %s') % (prr_line.product_allocation,prr_line.product_id.name,available_capacity,prr_line.tank_id.name))

                    #prevents two prr with the same opening stock(current stock leve) as a result of creating two draft ppr, from overriding their current stock level after one of them has been validated
                    if prr_line.current_stock_level != prr_line.tank_id.stock_level and not self.is_company_product :
                        raise UserError(_('Sorry, the tank %s current stock level has been previously updated by another process. Please delete this record and create a new product received record') % (prr_line.tank_id.name))

                    prr_line.tank_id.stock_level = prr_line.product_allocation + prr_line.tank_id.stock_level
                    prr_line.tank_id.current_stock_received += prr_line.product_allocation
                    #create the stock move
                    if prr_line.product_allocation != 0 :
                        stock_move_obj = self.env['stock.move']
                        quant_obj = self.env['stock.quant']
                        customer_location_id = self.to_stock_location_id.partner_ids and  self.to_stock_location_id.partner_ids[0].property_stock_customer or False

                        if not customer_location_id :
                            raise UserError(_('Please Contact the Admin to Create a Partner and Link it to the Retail Station'))

                        vals = {
                            'name': self.name,
                            'product_id': self.product_id.id,
                            'product_uom': self.product_id.uom_id.id,
                            'date': self.receiving_date,
                            'location_id': customer_location_id.id,
                            'location_dest_id': prr_line.tank_id.stock_location_tmpl_id.id,
                            'product_uom_qty' : prr_line.product_allocation,
                            'origin': self.name
                        }

                        move_id = stock_move_obj.create(vals)
                        move_id._action_confirm()
                        move_id._force_assign()
                        move_id._action_done()
                        move_id.prr_id = self.id

            var_qty = rec.quantity_loaded - rec.qty_received
            if var_qty != 0:
                rec.state = 'issue'
                self.post_issue_account(var_qty)
                if var_qty >= rec.to_stock_location_id.threshold_for_notification :
                    self.issue_notification()

            product_allocation = 0
            for prr_line in rec.prr_line_ids:
                product_allocation += prr_line.product_allocation
            var_discharged_qty = rec.qty_received - product_allocation
            if var_discharged_qty != 0 :
                rec.state = 'issue'
                self.post_discharged_discrepancy_account(var_discharged_qty)
                if var_discharged_qty >= rec.to_stock_location_id.threshold_for_notification:
                    self.issue_discharged_discrepancy_notification()

            if var_qty == 0 and var_discharged_qty == 0 :
                rec.state = 'validate'


    @api.multi
    def action_cancel(self):
        if self.state in 'cancel':
            raise UserError(_('This record has been previously cancelled. Please refresh your browser'))

        self.state = 'cancel'
        self.move_ids.button_cancel()
        self.move_ids.unlink()




    @api.multi
    def action_cancel_reverse_qty(self):
        retail_station_id = self.to_stock_location_id

        day_sale_stock_obj = self.env['kin.stock.control']
        sale_stock_control_later = day_sale_stock_obj.search([('retail_station_id', '=', retail_station_id.id), ('create_date', '>', self.create_date)])
        for sc in sale_stock_control_later :
            if not self.is_company_product:
                the_date = str(datetime.strptime(self.create_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y  %H:%M:%S"))
                sc_name = sc.name
                retail_station_name = retail_station_id.name
                raise UserError(_('Sorry, the day report with ID %s, created on or after %s, for the retail station (%s), must be cancelled and deleted to update the stock qty. You may contact the head office for the operation') % (sc_name,the_date,retail_station_name))


        prr_later_date = str(datetime.strptime(self.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1))
        prr_later = self.search([('to_stock_location_id', '=', retail_station_id.id), ('create_date', '>', prr_later_date)])
        for prr in prr_later:
            if not self.is_company_product:
                prr_later_date = str(
                    (datetime.strptime(self.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime(
                        "%d-%m-%Y  %H:%M:%S"))
                prr_name = prr.name
                retail_station_name = retail_station_id.name
                raise UserError(_('Sorry, the product received record with ID %s, created on or after %s, for the retail station (%s), must be cancelled and deleted, to update the stock qty.') % (prr_name,prr_later_date,retail_station_name))


        for prr_line in self.prr_line_ids:
            prr_line.tank_id.stock_level = prr_line.tank_id.stock_level - prr_line.product_allocation
            prr_line.tank_id.current_stock_received -= prr_line.product_allocation

        #Reverse Stock moves because the system cannot allow cancellation of done stock moves
        stock_move_obj = self.env['stock.move']
        for stock_move in  self.stock_move_ids:
            customer_location_id = self.to_stock_location_id.partner_ids and self.to_stock_location_id.partner_ids[0].property_stock_customer or False

            if not customer_location_id:
                raise UserError(_('Please Contact the Admin to Create a Partner and Link it to the Retail Station'))

            if stock_move.location_dest_id.id == customer_location_id.id : #erp stock modu;e does not create stock move when the source and destination are thesame
                stock_move.prr_id = False
            else :
            # create the reverse stock move
                vals = {
                        'name': 'Reversal for: ' + stock_move.origin,
                        'product_id': stock_move.product_id.id,
                        'product_uom': stock_move.product_uom.id,
                        'date': datetime.today(),
                        'location_id': stock_move.location_dest_id.id,
                        'location_dest_id': customer_location_id.id,
                        'product_uom_qty': stock_move.product_uom_qty,
                        'origin': stock_move.origin
                }
                stock_move.prr_id = False # prevent creation duplicate stock moves incase of more reversals
                move_id = stock_move_obj.create(vals)
                move_id._action_confirm()
                move_id._force_assign()
                move_id._action_done()
                move_id.prr_id = self.id


        self.action_cancel()


#TODO try to know if the system can pick values from the current internal move in and out and product received, rather than from the tank storage
    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_transit(self):
        self.state = 'transit'


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.is_company_product == True or (rec.is_company_product == False and rec.state != 'draft') :
                raise UserError(_('Sorry, you can only delete manually created record in draft state'))

        return super(ProductReceivedRegister, self).unlink()


    def _compute_discrepancy(self):
        for rec in self:
            rec.qty_discrepancy = rec.quantity_loaded - rec.qty_received
            rec.product_price = rec.product_id.standard_price
            rec.amt_discrepancy = rec.product_id.standard_price * rec.qty_discrepancy


    def _compute_discharged(self):
        for rec in self:
            total_allocation = 0
            for prr_line in rec.prr_line_ids :
                total_allocation += prr_line.product_allocation
            rec.qty_discharged = total_allocation
            rec.amt_discharged = rec.product_id.standard_price * total_allocation
            rec.discharged_discrepancy_qty = rec.qty_received - rec.qty_discharged
            rec.discharged_discrepancy_amt =  rec.product_id.standard_price * rec.discharged_discrepancy_qty


    @api.multi
    def btn_view_stock_move(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Stock Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.stock_move_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_move_ids')
    def _compute_stock_move_count(self):
        for rec in self:
            rec.stock_move_count = len(rec.stock_move_ids)

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

    @api.depends('move_ids')
    def _compute_jnr_count(self):
        for rec in self:
            rec.jnr_count = len(rec.move_ids)

    @api.depends('to_stock_location_id')
    def _compute_retail_station_manager(self):
        self.retail_station_manager_id = self.to_stock_location_id.retail_station_manager_id

    @api.depends('truck_date_in','truck_date_out')
    def _compute_time_interval(self):
        if self.truck_date_in  and self.truck_date_out :
            self.time_interval = datetime.strptime(self.truck_date_out , DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(self.truck_date_in , DEFAULT_SERVER_DATETIME_FORMAT)

    def _get_user_retail_station(self):
        user = self.env.user
        retail_station_obj = self.env['kin.retail.station']
        retail_station = retail_station_obj.search([('retail_station_manager_id','=',user.id)])
        return retail_station and retail_station[0].id

    name = fields.Char(string='Name')
    loading_date = fields.Date(string='Loading Date')
    receiving_date = fields.Date(string='Receiving Date',required=True)
    truck_no = fields.Char('Truck No')
    waybill_no = fields.Char('Waybill No')
    qty_discrepancy = fields.Float('Received Discrepancy Qty. (ltrs)',digits=dp.get_precision('Product Price'),compute='_compute_discrepancy')
    amt_discrepancy = fields.Monetary('Received Discrepancy Amount (NGN)',compute='_compute_discrepancy')
    product_price = fields.Monetary('Product Cost Price (NGN)',compute='_compute_discrepancy')
    qty_discharged = fields.Float('Discharged Quantity (ltrs)',compute='_compute_discharged')
    amt_discharged= fields.Monetary('Discharged Amount (NGN)',compute='_compute_discharged')
    discharged_discrepancy_qty = fields.Float('Discharged Discrepancy Qty. (ltrs)', digits=dp.get_precision('Product Price'),compute='_compute_discharged')
    discharged_discrepancy_amt = fields.Monetary('Discharged Discrepancy Amount. (NGN)', compute='_compute_discharged')
    driver_name = fields.Char(string="Driver's  Name")
    driver_mobile_no = fields.Char(string="Driver's  Mobile Number")
    truck_date_in = fields.Datetime('Truck In Date and Time ')
    truck_date_out = fields.Datetime('Truck Out Date and Time')
    time_interval = fields.Char(string='Time Interval',compute='_compute_time_interval')
    resolution_message = fields.Text('Resolution Message')
    resolution_notice_date = fields.Datetime('Resolution Notice Date')
    product_id = fields.Many2one('product.product', string='Product',ondelete='restrict')
    product_uom = fields.Many2one('product.uom',related='product_id.uom_id', string='Unit of Measure')
    quantity_loaded = fields.Float('Qty. Loaded (Waybill Qty.) (ltrs)',digits=dp.get_precision('Product Price'))
    qty_received = fields.Float('Qty. Received (ltrs)',digits=dp.get_precision('Product Price'))
    from_stock_location_id = fields.Many2one('stock.location',string='From Location',ondelete='restrict')
    to_stock_location_id = fields.Many2one('kin.retail.station',string='To Retail Station',default=_get_user_retail_station,ondelete='restrict')
    is_company_product  = fields.Boolean('Is Company Product')
    ticket_ref = fields.Char('Loading Ticket Reference')
    other_ref = fields.Char('Other Reference')
    loading_ticket_id = fields.Many2one('stock.picking',string='Loading Tickets')
    lt_count = fields.Integer(compute="_compute_lt_count", string='# of Loading Ticket', copy=False, default=0)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True,ondelete='restrict')
    prr_line_ids = fields.One2many('product.received.register.lines','prr_id',string='Product Discharged to Tanks')
    retail_station_manager_id = fields.Many2one('res.users',string='Retail Station Manager',compute='_compute_retail_station_manager',store=True,ondelete='restrict')
    retail_manager_comment = fields.Text("Retail Manager's Comment")
    jnr_count = fields.Integer(compute="_compute_jnr_count", string='# of Journal Items', copy=False, default=0)
    move_ids = fields.One2many('account.move', 'prr_id', string='Journal Entry(s)')
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False, default=0)
    stock_move_ids = fields.One2many('stock.move', 'prr_id', string='Stock Moves Entry(s)')
    state = fields.Selection(
        [('draft', 'Draft'),('transit', 'In Transit'),('issue', 'Discrepancy'),('resolved', 'Resolved'), ('validate', 'Done'),('cancel', 'Cancel')],
        default='draft', track_visibility='onchange')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id,ondelete='restrict')


class ProductReceivedRegisterLines(models.Model):
    _name = 'product.received.register.lines'

    @api.depends('tank_capacity','current_stock_level','product_allocation')
    def _compute_values(self):
        for rec in self:
            rec.available_capacity = rec.tank_capacity - rec.current_stock_level
            rec.exp_closing_dip = rec.current_stock_level + rec.product_allocation

    #using related="" is a loophole to reset the parent model without a state
    @api.depends('prr_id.state')
    def _compute_state(self):
        for rec in self:
            rec.state = rec.prr_id.state

    tank_id = fields.Many2one('kin.tank.storage',string='Storage Tank',ondelete='restrict')
    tank_capacity = fields.Float(digits=dp.get_precision('Product Price'),string='Tank Capacity (ltrs)')
    product_id = fields.Many2one(related='tank_id.product_id',string='Product',ondelete='restrict',store=True)
    product_uom = fields.Many2one(related='tank_id.product_uom',string='Unit')
    current_stock_level = fields.Float(digits=dp.get_precision('Product Price'),string='Current Stock Level (ltrs)')
    product_allocation = fields.Float(digits=dp.get_precision('Product Price'),string='Product Discharged Qty. (ltrs)')
    available_capacity = fields.Float(string='Available Capacity', compute='_compute_values',store=True)
    prr_id = fields.Many2one('product.received.register',string='Product Received Register')
    is_company_product = fields.Boolean('Is Company Product',related='prr_id.is_company_product',store=True)
    state = fields.Selection(
        [('draft', 'Draft'),('transit', 'In Transit'),('issue', 'Discrepancy'),('resolved', 'Resolved'), ('validate', 'Done'),('cancel', 'Cancel')],
         compute='_compute_state' ,store=True)
    exp_closing_dip = fields.Float(string='Expected Closing Dip', compute='_compute_values',digits=dp.get_precision('Product Price'),store=True)

class ProductProduct(models.Model):
    _inherit = 'product.template'

    discrepancy_account = fields.Many2one('account.account','Product Received Discrepancy Account')
    discharged_discrepancy_account = fields.Many2one('account.account', 'Product Discharged Discrepancy Account')
    white_product = fields.Selection([
        ('pms', 'PMS'),
        ('ago', 'AGO'),
        ('kero', 'DPK')

    ], string='White Product')

class AccountMove(models.Model):
    _inherit = 'account.move'

    prr_id = fields.Many2one('product.received.register', string="Product Received Register", track_visibility='onchange',
                                 readonly=True)
    stock_control_id = fields.Many2one('kin.stock.control', string="Stock Control",
                             track_visibility='onchange',
                             readonly=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    prr_id = fields.Many2one(related='move_id.prr_id',string="Product Received Register",  store=True)
    stock_control_id = fields.Many2one(related='move_id.stock_control_id', string="Stock Control",store=True)

class ResCompanyRetail(models.Model):
    _inherit = "res.company"

    inventory_change = fields.Many2one('account.account', 'Inventory Change Account')
    gain_account = fields.Many2one('account.account', 'Gain Account')
    loss_account = fields.Many2one('account.account', 'Loss Account')