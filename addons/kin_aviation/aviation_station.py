# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, ValidationError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
import  time


class BowserMovementBowser(models.Model):
    _name = 'kin.bowser.movement.bowser.aviation'
    _inherit = ['mail.thread']
    _order = 'date_move desc'

    @api.onchange('density', 'conductivity', 'is_appearance')
    def check_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not an Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
        elif self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
        elif self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
        else:
            self.is_passed = True

    def test_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not a Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Appearance Check.'))

        if self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Density Check'))

        if self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Conductivity Check'))

        self.is_passed = True


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft' :
                # Don't allow deletion of internal moves
                raise UserError(_('Sorry, Non-Draft Bowser Movement cannot be deleted.'))

        return super(BowserMovementBowser, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('bow_move_avb_code') or 'New'
        res = super(BowserMovementBowser, self).create(vals)
        self.env['test.obj'].check_status(res)
        self.env['test.obj'].check_records(res)
        return res

    @api.multi
    def action_confirm(self):
        self.test_parameters()
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

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
            'location_id': self.from_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'location_dest_id': self.to_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.bowser_movement_avb_id = self.id

        self.from_tank_storage_id.stock_level -= self.qty
        self.to_tank_storage_id.stock_level += self.qty
        self.from_tank_storage_id.current_int_transfer_out += self.qty
        self.to_tank_storage_id.current_int_transfer_in += self.qty
        self.state = 'validate'


    @api.multi
    def action_cancel(self):
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)
        #reverse the moves
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': 'Reversal for: ' + self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_move,
            'location_id': self.to_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'location_dest_id':self.from_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.bowser_movement_avb_id = self.id

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


    def _get_user_aviation_station(self):
        user = self.env.user
        aviation_station_obj = self.env['kin.aviation.station']
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id', '=', user.id)])
        return aviation_station[0].id


    name = fields.Char(string='Name',track_visibility='onchange')
    date_move = fields.Date(string='Date',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    to_tank_storage_id = fields.Many2one('kin.refueller.bowser', string='To Bowser / Refueller', ondelete='restrict',track_visibility='onchange')
    from_tank_storage_id = fields.Many2one('kin.refueller.bowser', string='From Bowser / Refueller', ondelete='restrict',track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict',track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    qty = fields.Float('Qty. (ltrs)', digits=dp.get_precision('Product Price'),track_visibility='onchange')
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False,default=0)
    stock_move_ids = fields.One2many('stock.move', 'bowser_movement_avb_id', string='Stock Moves Entry(s)')
    state = fields.Selection( [('draft', 'Draft'), ('validate', 'Done'), ('cancel', 'Cancel')],  default='draft', track_visibility='onchange')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True,
                              ondelete='restrict')
    aviation_station_id = fields.Many2one('kin.aviation.station',string='Aviation Station',default=_get_user_aviation_station,ondelete='restrict')


    # Quality Control Procedure
    is_appearance = fields.Boolean('Bright and Clear')
    temp = fields.Float('Observed Temperature')
    density = fields.Float('Density @‎ 15 degree (kg/m3)',
                           digits=dp.get_precision('Density and Conductivity'))  # (0.775-0.840)kg/m3
    conductivity = fields.Float('Conductivity (pS/m)',
                                digits=dp.get_precision('Density and Conductivity'))  # (50-600)pS/m
    qhsse_remark = fields.Text('QHSSE Remark')
    is_passed = fields.Boolean('Is Passed')



class BowserMovementTank(models.Model):
    _name = 'kin.bowser.movement.tank.aviation'
    _description = 'From Bowser to Tank'
    _inherit = ['mail.thread']
    _order = 'date_move desc'

    @api.onchange('density', 'conductivity', 'is_appearance')
    def check_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not an Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
        elif self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
        elif self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
        else:
            self.is_passed = True

    def test_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not a Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Appearance Check.'))

        if self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Density Check'))

        if self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Conductivity Check'))

        self.is_passed = True


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft' :
                # Don't allow deletion of internal moves
                raise UserError(_('Sorry, Non-Draft Bowser Movement cannot be deleted.'))

        return super(BowserMovementTank, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('bow_move_avt_code') or 'New'
        res = super(BowserMovementTank, self).create(vals)
        self.env['test.obj'].check_status(res)
        self.env['test.obj'].check_records(res)
        return res

    @api.multi
    def action_confirm(self):
        self.test_parameters()
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

        #check the current qty
        if self.qty > self.from_tank_storage_id.stock_level :
            raise UserError(_('Transfer Qty - %s is more than stock at hand - %s , for the bowser - %s' % (self.qty,self.from_tank_storage_id.stock_level,self.from_tank_storage_id.name)))

        # create the stock move
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_move,
            'location_id': self.from_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'location_dest_id': self.to_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.bowser_movement_avt_id = self.id

        self.from_tank_storage_id.stock_level -= self.qty
        self.to_tank_storage_id.stock_level += self.qty
        self.from_tank_storage_id.current_int_transfer_out += self.qty
        self.to_tank_storage_id.current_int_transfer_in += self.qty
        self.state = 'validate'


    @api.multi
    def action_cancel(self):
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)
        #reverse the moves
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': 'Reversal for: ' + self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_move,
            'location_id': self.to_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'location_dest_id':self.from_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.bowser_movement_avt_id = self.id

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


    def _get_user_aviation_station(self):
        user = self.env.user
        aviation_station_obj = self.env['kin.aviation.station']
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id', '=', user.id)])
        return aviation_station[0].id


    name = fields.Char(string='Name',track_visibility='onchange')
    date_move = fields.Date(string='Date',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    to_tank_storage_id = fields.Many2one('kin.tank.storage.aviation', string='To Tank Storage', ondelete='restrict',track_visibility='onchange')
    from_tank_storage_id = fields.Many2one('kin.refueller.bowser', string='From Bowser / Refueller', ondelete='restrict',track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict',track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    qty = fields.Float('Qty. (ltrs)', digits=dp.get_precision('Product Price'),track_visibility='onchange')
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False,default=0)
    stock_move_ids = fields.One2many('stock.move', 'bowser_movement_avt_id', string='Stock Moves Entry(s)')
    state = fields.Selection( [('draft', 'Draft'), ('validate', 'Done'), ('cancel', 'Cancel')],  default='draft', track_visibility='onchange')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True,
                              ondelete='restrict')
    aviation_station_id = fields.Many2one('kin.aviation.station',string='Aviation Station',default=_get_user_aviation_station,ondelete='restrict')


    # Quality Control Procedure
    is_appearance = fields.Boolean('Bright and Clear')
    temp = fields.Float('Observed Temperature')
    density = fields.Float('Density @‎ 15 degree (kg/m3)',
                           digits=dp.get_precision('Density and Conductivity'))  # (0.775-0.840)kg/m3
    conductivity = fields.Float('Conductivity (pS/m)',
                                digits=dp.get_precision('Density and Conductivity'))  # (50-600)pS/m
    qhsse_remark = fields.Text('QHSSE Remark')
    is_passed = fields.Boolean('Is Passed')




class BowserMovement(models.Model):
    _name = 'kin.bowser.movement.aviation'
    _description = 'Tank to Bowser Transfer'
    _inherit = ['mail.thread']
    _order = 'date_move desc'

    @api.onchange('density', 'conductivity', 'is_appearance')
    def check_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not an Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
        elif self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
        elif self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
        else:
            self.is_passed = True

    def test_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not a Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Appearance Check.'))

        if self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Density Check'))

        if self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Conductivity Check'))

        self.is_passed = True


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft' :
                # Don't allow deletion of internal moves
                raise UserError(_('Sorry, Non-Draft Bowser Movement cannot be deleted.'))

        return super(BowserMovement, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('bow_move_av_code') or 'New'
        res = super(BowserMovement, self).create(vals)
        self.env['test.obj'].check_status(res)
        self.env['test.obj'].check_records(res)
        return res

    @api.multi
    def action_confirm(self):
        self.test_parameters()
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

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
            'location_id': self.from_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'location_dest_id': self.to_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.bowser_movement_av_id = self.id

        self.from_tank_storage_id.stock_level -= self.qty
        self.to_tank_storage_id.stock_level += self.qty
        self.from_tank_storage_id.current_int_transfer_out += self.qty
        self.to_tank_storage_id.current_int_transfer_in += self.qty
        self.state = 'validate'


    @api.multi
    def action_cancel(self):
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)
        #reverse the moves
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': 'Reversal for: ' + self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_move,
            'location_id': self.to_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'location_dest_id':self.from_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.bowser_movement_av_id = self.id

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


    def _get_user_aviation_station(self):
        user = self.env.user
        aviation_station_obj = self.env['kin.aviation.station']
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id', '=', user.id)])
        return aviation_station[0].id


    name = fields.Char(string='Name',track_visibility='onchange')
    date_move = fields.Date(string='Date',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    from_tank_storage_id = fields.Many2one('kin.tank.storage.aviation', string='From Tank Storage', ondelete='restrict',track_visibility='onchange')
    to_tank_storage_id = fields.Many2one('kin.refueller.bowser', string='To Bowser / Refueller', ondelete='restrict',track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict',track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    qty = fields.Float('Qty. (ltrs)', digits=dp.get_precision('Product Price'),track_visibility='onchange')
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False,default=0)
    stock_move_ids = fields.One2many('stock.move', 'bowser_movement_av_id', string='Stock Moves Entry(s)')
    state = fields.Selection( [('draft', 'Draft'), ('validate', 'Done'), ('cancel', 'Cancel')],  default='draft', track_visibility='onchange')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True,
                              ondelete='restrict')
    aviation_station_id = fields.Many2one('kin.aviation.station',string='Aviation Station',default=_get_user_aviation_station,ondelete='restrict')


    # Quality Control Procedure
    is_appearance = fields.Boolean('Bright and Clear')
    temp = fields.Float('Observed Temperature')
    density = fields.Float('Density @‎ 15 degree (kg/m3)',
                           digits=dp.get_precision('Density and Conductivity'))  # (0.775-0.840)kg/m3
    conductivity = fields.Float('Conductivity (pS/m)',
                                digits=dp.get_precision('Density and Conductivity'))  # (50-600)pS/m
    qhsse_remark = fields.Text('QHSSE Remark')
    is_passed = fields.Boolean('Is Passed')


class InternalMovement(models.Model):
    _name = 'kin.internal.movement.aviation'
    _inherit = ['mail.thread']
    _order = 'date_move desc'

    @api.onchange('density', 'conductivity', 'is_appearance')
    def check_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not an Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
        elif self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
        elif self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
        else:
            self.is_passed = True

    def test_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not a Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Appearance Check.'))

        if self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Density Check'))

        if self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Conductivity Check'))

        self.is_passed = True


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft' :
                # Don't allow deletion of internal moves
                raise UserError(_('Sorry, Non-Draft Internal Movement cannot be deleted.'))

        return super(InternalMovement, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('int_move_av_code') or 'New'
        res = super(InternalMovement, self).create(vals)
        self.env['test.obj'].check_status(res)
        self.env['test.obj'].check_records(res)
        return res

    @api.multi
    def action_confirm(self):
        if self.state == 'validate':
            raise UserError(_('This record has been previously validated. Please refresh your browser'))

        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

        #check the current qty
        if self.qty > self.from_tank_storage_id.stock_level :
            raise UserError(_('Transfer Qty - %s is more than stock at hand - %s , for the tank storage - %s' % (self.qty,self.from_tank_storage_id.stock_level,self.from_tank_storage_id.name)))

        self.test_parameters()
        # create the stock move
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_move,
            'location_id': self.from_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'location_dest_id': self.to_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.internal_movement_av_id = self.id

        self.from_tank_storage_id.stock_level -= self.qty
        self.to_tank_storage_id.stock_level += self.qty
        self.from_tank_storage_id.current_int_transfer_out += self.qty
        self.to_tank_storage_id.current_int_transfer_in += self.qty
        self.state = 'validate'


    @api.multi
    def action_cancel(self):
        if self.state == 'cancel':
            raise UserError(_('This record has been previously cancelled. Please refresh your browser'))

        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

        #reverse the moves
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': 'Reversal for: ' + self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_move,
            'location_id': self.to_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'location_dest_id':self.from_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'product_uom_qty': self.qty,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.internal_movement_av_id = self.id

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


    def _get_user_aviation_station(self):
        user = self.env.user
        aviation_station_obj = self.env['kin.aviation.station']
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id', '=', user.id)])
        return aviation_station[0].id

    name = fields.Char(string='Name',track_visibility='onchange')
    date_move = fields.Date(string='Date',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    from_tank_storage_id = fields.Many2one('kin.tank.storage.aviation', string='From Tank Storage', ondelete='restrict',track_visibility='onchange')
    to_tank_storage_id = fields.Many2one('kin.tank.storage.aviation', string='To Tank Storage', ondelete='restrict',track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict',track_visibility='onchange')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of Measure')
    qty = fields.Float('Qty. (ltrs)', digits=dp.get_precision('Product Price'),track_visibility='onchange')
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False,default=0)
    stock_move_ids = fields.One2many('stock.move', 'internal_movement_av_id', string='Stock Moves Entry(s)')
    state = fields.Selection( [('draft', 'Draft'), ('validate', 'Done'), ('cancel', 'Cancel')],  default='draft', track_visibility='onchange')
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True,
                              ondelete='restrict')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station', default=_get_user_aviation_station, ondelete='restrict')

    # Quality Control Procedure
    is_appearance = fields.Boolean('Bright and Clear')
    temp = fields.Float('Observed Temperature')
    density = fields.Float('Density @‎ 15 degree (kg/m3)',
                           digits=dp.get_precision('Density and Conductivity'))  # (0.775-0.840)kg/m3
    conductivity = fields.Float('Conductivity (pS/m)',
                                digits=dp.get_precision('Density and Conductivity'))  # (50-600)pS/m
    qhsse_remark = fields.Text('QHSSE Remark')
    is_passed = fields.Boolean('Is Passed')


class ProductReceivedRegister(models.Model):
    _name = 'product.received.register.aviation'
    _inherit = ['mail.thread']
    _description = 'Product Received Register'
    _order = 'id desc'

    @api.onchange('is_tractor_cabin','is_spark_arrestor','is_seal_intact','is_tyre_condition_extra_type','is_fire_extinguisher','is_amber_light','is_truck_dedicated','is_truck_epoxycoated','is_reverse_alarm','density','conductivity','is_appearance')
    def check_parameters(self):
        aviation_station = self.to_stock_location_id
        if self.is_tractor_cabin == False or \
            self.is_spark_arrestor == False or \
            self.is_seal_intact == False or \
            self.is_tyre_condition_extra_type == False or \
            self.is_fire_extinguisher == False or \
            self.is_amber_light == False or \
            self.is_truck_dedicated == False or \
            self.is_truck_epoxycoated == False or \
            self.is_reverse_alarm == False :
            self.is_passed = False
        elif self.is_appearance == False :
            self.is_passed = False
        elif self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
        elif self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
        else :
            self.is_passed = True



    def test_parameters(self):
        if self.is_tractor_cabin == False or \
            self.is_spark_arrestor == False or \
            self.is_seal_intact == False or \
            self.is_tyre_condition_extra_type == False or \
            self.is_fire_extinguisher == False or \
            self.is_amber_light == False or \
            self.is_truck_dedicated == False or \
            self.is_truck_epoxycoated == False or \
            self.is_reverse_alarm == False :
            self.is_passed = False
            raise UserError(_('Truck Inspection Test Failed. Please check truck and tick the checks in the lists accordingly'))

        aviation_station = self.to_stock_location_id

        if  self.is_appearance == False :
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Appearance Check.'))

        if self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Density Check'))

        if self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Conductivity Check'))

        self.is_passed = True


    @api.multi
    def write(self, vals):
        qty_loaded = vals.get('quantity_loaded',False)
        if self.is_company_product == True and qty_loaded :
            raise UserError(_('Sorry, The Qty. Loaded cannot be changed'))

        product_id = vals.get('product_id',False)
        if self.is_company_product == True and product_id  :
            raise UserError(_('Sorry, The product cannot be changed'))



        # stop unauthorized user from accepting into a wrong station
        rid = vals.get('to_stock_location_id', False)
        if rid:
            user = self.env.user
            aviation_station_obj = self.env['kin.aviation.station']
            aviation_station = aviation_station_obj.search([('aviation_station_manager_id', '=', user.id), ('id', '=', rid)])
            if not aviation_station:
                raise UserError(_('You are not allowed to receive products into this aviation station.'))

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
        tank_obj = self.env['kin.tank.storage.aviation']
        self.prr_line_ids.unlink()
        tanks = tank_obj.search([('aviation_station_id', "=", self.to_stock_location_id.id)])
        #
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
        # No pending un-approved previous stock control for each aviation station, so that there is no wrong update of the stock value for the tanks
        is_company_product = vals.get('is_company_product', False)
        avid = vals.get('to_stock_location_id', False)

        # stop unauthorized user from accepting into a wrong station
        aviation_station_obj = self.env['kin.aviation.station']
        user = self.env.user
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id', '=', user.id),('id', '=', avid)])
        if not aviation_station:
            raise UserError(_('You are not allowed to receive products into this aviation station.'))

        vals['name'] = self.env['ir.sequence'].next_by_code('prr_code_av') or 'New'
        res = super(ProductReceivedRegister, self).create(vals)

        self.env['test.obj'].check_status(res)
        self.env['test.obj'].check_records(res)

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

        # Notify the aviation Manager
        aviation_manager = self.user_id

        if aviation_manager.email:
            user_ids = []
            user_ids.append(aviation_manager.id)
            self.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'For your information the Product Received Record with ID (%s) for the aviation station (%s), has been marked as resolved by %s. Resolution Message: %s.') % (
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
        # Notify the aviation Manager
        aviation_station = new_destination  # the aviation station
        aviation_manager = aviation_station and aviation_station.aviation_station_manager_id or False

        if not aviation_manager:
            raise UserError(_(
                'Please contact your admin, to create a aviation manager and attach to the aviation station. Then the aviation station should be linked to the respective partner'))

        if aviation_manager.email:
            user_ids = []
            user_ids.append(aviation_manager.id)
            self.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            self.message_post(_(
                'This is to notify you that some products will be coming into your aviation station %s, with Product Received Register ID (%s).') % (
                new_destination.name, self.name),
                                 subject='An Incoming Product Received register ',
                                 subtype='mail.mt_comment')




    def issue_notification(self):
        # Notify the issue management people
        user_ids = []
        group_obj = self.env.ref('kin_aviation.group_product_received_register_resolution_aviation')
        for user in group_obj.users:
            user_ids.append(user.id)

        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                'For your information, there is an Product Received Discrepancy with the product received quantity for the %s document. This Product Received Discrepancy is being initiated by %s, for the %s aviation Station.') % (
                                  self.name, self.env.user.name, self.to_stock_location_id.name),
                              subject='Product Received Discrepancy has been Raised',
                              subtype='mail.mt_comment')



    @api.multi
    def post_issue_account(self,var_qty):
        journal_id = self.env.ref('kin_aviation.product_discrepancy_journal_aviation')
        account_id = self.product_id.discrepancy_account_aviation
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
        #     raise UserError(_('Please set the cost center account for the aviation station - %s ' % self.to_stock_location_id.name))

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
            move_id.prr_av_id = self.id

        return

    def issue_discharged_discrepancy_notification(self):
        # Notify the issue management people
        user_ids = []
        group_obj = self.env.ref('kin_aviation.group_product_received_register_resolution_aviation')
        for user in group_obj.users:
            user_ids.append(user.id)

        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                'For your information, there is a Product Discharged Discrepancy with the product discharged quantity for the %s document. This Product Discharged Discrepancy is being initiated by %s, for the %s aviation Station.') % (
                                  self.name, self.env.user.name, self.to_stock_location_id.name),
                              subject='Product Discharged Discrepancy has been Raised',
                              subtype='mail.mt_comment')


    @api.multi
    def post_discharged_discrepancy_account(self,var_qty):
        journal_id = self.env.ref('kin_aviation.product_discrepancy_journal_aviation')
        account_id = self.product_id.discharged_discrepancy_account_aviation
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
        #     raise UserError(_('Please set the cost center account for the aviation station - %s ' % self.to_stock_location_id.name))

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
            move_id.prr_av_id = self.id

        return

    @api.multi
    def action_create_journal_entry(self):
        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('account.action_move_journal_line')
        form_view_id = model_data_obj.xmlid_to_res_id('account.view_move_form')
        journal_id = self.env.ref('kin_aviation.product_discrepancy_journal_aviation')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'domain': action.domain,
            'context': {'default_prr_av_id': self.id,'default_journal_id':journal_id.id},
            'res_model': action.res_model,
            'target': 'new'
        }

    @api.multi
    def action_confirm(self):
        self.test_parameters()
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)
        for rec in self:
            product_allocation = 0
            for prr_line in rec.prr_line_ids:
                product_allocation += prr_line.product_allocation
            if product_allocation <= 0:
                raise UserError(_(
                        'Product should be discharged to at least one of the tanks or product discharged to each tank cannot be lesser than 0'))

            if product_allocation <> rec.qty_received:
                model_data_obj = self.env['ir.model.data']
                action = self.env['ir.model.data'].xmlid_to_object('kin_aviation.action_discharged_discrepancy_confirmation_aviation')
                form_view_id = model_data_obj.xmlid_to_res_id('kin_aviation.view_discharged_discrepancy_confirmation_aviation')

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

            product_allocation = 0
            for prr_line in rec.prr_line_ids:
                if not prr_line.product_allocation <= 0 :
                    current_stock_level = prr_line.tank_id.stock_level
                    tank_capacity = prr_line.tank_id.capacity
                    available_capacity = tank_capacity - current_stock_level
                    if prr_line.product_allocation > available_capacity:
                        raise UserError(_('Discharged qty %s for %s is more than the available capacity of %s for %s') % (prr_line.product_allocation,prr_line.product_id.name,available_capacity,prr_line.tank_id.name))

                    #prevents two prr with the same opening stock(current stock leve) as a result of creating two draft ppr, from overriding their current stock level after one of them has been validated
                    # if prr_line.current_stock_level != prr_line.tank_id.stock_level and not self.is_company_product :
                    #     raise UserError(_('Sorry, the tank %s current stock level has been previously updated by another process. Please delete this record and create a new product received record') % (prr_line.tank_id.name))

                    prr_line.tank_id.stock_level = prr_line.product_allocation + prr_line.tank_id.stock_level
                    prr_line.tank_id.current_stock_received += prr_line.product_allocation

                    #create the stock move
                    stock_move_obj = self.env['stock.move']
                    quant_obj = self.env['stock.quant']
                    customer_location_id = self.to_stock_location_id.partner_ids and  self.to_stock_location_id.partner_ids[0].property_stock_customer or False

                    if not customer_location_id :
                        raise UserError(_('Please Contact the Admin to Create a Partner and Link it to the aviation Station'))

                    vals = {
                        'name': self.name,
                        'product_id': self.product_id.id,
                        'product_uom': self.product_id.uom_id.id,
                        'date': self.receiving_date,
                        'location_id': customer_location_id.id,
                        'location_dest_id': prr_line.tank_id.stock_location_tmpl_aviation_id.id,
                        'product_uom_qty' : prr_line.product_allocation,
                        'origin': self.name
                    }

                    move_id = stock_move_obj.create(vals)
                    move_id.action_confirm()
                    move_id.force_assign()
                    move_id.action_done()
                    move_id.prr_av_id = self.id

            #Meter Check
            if rec.meter_end <= rec.meter_start:
                raise UserError('Meter End Value cannot be lower than or equal to Meter Start Value')

            if rec.meter_start != rec.pump_id.totalizer:
                raise ValidationError(_(
                    'The Meter Start is not equal to the Totalizer value. The Totalizer has been previously updated. Please delete this record and recreate a new one'))

            #update the discharge pump totalizer
            rec.pump_id.totalizer = rec.meter_end

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

            var_qty_haul = rec.qty_haulaged - rec.qty_received
            if var_qty_haul != 0:
                rec.state = 'issue'
                self.post_issue_account(var_qty_haul)
                if var_qty >= rec.to_stock_location_id.threshold_for_notification:
                    self.issue_notification()

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
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)
        aviation_station_id = self.to_stock_location_id

        for prr_line in self.prr_line_ids:
            prr_line.tank_id.stock_level = prr_line.tank_id.stock_level - prr_line.product_allocation
            prr_line.tank_id.current_stock_received -= prr_line.product_allocation

        #reverse the totalizer value
        self.pump_id.totalizer = self.meter_start

        # Reverse Stock moves because the system cannot allow cancellation of done stock moves
        stock_move_obj = self.env['stock.move']
        for stock_move in self.stock_move_ids:
            customer_location_id = self.to_stock_location_id.partner_ids and self.to_stock_location_id.partner_ids[
                0].property_stock_customer or False

            if not customer_location_id:
                raise UserError(_('Please Contact the Admin to Create a Partner and Link it to the aviation Station'))

            if stock_move.location_dest_id.id == customer_location_id.id:  # erp stock modu;e does not create stock move when the source and destination are thesame
                stock_move.prr_id = False
            else:
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
                stock_move.prr_av_id = False  # prevent creation duplicate stock moves incase of more reversals
                move_id = stock_move_obj.create(vals)
                move_id.action_confirm()
                move_id.force_assign()
                move_id.action_done()
                move_id.prr_av_id = self.id

        self.action_cancel()


    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_transit(self):
        self.state = 'transit'


    # @api.multi
    # @api.constrains('create_date')
    # def check_prr_date(self):
    #     for rec in self:
    #         prr_later_date = str(datetime.strptime(rec.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1))
    #         prr_later = rec.search([('to_stock_location_id', '=', rec.aviation_station_id.id), ('create_date', '>', prr_later_date)])
    #         for prr in prr_later:
    #             if not rec.is_company_product:
    #                 prr_later_date = str((datetime.strptime(rec.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime("%d-%m-%Y  %H:%M:%S"))
    #                 prr_name = prr.name
    #                 aviation_station_name = rec.aviation_station_id.name
    #                 raise ValidationError(_('Sorry, the product received record with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (prr_name,prr_later_date,aviation_station_name))

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.is_company_product == True or (rec.is_company_product == False and rec.state != 'draft') :
                raise UserError(_('Sorry, you can only delete manually created record in draft state'))

        return super(ProductReceivedRegister, self).unlink()



    def _compute_discrepancy(self):
        for rec in self:
            rec.qty_discrepancy = rec.qty_received - rec.quantity_loaded
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
    def _compute_aviation_station_manager(self):
        self.aviation_station_manager_id = self.to_stock_location_id.aviation_station_manager_id

    @api.depends('truck_date_in','truck_date_out')
    def _compute_time_interval(self):
        if self.truck_date_in  and self.truck_date_out :
            self.time_interval = datetime.strptime(self.truck_date_out , DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(self.truck_date_in , DEFAULT_SERVER_DATETIME_FORMAT)


    def _get_user_aviation_station(self):
        user = self.env.user
        aviation_station_obj = self.env['kin.aviation.station']
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id','=',user.id)])
        return aviation_station[0]


    def _get_discharge_pump(self):
        avs = self._get_user_aviation_station()
        discharge_pump_obj = self.env['kin.fuel.pump.aviation']
        discharge_pump = discharge_pump_obj.search([('aviation_station_id','=',avs.id),('pump_type','=','is_discharging_pump')])
        return discharge_pump[0]

    @api.depends('meter_start','meter_end','quantity_loaded')
    def _compute_received(self):
        for rec in self:
            rec.qty_received = rec.meter_end - rec.meter_start
            rec._compute_discrepancy()


    @api.depends('pump_id')
    def _compute_meter_start(self):
        for rec in self:
            rec.meter_start = rec.pump_id.totalizer

    name = fields.Char(string='Name')
    loading_date = fields.Date(string='Loading Date')
    receiving_date = fields.Date(string='Receiving Date')
    truck_no = fields.Char('Truck No')
    waybill_no = fields.Char('Waybill No')
    qty_discrepancy = fields.Float('Received Discrepancy Qty.',compute='_compute_discrepancy',help="Waybill Qty. - Meter Qty. Received")
    amt_discrepancy = fields.Float('Received Discrepancy Amount',compute='_compute_discrepancy')
    product_price = fields.Float('Product Cost Price',compute='_compute_discrepancy')
    qty_discharged = fields.Float('Discharged Quantity',compute='_compute_discharged')
    amt_discharged= fields.Float('Discharged Amount',compute='_compute_discharged')
    discharged_discrepancy_qty = fields.Float('Discharged Discrepancy Qty.', compute=_compute_discharged)
    discharged_discrepancy_amt = fields.Float('Discharged Discrepancy Amount.', compute=_compute_discharged)
    driver_name = fields.Char(string="Driver's  Name")
    driver_mobile_no = fields.Char(string="Driver's  Mobile Number")
    truck_date_in = fields.Datetime('Truck In Date and Time ')
    truck_date_out = fields.Datetime('Truck Out Date and Time')
    time_interval = fields.Char(string='Time Interval',compute='_compute_time_interval')
    resolution_message = fields.Text('Resolution Message')
    resolution_notice_date = fields.Datetime('Resolution Notice Date')
    product_id = fields.Many2one('product.product', string='Product',ondelete='restrict')
    product_uom = fields.Many2one('product.uom',related='product_id.uom_id', string='Unit of Measure')
    quantity_loaded = fields.Float('Waybill Qty.')
    pump_id = fields.Many2one('kin.fuel.pump.aviation', default=_get_discharge_pump, string='Discharge Pump')
    meter_start = fields.Float('Meter Start',compute=_compute_meter_start,store=True)
    meter_end =  fields.Float('Meter End')
    qty_received = fields.Float('Meter Qty. Received',compute='_compute_received', store=True)
    qty_haulaged = fields.Float('Qty. Haulaged')
    from_stock_location_id = fields.Many2one('stock.location',string='From Stock Location',ondelete='restrict')
    to_stock_location_id = fields.Many2one('kin.aviation.station',string='To Aviation Station',default=_get_user_aviation_station,ondelete='restrict')
    is_company_product  = fields.Boolean('Is Company Product')
    ticket_ref = fields.Char('Loading Ticket Reference')
    other_ref = fields.Char('Other Reference')
    loading_ticket_id = fields.Many2one('stock.picking',string='Loading Tickets')
    lt_count = fields.Integer(compute="_compute_lt_count", string='# of Loading Ticket', copy=False, default=0)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True,ondelete='restrict')
    prr_line_ids = fields.One2many('product.received.register.lines.aviation','prr_id',string='Product Received Allocations to Tanks')
    aviation_station_manager_id = fields.Many2one('res.users',string='Aviation Station Manager',compute='_compute_aviation_station_manager',store=True,ondelete='restrict')
    aviation_manager_comment = fields.Text("Aviation Manager's Comment")
    jnr_count = fields.Integer(compute="_compute_jnr_count", string='# of Journal Items', copy=False, default=0)
    move_ids = fields.One2many('account.move', 'prr_av_id', string='Journal Entry(s)')
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False, default=0)
    stock_move_ids = fields.One2many('stock.move', 'prr_av_id', string='Stock Moves Entry(s)')
    state = fields.Selection(
        [('draft', 'Draft'),('transit', 'In Transit'),('issue', 'Discrepancy'),('resolved', 'Resolved'), ('validate', 'Done'),('cancel', 'Cancel')],
        default='draft', track_visibility='onchange')

    date_time_arrival = fields.Datetime(string='Date and Time of Arrival')
    check_date = fields.Date(string='Check Date', default=fields.Datetime.now, required=True)
    is_tractor_cabin = fields.Boolean(string='Tractor Cabin')
    is_ppes = fields.Boolean(string='PPES')
    is_spark_arrestor = fields.Boolean(string='Spark Arrestor')
    is_seal_intact = fields.Boolean(string='Seal Intact')
    is_tyre_condition_extra_type = fields.Boolean(string='Is Tyre Condition with Extra Tyre')
    is_fire_extinguisher = fields.Boolean(string='Fire Extinguisher (DPC)')
    is_amber_light = fields.Boolean(string='Amber Light')
    is_truck_dedicated = fields.Boolean(string='Truck Dedicated for JETA-1')
    is_truck_epoxycoated = fields.Boolean(string='Truck Epoxycoated')
    is_reverse_alarm = fields.Boolean(string='Reverse Alarm')
    note_security = fields.Text('Security Officer Comment')
    note_safety = fields.Text('Safety Officer Comment')
    note_depot = fields.Text('Depot Superintendent Comment')

    #Quality Control Procedure
    is_appearance = fields.Boolean('Bright and Clear')
    temp = fields.Float('Observed Temperature')
    density = fields.Float('Density @‎ 15 degree (kg/m3)',digits=dp.get_precision('Density and Conductivity'))  #(0.775-0.840)kg/m3
    conductivity = fields.Float('Conductivity (pS/m)',digits=dp.get_precision('Density and Conductivity'))  #(50-600)pS/m
    qhsse_remark = fields.Text('QHSSE Remark')
    is_passed = fields.Boolean('Is Passed')




class ProductReceivedRegisterLines(models.Model):
    _name = 'product.received.register.lines.aviation'

    @api.depends('is_company_product','tank_capacity','current_stock_level','product_allocation')
    def _compute_values(self):
        for rec in self:
            rec.available_capacity = rec.tank_capacity - rec.current_stock_level
            rec.exp_closing_dip = rec.current_stock_level + rec.product_allocation

    #using related="" is a loophole to reset the parent model without a state
    @api.depends('prr_id.state')
    def _compute_state(self):
        for rec in self:
            rec.state = rec.prr_id.state

    tank_id = fields.Many2one('kin.tank.storage.aviation',string='Storage Tank',ondelete='restrict')
    tank_capacity = fields.Float(digits=dp.get_precision('Product Price'),string='Tank Capacity')
    product_id = fields.Many2one(related='tank_id.product_id',string='Product',ondelete='restrict',store=True)
    product_uom = fields.Many2one(related='tank_id.product_uom',string='Unit')
    current_stock_level = fields.Float(digits=dp.get_precision('Product Price'),string='Current Stock Level')
    product_allocation = fields.Float(digits=dp.get_precision('Product Price'),string='Product Discharged Qty.')
    available_capacity = fields.Float(string='Available Capacity', compute='_compute_values',store=True)
    prr_id = fields.Many2one('product.received.register.aviation',string='Product Received Register')
    is_company_product = fields.Boolean('Is Company Product',related='prr_id.is_company_product',store=True)
    state = fields.Selection(
        [('draft', 'Draft'),('transit', 'In Transit'),('issue', 'Discrepancy'),('resolved', 'Resolved'), ('validate', 'Done'),('cancel', 'Cancel')],
         compute='_compute_state' ,store=True)
    exp_closing_dip = fields.Float(string='Expected Closing Dip', compute='_compute_values',digits=dp.get_precision('Product Price'),store=True)



class ProductProduct(models.Model):
    _inherit = 'product.template'

    discrepancy_account_aviation = fields.Many2one('account.account','Product Received Discrepancy Aviation Account')
    discharged_discrepancy_account_aviation = fields.Many2one('account.account', 'Product Discharged Discrepancy Aviation Account')
    white_product_aviation = fields.Selection([
        ('atk','ATK')

    ], string='Aviation Product')

class AccountMove(models.Model):
    _inherit = 'account.move'

    prr_av_id = fields.Many2one('product.received.register.aviation', string="Product Received Register", track_visibility='onchange',
                                 readonly=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    prr_av_id = fields.Many2one(related='move_id.prr_av_id',string="Product Received Register",  store=True)
    # stock_control_id = fields.Many2one(related='move_id.stock_control_id', string="Stock Control",store=True)

class ResCompanyAviation(models.Model):
    _inherit = "res.company"

    # inventory_change_aviation = fields.Many2one('account.account', 'Inventory Change Aviation Account')
    # gain_account_aviation = fields.Many2one('account.account', 'Gain Aviation Account')
    # loss_account_aviation = fields.Many2one('account.account', 'Loss Aviation Account')
    #

class ProductReorderLevel(models.Model):
    _name = 'kin.product.reorder.level.aviation'

    product_id = fields.Many2one('product.product', string='Product',domain="[('white_product_aviation','=','atk')]" )
    reorder_level = fields.Float(string='Amount')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station')


class AviationStation(models.Model):
    _name = 'kin.aviation.station'
    _inherit = ['mail.thread']
    _inherits = {'stock.location': 'stock_location_tmpl_aviation_id'}


    def send_email_notification(self,aviation_station,product_name,stock_level,re_order_level):
        user_ids = []
        group_obj = self.env.ref('kin_aviation.group_minimum_stock_level')
        for user in group_obj.users:
            user_ids.append(user.id)
        aviation_station.message_unsubscribe_users(user_ids=user_ids)
        aviation_station.message_subscribe_users(user_ids=user_ids)
        aviation_station.message_post(_(
                'For your information, The %s Aviation Station %s product stock level with %s qty, is below the set re-order level of %s qty. You may proceed with the product request for the respective aviation station') % (
                aviation_station.name, product_name, stock_level, re_order_level),
                                        subject='Aviation Station Total Stock Below Re-Order Level',
                                        subtype='mail.mt_comment')

    @api.model
    def run_notify_reorder_level_stock(self):

        aviation_stations = self.search([])
        tank_obj = self.env['kin.tank.storage.aviation']
        reorder_obj = self.env['kin.product.reorder.level.aviation']

        for aviation_station in aviation_stations:
            total_tank_stock_level =  0
            tank_atk = tank_obj.search([('product_id.white_product_aviation', '=', 'atk'), ('aviation_station_id', '=', aviation_station.id)])

            for tank in tank_atk:
                total_tank_stock_level += tank.stock_level
            aviation_station.total_stock_level_pms = total_tank_stock_level

            reorder_level = reorder_obj.search([('product_id.white_product_aviation', '=', 'atk'), ('aviation_station_id', '=', aviation_station.id)])
            for product_reorder in reorder_level :
                if total_tank_stock_level < product_reorder.reorder_level:
                    self.send_email_notification(aviation_station, product_reorder.product_id.name,total_tank_stock_level, product_reorder.reorder_level)

        return True


    def _compute_total_stock_level(self):
        for rec in self:
            total_tank_stock_level = 0
            for tank in rec.tank_ids:
                total_tank_stock_level += tank.stock_level
            rec.total_stock_level = total_tank_stock_level


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
            'domain': [('id', 'in', [x.id for x in self.stock_location_tmpl_aviation_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_location_tmpl_aviation_id')
    def _compute_stock_location_count(self):
        for rec in self:
            rec.stock_location_count = len(rec.stock_location_tmpl_aviation_id)


    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one('res.country.state', 'State')
    address = fields.Char('Address')
    aviation_station_manager_id = fields.Many2one('res.users', string='Aviation Station Manager')
    # shift_supervisor_ids = fields.Many2many('res.users', string='Shift Supervisors')
    partner_ids = fields.One2many('res.partner','aviation_station_id',string='Partners')
    tank_ids = fields.One2many('kin.tank.storage.aviation','aviation_station_id',string='Storage Tanks')
    aviation_record_ids = fields.One2many('kin.aviation.record','aviation_station_id',string='Aviation Records')

    total_stock_level = fields.Float(string='Total Stock Level',compute='_compute_total_stock_level')
    reorder_level = fields.Float('Re-Order Level',
                                       help='Allows notification of the people responsible for stock below minimum level')
    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    analytical_account_id = fields.Many2one('account.analytic.account',string='Analytic Account (Cost Center)')
    stock_location_count = fields.Integer(compute="_compute_stock_location_count", string='# of Stock Locations',
                                          copy=False, default=0)
    stock_location_tmpl_aviation_id = fields.Many2one('stock.location', 'Stock Location Template', required=True,
                                             ondelete="cascade", select=True, auto_join=True)
    aviation_station_customer_location_id = fields.Many2one('stock.location', "Aviation Station Customer's Location")
    tank_difference_location_id = fields.Many2one('stock.location', "Tank Difference Location")
    bowser_difference_location_id = fields.Many2one('stock.location', "Bowser Difference Location")
    threshold_for_notification = fields.Float(string='Threshold for Notification')
    aviation_officer_ids = fields.Many2many('res.users', string='Aviation Officers')

    density_min = fields.Float('Density Minimum (kg/m3)', default='0.775')
    density_max = fields.Float('Density Maximum (kg/m3)', default='0.840')
    conductivity_min = fields.Float('Conductivity Minimum (pS/m)', default='50')
    conductivity_max = fields.Float('Conductivity Maximum(pS/m)', default='600')

class TankStorage(models.Model):
    _name = 'kin.tank.storage.aviation'
    _inherit = ['mail.thread']
    _inherits = {'stock.location': 'stock_location_tmpl_aviation_id'}

    @api.model
    def run_notify_minimum_stock_level_dead_stock(self):

        tanks = self.search([])
        for tank in tanks:
            if tank.stock_level < tank.minimum_stock_level:
                    # Notify the aviation Manager
                aviation_manager = tank.aviation_station_id and tank.aviation_station_id.aviation_station_manager_id or False

                if aviation_manager and aviation_manager.email:
                    user_ids = []
                    user_ids.append(aviation_manager.id)
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
            'domain': [('id', 'in', [x.id for x in self.stock_location_tmpl_aviation_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_location_tmpl_aviation_id')
    def _compute_stock_location_count(self):
        for rec in self:
            rec.stock_location_count = len(rec.stock_location_tmpl_aviation_id)

    @api.depends('capacity','stock_level')
    def _compute_available_space(self):
        for rec in self:
            rec.available_space = rec.capacity - rec.stock_level


    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    capacity = fields.Float('Capacity')
    stock_level = fields.Float('Stock at Hand')
    current_stock_received = fields.Float('Current Stock Received')
    current_int_transfer_in = fields.Float('Current Internal Transfer IN')
    current_int_transfer_out = fields.Float('Current Internal Transfer OUT')
    current_closing_stock = fields.Float('Current Closing Stock')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station')
    pump_ids = fields.Many2many('kin.fuel.pump.aviation', 'aviation_tank_fuel_rel', 'fuel_id', 'tank_id', string='Pumps')
    prr_line_ids = fields.One2many('product.received.register.lines.aviation', 'tank_id',
                                   string='Product Received Batches')
    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    minimum_stock_level = fields.Float('Dead Stock Level (Minimum Stock Level)',
                                       help='Allows notification of the people responsible for the Dead Stock')
    remark = fields.Text('Note')
    available_space = fields.Float('Available Space', compute="_compute_available_space", store=True)

    stock_location_count = fields.Integer(compute="_compute_stock_location_count", string='# of Stock Locations',
                                          copy=False, default=0)
    stock_location_tmpl_aviation_id = fields.Many2one('stock.location', 'Stock Location Template', required=True,
                                             ondelete="cascade", select=True, auto_join=True)


class FuelPumpPriceHistory(models.Model):
    _name = 'kin.fuel.pump.history.aviation'
    _order = 'date_change desc'

    product_id = fields.Many2one('product.product', 'Product', required=True, ondelete='cascade')
    uom_id = fields.Many2one(string='Unit', related='product_id.uom_id')
    user_id = fields.Many2one('res.users', string='Changed By')
    date_change = fields.Datetime(string='Changed Date and Time',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    previous_price = fields.Monetary(string='Previous Price')
    new_price = fields.Monetary(string='New Price')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    fuel_pump_id = fields.Many2one('kin.fuel.pump.aviation', string='Fuel Pump')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station',
                                        related='fuel_pump_id.aviation_station_id', store=True)

class FuelPumpTotalizerHistory(models.Model):
    _name = 'kin.fuel.totalizer.history.aviation'
    _order = 'date_change desc'

    product_id = fields.Many2one('product.product', 'Product', required=True, ondelete='restrict')
    uom_id = fields.Many2one(string='Unit', related='product_id.uom_id',ondelete='restrict')
    user_id = fields.Many2one('res.users', string='Changed By',ondelete='restrict')
    date_change = fields.Datetime(string='Changed Date and Time',
                                  default=lambda self: datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    previous_totalizer = fields.Float(string='Previous Totalizer Value')
    new_totalizer = fields.Float(string='New Totalizer Value')
    fuel_pump_id = fields.Many2one('kin.fuel.pump.aviation', string='Fuel Pump Meter',ondelete='restrict')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station',
                                        related='fuel_pump_id.aviation_station_id', store=True,ondelete='restrict')



class FuelPump(models.Model):
    _name = 'kin.fuel.pump.aviation'
    _inherit = ['mail.thread']

    @api.multi
    def change_prices(self, new_price):
        fuel_pump_history = self.env['kin.fuel.pump.history.aviation']
        for rec in self:
            rec.price = new_price

            # Send Email Notification for Price Change
            user_ids = []
            group_obj = self.env.ref('kin_aviation.group_change_price_aviation')
            for user in group_obj.users:
                user_ids.append(user.id)
            rec.message_subscribe_users(user_ids=user_ids)
            rec.message_post(
                _('Fuel Pump Price change alert for the fuel pump - %s in %s, was changed from %s to %s') % (
                    rec.name, rec.aviation_station_id.name, rec.price, new_price),
                subject='Fuel Pump Price Change Notification Created', subtype='mail.mt_comment')

            # Record the Price Change History
            fuel_pump_history.create({
                'product_id': rec.product_id.id,
                'user_id': self.env.user.id,
                'previous_price': rec.price,
                'new_price': new_price,
                'fuel_pump_id': rec.id
            })


    @api.multi
    def change_totalizer_value(self,new_totalizer):

        fuel_totalizer_history = self.env['kin.fuel.totalizer.history.aviation']

        # Send Email Notification for Totalizer Value
        user_ids = []
        group_obj = self.env.ref('kin_aviation.group_change_totalizer_value_aviation')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(
            _('Fuel Pump Meter Totalizer Value change alert for the fuel Pump Meter - %s in %s, was changed from %s to %s') % (
                self.name, self.aviation_station_id.name, self.totalizer, new_totalizer),
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


    name = fields.Char('Pump No.', track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    totalizer = fields.Float('Totalizer', track_visibility='onchange')
    previous_totalizer = fields.Float('Previous Totalizer', track_visibility='onchange')
    tank_ids = fields.Many2many('kin.tank.storage.aviation', 'aviation_tank_fuel_rel', 'tank_id', 'fuel_id', string='Tanks',
                                help='Tank Supplying to the Pump', track_visibility='onchange')
    bowser_ids = fields.Many2many('kin.refueller.bowser', 'bowser_tank_fuel_rel', 'bowser_id', 'fuel_id',
                                string='Bowsers', track_visibility='onchange')
    aviation_station_id = fields.Many2one(related='tank_ids.aviation_station_id', store=True, string='Aviation Station')
    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    price = fields.Monetary(string='Price')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    pump_price_history_ids = fields.One2many('kin.fuel.pump.history.aviation', 'fuel_pump_id', string='Fuel Pump History')
    pump_totalizer_history_ids = fields.One2many('kin.fuel.totalizer.history.aviation', 'fuel_pump_id',
                                                 string='Fuel Pump Meter Totalizer Value History')

    pump_type = fields.Selection([('is_discharging_pump','Is Discharging Pump'),('is_loading_pump','Is Loading Pump'),('is_bowser_loading_pump','Is Bowser Loading Pump')],string="Pump Type")



class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_company_aviation_station = fields.Boolean('Is Company Aviation Station')
    aviation_station_id = fields.Many2one('kin.aviation.station',string='Aviation Station')


class StockMove(models.Model):
    _inherit = 'stock.move'

    prr_av_id = fields.Many2one('product.received.register.aviation', string="Product Received Record",  track_visibility='onchange',readonly=True)
    stock_control_av_id = fields.Many2one('kin.aviation.record', string="Stock Control", track_visibility='onchange', readonly=True)
    internal_movement_av_id = fields.Many2one('kin.internal.movement.aviation', string="Internal Movement",
                             track_visibility='onchange', readonly=True)
    bowser_movement_av_id = fields.Many2one('kin.bowser.movement.aviation', string="Tank to Bowser Movement",
                                              track_visibility='onchange', readonly=True)
    bowser_movement_avt_id = fields.Many2one('kin.bowser.movement.tank.aviation', string="Bowser to Tank Movement",
                                            track_visibility='onchange', readonly=True)
    bowser_movement_avb_id = fields.Many2one('kin.bowser.movement.bowser.aviation', string="Bowser to Bowser Movement",
                                             track_visibility='onchange', readonly=True)
    loading_av_id = fields.Many2one('kin.loading.record', string="Loading Record Movement",
                                             track_visibility='onchange', readonly=True)
    delivery_receipt_av_id = fields.Many2one('kin.fuel.delivery.receipt', string="Fuel Delivery Receipt Movement",
                                             track_visibility='onchange', readonly=True)


class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.multi
    def btn_view_aviation_stations(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Aviation Stations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.aviation.station',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.aviation_station_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('aviation_station_ids')
    def _compute_aviation_station_count(self):
        for rec in self:
            rec.aviation_station_count = len(rec.aviation_station_ids)

    @api.multi
    def btn_view_tank_storages(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Tank Storages'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.tank.storage.aviation',
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

    @api.multi
    def btn_view_bowsers(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Bowsers'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.refueller.bowser',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.bowser_ids])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('bowser_ids')
    def _compute_bowser_count(self):
        for rec in self:
            rec.bowser_count = len(rec.bowser_ids)


    @api.multi
    def btn_view_prr_aviation(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Product Received Register'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.received.register.aviation',
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

    prr_ids = fields.One2many('product.received.register.aviation','from_stock_location_id',string='Product Received Registers')
    prr_count = fields.Integer(compute="_compute_prr_count", string='# of Product Received Register', copy=False, default=0)

    aviation_station_ids = fields.One2many('kin.aviation.station', 'stock_location_tmpl_aviation_id', string='Aviation Stations')
    aviation_station_count = fields.Integer(compute="_compute_aviation_station_count", string='# of Aviation Stations',
                                            copy=False, default=0)

    tank_storage_ids = fields.One2many('kin.tank.storage.aviation', 'stock_location_tmpl_aviation_id', string='Tank Storages')
    tank_storage_count = fields.Integer(compute="_compute_tank_storage_count", string='# of Tank Storages',
                                        copy=False, default=0)

    bowser_ids = fields.One2many('kin.refueller.bowser','stock_location_tmpl_bowser_id',string='Bowsers')
    bowser_count = fields.Integer(compute="_compute_bowser_count", string='# of Bowsers',copy=False, default=0)


class RefuellerBowser(models.Model):
    _name = 'kin.refueller.bowser'
    _inherit = ['mail.thread']
    _inherits = {'stock.location': 'stock_location_tmpl_bowser_id'}


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
            'domain': [('id', 'in', [x.id for x in self.stock_location_tmpl_bowser_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('stock_location_tmpl_bowser_id')
    def _compute_stock_location_count(self):
        for rec in self:
            rec.stock_location_count = len(rec.stock_location_tmpl_bowser_id)

    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    capacity = fields.Float('Capacity')
    stock_level = fields.Float('Stock at Hand')
    current_stock_received = fields.Float('Current Stock Received')
    current_int_transfer_in = fields.Float('Current Internal Transfer IN')
    current_int_transfer_out = fields.Float('Current Internal Transfer OUT')
    current_closing_stock = fields.Float('Current Closing Stock')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station')
    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    minimum_stock_level = fields.Float('Dead Stock Level (Minimum Stock Level)',
                                       help='Allows notification of the people responsible for the Dead Stock')
    remark = fields.Text('Note')
    available_space = fields.Float('Available Space',  store=True)
    pump_ids = fields.Many2many('kin.fuel.pump.aviation', 'bowser_tank_fuel_rel', 'fuel_id', 'bowser_id',
                                string='Pumps')
    stock_location_count = fields.Integer(compute="_compute_stock_location_count", string='# of Stock Locations',
                                          copy=False, default=0)
    stock_location_tmpl_bowser_id = fields.Many2one('stock.location', 'Stock Location Template', required=True,
                                                    ondelete="cascade", select=True, auto_join=True)


class RefuellerLoadingRecord(models.Model):
    _name = 'kin.refueller.loading.record'
    _description = 'Refueller Dippings'
    _inherit = ['mail.thread']


    @api.model
    def create(self, vals):
        res = super(RefuellerLoadingRecord, self).create(vals)
        if res.refueller_closing_dip < 0 :
            raise UserError(_('Refueller closing dip cannot go negative'))
        # if res.refueller_closing_dip > res.stock_at_hand:
        #     raise UserError(_('Refueller closing dip cannot be greater than refueller stock at hand'))


        return res

    @api.multi
    def write(self, vals):
        res = super(RefuellerLoadingRecord, self).write(vals) #since the stock_at_hand field is readonly, it means the val field cannot get new changes for this field, thus the only option is to do write() first before accessing the field value. Accessing the value first before write() will give you the outdated field value, which is wrong for the calculation
        if self.refueller_closing_dip < 0 :
            raise UserError(_('Refueller closing dip cannot go negative'))
        # if self.refueller_closing_dip > self.stock_at_hand:
        #     raise UserError(_('Refueller closing dip cannot be greater than refueller stock at hand'))

        return res

    @api.depends('refueller_opening_dip', 'stock_at_hand')
    def _check_stock_values(self):
        for rec in self:
            if rec.refueller_closing_dip > rec.stock_at_hand:
                warning_mess = {
                    'title': _('Stock at Hand > Refueller Opening dip!'),
                    'message': _('Refueller closing dip cannot be greater than stock at hand')
                }
                return {'warning': warning_mess}

    @api.depends('refueller_opening_dip', 'stock_received','refueller_closing_dip','current_int_transfer_in','current_int_transfer_out')
    def _compute_measures(self):
        for rec in self:
            rec.stock_at_hand = rec.refueller_opening_dip + rec.stock_received + rec.current_int_transfer_in - rec.current_int_transfer_out
            rec.refueller_difference = rec.stock_at_hand - rec.refueller_closing_dip


    name = fields.Char('Name')
    refueller_id = fields.Many2one('kin.refueller.bowser',string='Refueller')
    product_id = fields.Many2one('product.product', related='refueller_id.product_id', string='Product')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    stock_received = fields.Float('Stock Received')
    current_int_transfer_in = fields.Float('Transfer IN')
    current_int_transfer_out = fields.Float('Transfer OUT')
    stock_at_hand = fields.Float('Stock at Hand', compute='_compute_measures', help='Refueller Opening Dip + Stock Received + Transfer IN - Transfer OUT')
    refueller_opening_dip = fields.Float(string='Refueller Opening Dip')
    refueller_closing_dip = fields.Float(string='Refueller Closing Dip')
    refueller_difference = fields.Float(string='Refueller Difference',compute='_compute_measures')
    aviation_record_id = fields.Many2one('kin.aviation.record', string='Aviation Record')



class LoadingRecord(models.Model):
    _name = 'kin.loading.record'
    _description = 'Loading Record'
    _inherit = ['mail.thread']
    _order = 'id desc'


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('lr_code_av') or 'New'
        res = super(LoadingRecord, self).create(vals)
        self.env['test.obj'].check_status(res)
        self.env['test.obj'].check_records(res)
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft','cancel']:
                raise UserError(_('Sorry, Non-draft/Cancelled Record cannot be deleted'))
        return super(LoadingRecord, self).unlink()


    @api.onchange('pump_id')
    def populate_opening_meter(self):
        for rec in self:
            rec.loading_opening_meter = rec.pump_id.totalizer


    @api.depends('loading_opening_meter','loading_closing_meter')
    def _compute_difference(self):
        for rec in self :
            rec.loading_difference = rec.loading_closing_meter - rec.loading_opening_meter

    @api.onchange('density','conductivity','is_appearance')
    def check_parameters(self):
        aviation_station = self.aviation_station_id
        if self.is_appearance == False :
            self.is_passed = False
        elif self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
        elif self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
        else :
            self.is_passed = True

    def test_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not an Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Appearance Check.'))

        if self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Density Check'))

        if self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Conductivity Check'))

        self.is_passed = True

    @api.multi
    def action_confirm(self):
        self.test_parameters()
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

        asi = self.aviation_station_id

        if self.loading_closing_meter < self.loading_opening_meter:
            raise UserError('Loading Closing Meter Value cannot be lower than Loading Opening Meter Value')

        if self.loading_opening_meter != self.pump_id.totalizer:
            raise ValidationError(_('The Loading Opening Meter is not equal to the Totalizer value. The Totalizer has been previously updated. Please delete this record and recreate a new one'))

        self.pump_id.totalizer = self.loading_closing_meter


        # check the current qty
        if self.loading_difference > self.from_tank_storage_id.stock_level:
            raise UserError(_('Transfer Qty - %s is more than stock at hand - %s , for the tank storage - %s' % (
            self.loading_difference, self.from_tank_storage_id.stock_level, self.from_tank_storage_id.name)))

        # create the stock move
        stock_move_obj = self.env['stock.move']

        vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.date_load,
            'location_id': self.from_tank_storage_id.stock_location_tmpl_aviation_id.id,
            'location_dest_id': self.to_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'product_uom_qty': self.loading_difference,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.loading_av_id = self.id

        self.from_tank_storage_id.stock_level -= self.loading_difference
        self.to_tank_storage_id.stock_level += self.loading_difference
        self.from_tank_storage_id.current_int_transfer_out += self.loading_difference
        self.to_tank_storage_id.current_int_transfer_in += self.loading_difference

        self.state = 'confirm'


    @api.multi
    def action_cancel(self):
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

        #reverse the totalizer value
        self.pump_id.totalizer = self.loading_opening_meter

        # create the reverse stock move
        # Reverse Stock moves because the system cannot allow cancellation of done stock moves
        stock_move_obj = self.env['stock.move']
        for stock_move in self.stock_move_ids:
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
            stock_move.loading_av_id = False  # prevent creation duplicate stock moves incase of more reversals
            move_id = stock_move_obj.create(vals)
            move_id.action_confirm()
            move_id.force_assign()
            move_id.action_done()
            move_id.loading_av_id = self.id

            self.from_tank_storage_id.stock_level += self.loading_difference
            self.to_tank_storage_id.stock_level -= self.loading_difference
            self.from_tank_storage_id.current_int_transfer_out -= self.loading_difference
            self.to_tank_storage_id.current_int_transfer_in -= self.loading_difference
        self.state = 'cancel'



    @api.multi
    def action_draft(self):
        self.state = 'draft'

    def _get_user_aviation_station(self):
        user = self.env.user
        aviation_station_obj = self.env['kin.aviation.station']
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id', '=', user.id)])
        return aviation_station[0]

    @api.depends('pump_id')
    def _compute_meter_start(self):
        for rec in self:
            rec.loading_opening_meter = rec.pump_id.totalizer


    @api.multi
    def btn_view_aviation_record(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Aviation Record'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.aviation.record',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.aviation_record_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }

    @api.depends('aviation_record_id')
    def _compute_aviation_record_count(self):
        for rec in self:
            rec.aviation_record_count = len(rec.aviation_record_id)


    @api.depends('opening_dip','closing_dip')
    def _compute_dipping_difference(self):
        for rec in self :
            rec.dipping_difference = rec.closing_dip - rec.opening_dip

    @api.depends('dipping_difference','loading_difference')
    def _compute_stock_gain_loss_difference(self):
        for rec in self :
            rec.stock_gain_loss_difference = rec.dipping_difference - rec.loading_difference

    @api.depends('to_tank_storage_id')
    def _compute_opening_dip(self):
        for rec in self:
            rec.opening_dip = rec.to_tank_storage_id.stock_level


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


    name = fields.Char('Name')
    pump_id = fields.Many2one('kin.fuel.pump.aviation',string='Loading Pump')
    product_id = fields.Many2one('product.product', related='pump_id.product_id', string='Product')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    loading_operator_id = fields.Many2one('res.users',string='Loading Operator')
    loading_opening_meter = fields.Float(string='Loading Opening Meter',compute=_compute_meter_start,store=True)
    loading_closing_meter = fields.Float(string='Loading Closing Meter')
    loading_difference = fields.Float(string='Loading Difference',compute='_compute_difference',store=True)
    aviation_record_id = fields.Many2one('kin.aviation.record', string='Aviation Record')
    date_load = fields.Date(string='Date')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Done'), ('cancel', 'Cancel')], default='draft',track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True, ondelete='restrict')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station', default=_get_user_aviation_station, ondelete='restrict')
    aviation_record_count = fields.Integer(compute="_compute_aviation_record_count", string='# of Aviation Record',copy=False, default=0)

    from_tank_storage_id = fields.Many2one('kin.tank.storage.aviation', string='From Tank Storage', ondelete='restrict',
                                           track_visibility='onchange')
    to_tank_storage_id = fields.Many2one('kin.refueller.bowser', string='To Bowser / Refueller', ondelete='restrict',
                                         track_visibility='onchange')
    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False,
                                      default=0)
    stock_move_ids = fields.One2many('stock.move', 'loading_av_id', string='Stock Moves Entry(s)')

    #Dippings
    # opening_dip = fields.Float(string='Opening Dip',compute=_compute_opening_dip,store=True)
    # closing_dip = fields.Float(string='Closing Dip')
    # dipping_difference = fields.Float(string='Dipping Difference',store=True,compute=_compute_dipping_difference,help='Closing Dip - Opening Dip')
    # stock_gain_loss_difference = fields.Float(compute=_compute_stock_gain_loss_difference,store=True,string='Stock Gain/Loss Difference')

   #  # Quality Control Procedure
    is_appearance = fields.Boolean('Bright and Clear')
    temp = fields.Float('Observed Temperature')
    density = fields.Float('Density @‎ 15 degree (kg/m3)',
                           digits=dp.get_precision('Density and Conductivity'))  # (0.775-0.840)kg/m3
    conductivity = fields.Float('Conductivity (pS/m)',
                                digits=dp.get_precision('Density and Conductivity'))  # (50-600)pS/m
    qhsse_remark = fields.Text('QHSSE Remark')
    is_passed = fields.Boolean('Is Passed')



class TankRecord(models.Model):
    _name = 'kin.tank.record'
    _description = 'Tank Dippings'
    _inherit = ['mail.thread']

    @api.model
    def create(self, vals):
        res = super(TankRecord, self).create(vals)
        if res.tank_closing_dip < 0 :
            raise UserError(_('Tank closing dip cannot go negative'))
        # if res.tank_closing_dip > res.stock_at_hand:
        #     raise UserError(_('Tank closing dip cannot be greater than tank stock at hand'))

        return res

    @api.multi
    def write(self, vals):
        res = super(TankRecord, self).write(vals) #since the stock_at_hand field is readonly, it means the val field cannot get new changes for this field, thus the only option is to do write() first before accessing the field value. Accessing the value first before write() will give you the outdated field value, which is wrong for the calculation
        if self.tank_closing_dip < 0 :
            raise UserError(_('Tank closing dip cannot go negative'))
        # if self.tank_closing_dip > self.stock_at_hand:
        #     raise UserError(_('Tank closing dip cannot be greater than stock at hand'))

        return res
    #
    # @api.depends('tank_opening_dip', 'stock_at_hand')
    # def _check_stock_values(self):
    #     for rec in self:
    #         if rec.tank_closing_dip > rec.stock_at_hand:
    #             warning_mess = {
    #                 'title': _('Tank Closing Dip > Stock at hand !'),
    #                 'message': _('Tank closing dip cannot be greater than stock at hand')
    #             }
    #             return {'warning': warning_mess}


    @api.depends('tank_opening_dip', 'stock_received','current_int_transfer_in','current_int_transfer_out','tank_closing_dip')
    def _compute_measures(self):
        for rec in self:
            rec.stock_at_hand = rec.tank_opening_dip + rec.stock_received + rec.current_int_transfer_in - rec.current_int_transfer_out
            rec.tank_difference = rec.stock_at_hand - rec.tank_closing_dip


    name = fields.Char('Name')
    tank_id = fields.Many2one('kin.tank.storage.aviation',string='Tank')
    product_id = fields.Many2one('product.product', related='tank_id.product_id', string='Product')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit')
    tank_opening_dip = fields.Float(string='Tank Opening Dip')
    stock_received = fields.Float('Stock Received')
    current_int_transfer_in = fields.Float('Transfer IN')
    current_int_transfer_out = fields.Float('Transfer OUT')
    tank_closing_dip = fields.Float(string='Tank Closing Dip')
    stock_at_hand = fields.Float('Stock at Hand', compute='_compute_measures', help='Tank Opening Dip + Stock Received + Transfer IN - Transfer OUT')
    tank_difference = fields.Float(string='Tank Difference',compute='_compute_measures')
    aviation_record_id = fields.Many2one('kin.aviation.record', string='Aviation Record')


class FuelDeliveryReceipt(models.Model):
    _name = 'kin.fuel.delivery.receipt'
    _description = 'Fuel Delivery Receipt'
    _inherit = ['mail.thread']
    _order = 'id desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('dr_code_av') or 'New'
        res = super(FuelDeliveryReceipt, self).create(vals)
        self.env['test.obj'].check_status(res)
        self.env['test.obj'].check_records(res)
        return res


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft','cancel']:
                raise UserError(_('Sorry, Non-draft/Cancelled Record cannot be deleted'))
        return super(FuelDeliveryReceipt, self).unlink()

    @api.depends('volume_sold','product_price')
    def _compute_sub_total_price(self):
        for rec in self:
            rec.price_subtotal = rec.volume_sold * rec.product_price

    @api.depends('opening_meter', 'closing_meter')
    def _compute_measures(self):
        for rec in self:
            rec.volume_sold = rec.opening_meter - rec.closing_meter

    @api.onchange('product_id')
    def _get_price(self):
        for rec in self:
            rec.update({
                'product_price':rec.product_id.lst_price
            })

    @api.depends('opening_meter','closing_meter')
    def _compute_volume_sold(self):
        for rec in self:
            rec.volume_sold = rec.closing_meter - rec.opening_meter

    @api.onchange('density','conductivity','is_appearance')
    def check_parameters(self):
        aviation_station = self.aviation_station_id
        if self.is_appearance == False :
            self.is_passed = False
        elif self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
        elif self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
        else :
            self.is_passed = True

    def test_parameters(self):
        av  = self.env['kin.aviation.station'].search([('aviation_station_manager_id', '=', self.env.user.id)])
        if not av :
            raise UserError(_('You are not a Aviation Manager'))
        aviation_station = av[0]
        if self.is_appearance == False:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Appearance Check.'))

        if self.density < aviation_station.density_min or self.density > aviation_station.density_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Density Check'))

        if self.conductivity < aviation_station.conductivity_min or self.conductivity > aviation_station.conductivity_max:
            self.is_passed = False
            raise UserError(
                _('Quality Control Test Failed for Conductivity Check'))

        self.is_passed = True

    @api.multi
    def action_confirm(self):
        self.test_parameters()
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

        asi = self.aviation_station_id

        # Meter Check
        if self.closing_meter < self.opening_meter:
            raise UserError('Closing Meter Value cannot be lower than Opening Meter Value')

        if self.opening_meter != self.pump_id.totalizer:
            raise ValidationError(_('The Opening Meter is not equal to the Totalizer value. The Totalizer has been previously updated. Please delete this record and recreate a new one'))

        self.pump_id.totalizer = self.closing_meter

        # check the current qty
        if self.volume_sold > self.from_tank_storage_id.stock_level:
            raise UserError(_('Transfer Qty - %s is more than stock at hand - %s , for the tank storage - %s' % (
                self.volume_sold, self.from_tank_storage_id.stock_level, self.from_tank_storage_id.name)))

        # create the stock move
        stock_move_obj = self.env['stock.move']
        vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'date': self.receipt_date,
            'location_id': self.from_tank_storage_id.stock_location_tmpl_bowser_id.id,
            'location_dest_id': self.aviation_station_id.aviation_station_customer_location_id.id,
            'product_uom_qty': self.volume_sold,
            'origin': self.name
        }

        move_id = stock_move_obj.create(vals)
        move_id.action_confirm()
        move_id.force_assign()
        move_id.action_done()
        move_id.delivery_receipt_av_id = self.id

        self.from_tank_storage_id.stock_level -= self.volume_sold
        self.from_tank_storage_id.current_int_transfer_out += self.volume_sold

        self.state = 'confirm'


    @api.multi
    def action_cancel(self):
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)
        asi = self.aviation_station_id

         #reverse the totalizer value
        self.pump_id.totalizer = self.opening_meter

        # create the reverse stock move
        # Reverse Stock moves because the system cannot allow cancellation of done stock moves
        stock_move_obj = self.env['stock.move']
        for stock_move in self.stock_move_ids:
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
            stock_move.loading_av_id = False  # prevent creation duplicate stock moves incase of more reversals
            move_id = stock_move_obj.create(vals)
            move_id.action_confirm()
            move_id.force_assign()
            move_id.action_done()
            move_id.delivery_receipt_av_id = self.id

            self.from_tank_storage_id.stock_level += self.volume_sold
            self.from_tank_storage_id.current_int_transfer_out -= self.volume_sold
        self.state = 'cancel'

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    def _get_user_aviation_station(self):
        user = self.env.user
        aviation_station_obj = self.env['kin.aviation.station']
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id', '=', user.id)])
        return aviation_station[0]

    @api.depends('pump_id')
    def _compute_meter_start(self):
        for rec in self:
            rec.opening_meter = rec.pump_id.totalizer

    @api.multi
    def btn_view_aviation_record(self):
        context = dict(self.env.context or {})
        context['active_id'] = self.id
        return {
            'name': _('Aviation Record'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kin.aviation.record',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.aviation_record_id])],
            # 'context': context,
            # 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
            # 'res_id': self.env.context.get('cashbox_id'),
            'target': 'new'
        }


    @api.depends('aviation_record_id')
    def _compute_aviation_record_count(self):
        for rec in self:
            rec.aviation_record_count = len(rec.aviation_record_id)


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


    name = fields.Char('Name')
    receipt_date = fields.Date(string='Receipt Date',default=lambda self: datetime.today().strftime('%Y-%m-%d'))
    customer_id = fields.Many2one('res.partner',string='Customer')
    delivery_attendant_id = fields.Many2one('res.users', string='Delivery Attendant')
    product_id = fields.Many2one('product.product',  string='Product')
    product_uom = fields.Many2one('product.uom',  related='product_id.uom_id',string='Unit')
    product_price = fields.Float(string='Selling Price')
    pump_id = fields.Many2one('kin.fuel.pump.aviation', string='Bowser Pump')
    volume_sold = fields.Float(string='Volume Sold / Meter Diff.',compute='_compute_volume_sold')
    opening_meter = fields.Float(string='Opening Meter',compute=_compute_meter_start,store=True)
    closing_meter = fields.Float(string='Closing Meter')
    # sale_qty = fields.Float(string='Pump Sales Qty.')
    price_subtotal = fields.Monetary(string='Subtotal Price',compute='_compute_sub_total_price',
                                     help='Pump Sales Qty. * Selling price of Product')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    aviation_record_id = fields.Many2one('kin.aviation.record',string='Aviation Record')
    aviation_record_count = fields.Integer(compute="_compute_aviation_record_count", string='# of Aviation Record', copy=False,default=0)

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Done'), ('cancel', 'Cancel')], default='draft',track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True,ondelete='restrict')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station', default=_get_user_aviation_station, ondelete='restrict')

    from_tank_storage_id = fields.Many2one('kin.refueller.bowser', string='From Bowser', ondelete='restrict',
                                           track_visibility='onchange')

    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False,
                                      default=0)
    stock_move_ids = fields.One2many('stock.move', 'delivery_receipt_av_id', string='Stock Moves Entry(s)')

    #  # Quality Control Procedure
    is_appearance = fields.Boolean('Bright and Clear')
    temp = fields.Float('Observed Temperature')
    density = fields.Float('Density @‎ 15 degree (kg/m3)',digits=dp.get_precision('Density and Conductivity'))  # (0.775-0.840)kg/m3
    conductivity = fields.Float('Conductivity (pS/m)',digits=dp.get_precision('Density and Conductivity'))  # (50-600)pS/m
    qhsse_remark = fields.Text('QHSSE Remark')
    is_passed = fields.Boolean('Is Passed')


class AviationRecord(models.Model):
    _name = 'kin.aviation.record'
    _description = 'Aviation Record'
    _inherit = ['mail.thread']
    _order = 'id desc'

    @api.depends('tank_record_ids.tank_difference', 'loading_record_ids.loading_difference', 'refueller_loading_record_ids.refueller_difference',
                 'fuel_delivery_receipt_ids.volume_sold')
    def _amount_all(self):
        for rec in self:
            total_tank_diff = total_meter_diff =  total_bowser_diff = total_receipt_diff = 0

            for tr in rec.tank_record_ids:
                total_tank_diff += tr.tank_difference
            for lr in rec.loading_record_ids:
                total_meter_diff += lr.loading_difference
            for rr in self.refueller_loading_record_ids:
                total_bowser_diff += rr.refueller_difference
            for rp in self.fuel_delivery_receipt_ids:
                total_receipt_diff += rp.volume_sold

            self.total_tank_diff = total_tank_diff
            rec.update({
                'total_meter_diff': total_meter_diff,
                'total_bowser_diff':total_bowser_diff,
                'total_receipt_diff':total_receipt_diff
            })

    @api.multi
    def button_dummy(self):
        return True


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('av_rec_code') or 'New'
        res = super(AviationRecord, self).create(vals)

        self.env['test.obj'].check_status(res)
        self.env['test.obj'].check_records(res)

        # loading Records
        kin_loading_record_obj = self.env['kin.loading.record']
        loading_records = kin_loading_record_obj.search(
            [('aviation_station_id', "=", res.aviation_station_id.id), ('date_load', '=', res.aviation_record_date)])
        loading_records.write({'aviation_record_id': res.id})

        # fuel Delivery Receipts
        kin_fuel_delivery_receipt_obj = self.env['kin.fuel.delivery.receipt']
        receipt_records = kin_fuel_delivery_receipt_obj.search(
            [('aviation_station_id', "=", res.aviation_station_id.id),
             ('receipt_date', '=', res.aviation_record_date)])
        receipt_records.write({'aviation_record_id': res.id})

        return res

    @api.multi
    def write(self,vals):
        res = super(AviationRecord,self).write(vals)

        # loading Records
        self.loading_record_ids.write({'aviation_record_id': False})
        kin_loading_record_obj = self.env['kin.loading.record']
        loading_records = kin_loading_record_obj.search(
            [('aviation_station_id', "=", self.aviation_station_id.id), ('date_load', '=', self.aviation_record_date)])
        loading_records.write({'aviation_record_id': self.id})

        # #fuel Delivery Receipts
        self.fuel_delivery_receipt_ids.write({'aviation_record_id': False})
        kin_fuel_delivery_receipt_obj = self.env['kin.fuel.delivery.receipt']
        receipt_records = kin_fuel_delivery_receipt_obj.search(
            [('aviation_station_id', "=", self.aviation_station_id.id),
             ('receipt_date', '=', self.aviation_record_date)])
        receipt_records.write({'aviation_record_id': self.id})

        return res




    @api.onchange('aviation_station_id','aviation_record_date')
    def populate_lines(self):
        if self.aviation_station_id and self.aviation_record_date:

            # populate tank lines
            tank_storage_obj = self.env['kin.tank.storage.aviation']
            # self.tank_record_ids.unlink()
            tanks = tank_storage_obj.search([('aviation_station_id', "=", self.aviation_station_id.id)])

            line_tanks = []
            for tank in tanks:
                line_tanks += [(0, 0, {
                    'tank_id': tank.id,
                    'product_id':tank.product_id.id,
                    'tank_opening_dip': tank.stock_level,
                    'stock_received' : tank.current_stock_received,
                    'current_int_transfer_in': tank.current_int_transfer_in,
                    'current_int_transfer_out': tank.current_int_transfer_out
                })
                               ]
            self.tank_record_ids = line_tanks

            #populate Bowser
            bowser_obj = self.env['kin.refueller.bowser']
            bowsers = bowser_obj.search([('aviation_station_id', "=", self.aviation_station_id.id)])

            bowser_tanks = []
            for bowser in bowsers:
                bowser_tanks += [(0, 0, {
                    'refueller_id': bowser.id,
                    'product_id':bowser.product_id.id,
                    'refueller_opening_dip': bowser.stock_level,
                    'stock_received': bowser.current_stock_received,
                    'current_int_transfer_in': bowser.current_int_transfer_in,
                    'current_int_transfer_out': bowser.current_int_transfer_out
                })
                               ]
            self.refueller_loading_record_ids = bowser_tanks


    @api.multi
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        orders.write({
            'state': 'draft'
        })

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft','cancel']:
                raise UserError(_('Sorry, Non-draft/Cancelled Aviation Record cannot be deleted'))

        return super(AviationRecord, self).unlink()

    @api.multi
    def action_cancel(self):
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)
        self.write({'state': 'cancel'})


    @api.multi
    def action_cancel_approver(self):
        self.action_cancel()

        #reverse loading meter
        for load_meter in self.loading_record_ids :
            load_meter.pump_id.totalizer = load_meter.loading_opening_meter

        #reverse the stock level
        for td in self.tank_record_ids :
            td.tank_id.current_int_transfer_in = td.current_int_transfer_in
            td.tank_id.current_int_transfer_out = td.current_int_transfer_out
            td.tank_id.current_stock_received = td.stock_received
            td.tank_id.stock_level = td.tank_opening_dip + td.stock_received + td.current_int_transfer_in - td.current_int_transfer_out
            td.tank_id.current_closing_stock = td.tank_closing_dip

        #reverse for bowser
        for rf in self.refueller_loading_record_ids:
            rf.refueller_id.current_int_transfer_in = rf.current_int_transfer_in
            rf.refueller_id.current_int_transfer_out = rf.current_int_transfer_out
            rf.refueller_id.current_stock_received = rf.stock_received
            rf.refueller_id.stock_level = rf.refueller_opening_dip + rf.stock_received + rf.current_int_transfer_in - rf.current_int_transfer_out
            rf.refueller_id.current_closing_stock = rf.refueller_closing_dip


        #Reverse Stock moves because the system cannot allow cancellation of done stock moves
        for stock_move in  self.stock_move_ids:
            # create the reverse stock move
            stock_move_obj = self.env['stock.move']

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
            stock_move.stock_control_av_id = False
            move_id = stock_move_obj.create(vals)
            move_id.action_confirm()
            move_id.force_assign()
            move_id.action_done()


    def action_approved(self):

        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

        # Update totalizer
        for load_meter in self.loading_record_ids :
            load_meter.pump_id.totalizer = load_meter.loading_closing_meter


        stock_move_obj = self.env['stock.move']
        # update the Stock Level for the tanks
        for td in self.tank_record_ids:
            td.tank_id.current_stock_received = 0
            td.tank_id.current_int_transfer_in = 0
            td.tank_id.current_int_transfer_out = 0
            td.tank_id.stock_level = td.tank_closing_dip
            td.tank_id.current_closing_stock = td.tank_closing_dip

            # create the stock move
            tank_location_id = td.tank_id.stock_location_tmpl_aviation_id

            tank_difference_location_id = td.tank_id.aviation_station_id.tank_difference_location_id or False
            if not tank_difference_location_id:
                raise UserError(_('Please Contact the Admin to Tank Difference Location for the Aviation Station'))

            vals = {
                'name': td.tank_id.name,
                'product_id': td.product_id.id,
                'product_uom': td.product_id.uom_id.id,
                'date': self.aviation_record_date,
                'location_id': tank_location_id.id,
                'location_dest_id': tank_difference_location_id.id,
                'product_uom_qty': abs(td.tank_difference),
                'origin': self.name
            }

            if td.tank_difference > 0 :
                vals.update({
                    'location_id': tank_location_id.id,
                    'location_dest_id': tank_difference_location_id.id
                })
                move_id = stock_move_obj.create(vals)
                move_id.action_confirm()
                move_id.force_assign()
                move_id.action_done()
                move_id.stock_control_av_id = self.id
            elif td.tank_difference < 0:
                vals.update({
                    'location_id': tank_difference_location_id.id,
                    'location_dest_id': tank_location_id.id
                })
                move_id = stock_move_obj.create(vals)
                move_id.action_confirm()
                move_id.force_assign()
                move_id.action_done()
                move_id.stock_control_av_id = self.id


        for rf in self.refueller_loading_record_ids:
            rf.refueller_id.current_int_transfer_in = 0
            rf.refueller_id.current_int_transfer_out = 0
            rf.refueller_id.current_stock_received = 0
            rf.refueller_id.stock_level = rf.refueller_closing_dip
            rf.refueller_id.current_closing_stock = rf.refueller_closing_dip

            # create the stock move
            bowser_location_id = rf.refueller_id.stock_location_tmpl_bowser_id

            bowser_difference_location_id = td.tank_id.aviation_station_id.bowser_difference_location_id or False
            if not bowser_difference_location_id:
                raise UserError(_('Please Contact the Admin to Set the Bowser Difference for the Aviation Station'))

            if rf.refueller_difference > 0:
                vals = {
                    'name': td.tank_id.name,
                    'product_id': rf.product_id.id,
                    'product_uom': rf.product_id.uom_id.id,
                    'date': self.aviation_record_date,
                    'location_id': bowser_location_id.id,
                    'location_dest_id': bowser_difference_location_id.id,
                    'product_uom_qty': rf.refueller_difference,
                    'origin': self.name
                }

                move_id = stock_move_obj.create(vals)
                move_id.action_confirm()
                move_id.force_assign()
                move_id.action_done()
                move_id.stock_control_av_id = self.id

        return self.write({'state': 'approve'})


    @api.multi
    def action_approve(self):
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)
        self.action_approved()
        self.state = 'approve'

    @api.multi
    def action_confirm(self):
        self.env['test.obj'].check_status(self)
        self.env['test.obj'].check_records(self)

        #check if the tank dipping
        for td in self.tank_record_ids:
            if td.tank_closing_dip <= 0 and td.stock_at_hand :
                raise UserError('Please consider the dead stock for the tank - %s. Kindly set a positive closing dip' % (td.tank_id.name))

        #check the bowser dippings
        for bd in self.refueller_loading_record_ids:
            if bd.refueller_closing_dip <= 0 and bd.stock_at_hand:
                raise UserError('Please consider the dead stock for the bowser - %s. Kindly set a positive closing dip' % (bd.refueller_id.name))

        user_ids = []
        group_obj = self.env.ref('kin_aviation.group_aviation_station_management')
        for user in group_obj.users:
            user_ids.append(user.id)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_('Aviation Records from %s have been Created with ID %s.') % (
            self.env.user.name, self.name),
                          subject='An Aviation Records have been Created ', subtype='mail.mt_comment')

        self.state = 'confirm'

    @api.multi
    def action_disapprove(self, msg):
        user_ids = []
        aviation_station_manager = self.aviation_station_id.aviation_station_manager_id
        if aviation_station_manager:
            user_ids.append(aviation_station_manager.id)
            self.message_unsubscribe_users(user_ids=user_ids)
            self.message_subscribe_users(user_ids=user_ids)
            user = self.env.user
            self.message_post(_(
                'The Aviation Record (%s) has been DisApproved by %s. Reason for Disapproval: %s. You may correct and Re-Submit again for approval ') % (
                                  self.name, user.name, msg),
                              subject='The Aviation Record (%s) has been Dis-Approved by %s' % (self.name, user.name),
                              subtype='mail.mt_comment')


        return self.write({'state': 'draft', 'disapprove_id': user.id,
                           'disapprove_date': datetime.today(), 'reason_disapprove': msg})


    def _get_user_aviation_station(self):
        user = self.env.user
        aviation_station_obj = self.env['kin.aviation.station']
        aviation_station = aviation_station_obj.search([('aviation_station_manager_id','=',user.id)])
        return aviation_station[0].id


    @api.depends('aviation_station_id')
    def _compute_aviation_station_manager(self):
        self.aviation_station_manager_id = self.aviation_station_id.aviation_station_manager_id

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

    name = fields.Char(string='ID')
    aviation_record_date = fields.Date(string='Date')
    aviation_station_id = fields.Many2one('kin.aviation.station', string='Aviation Station',default=_get_user_aviation_station)
    aviation_station_manager_id = fields.Many2one('res.users', compute='_compute_aviation_station_manager',
                                                  string='Aviation Station Manager', store=True)

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, ondelete='restrict')
    fuel_delivery_receipt_ids = fields.One2many('kin.fuel.delivery.receipt','aviation_record_id',string='Fuel Delivery Receipts')
    tank_record_ids = fields.One2many('kin.tank.record','aviation_record_id',string='Tank Records')
    loading_record_ids = fields.One2many('kin.loading.record','aviation_record_id',string='Loading Records')
    refueller_loading_record_ids = fields.One2many('kin.refueller.loading.record','aviation_record_id',string='Refueller Loading Records')
    reason_disapprove = fields.Text(string='Reason for Dis-Approval')
    disapprove_id = fields.Many2one('res.users',string='Disapproved By')
    disapprove_date = fields.Datetime(string='Disapproved Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    total_tank_diff = fields.Float(string='Total Tank Difference',compute='_amount_all')
    total_meter_diff = fields.Float(string='Total Meter Difference',compute='_amount_all')
    total_bowser_diff = fields.Float(string='Total Bowser Difference',compute='_amount_all')
    total_receipt_diff = fields.Float(string='Total Receipt Difference',compute='_amount_all')

    stock_move_count = fields.Integer(compute="_compute_stock_move_count", string='# of Stock Moves', copy=False, default=0)
    stock_move_ids = fields.One2many('stock.move', 'stock_control_av_id', string='Stock Moves')


class testobj(models.Model):
    _name = 'test.obj'

    def check_status(self,obj):
        if obj._name == 'product.received.register.aviation':
            aviation_station_id = obj.to_stock_location_id
        else:
            aviation_station_id = obj.aviation_station_id
        #check PRR status
        prr_pending = self.env['product.received.register.aviation'].search([('to_stock_location_id', '=', aviation_station_id.id), ('state', 'in', ['draft', 'transit', 'cancel'])])
        if prr_pending._name == obj._name:
            prr_pending = prr_pending - obj
        if len(prr_pending) > 0:  # since this is the only record
            raise UserError(_(
                "Sorry, There is a product received record with ID - %s for %s with date on %s, that still need to be validated or deleted" % (
                    prr_pending[0].name, prr_pending[0].to_stock_location_id.name,
                    datetime.strptime(prr_pending[0].receiving_date, "%Y-%m-%d").strftime("%d-%m-%Y"))))

        #check tank to tank transfer
        ttr_pending = self.env['kin.internal.movement.aviation'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('state', 'in', ['draft', 'cancel'])])
        if ttr_pending._name == obj._name:
            ttr_pending = ttr_pending - obj
        if len(ttr_pending) > 0:  # since this is the only record
            raise UserError(_(
                "Sorry, There is a tank to tank transfer record with ID - %s for %s with date on %s, that still need to be validated or deleted" % (
                    ttr_pending[0].name, ttr_pending[0].aviation_station_id.name,
                    datetime.strptime(ttr_pending[0].date_move, "%Y-%m-%d").strftime("%d-%m-%Y"))))


        # check tank to Bowser transfer
        tbr_pending = self.env['kin.bowser.movement.aviation'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('state', 'in', ['draft', 'cancel'])])
        if tbr_pending._name == obj._name:
            tbr_pending = tbr_pending - obj
        if len(tbr_pending) > 0:  # since this is the only record
            raise UserError(_(
                "Sorry, There is a tank to bowser transfer record with ID - %s for %s with date on %s, that still need to be validated or deleted" % (
                    tbr_pending[0].name, tbr_pending[0].aviation_station_id.name,
                    datetime.strptime(tbr_pending[0].date_move, "%Y-%m-%d").strftime("%d-%m-%Y"))))

        # check Bowser to tank transfer
        btr_pending = self.env['kin.bowser.movement.tank.aviation'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('state', 'in', ['draft', 'cancel'])])
        if btr_pending._name == obj._name:
            btr_pending = btr_pending - obj
        if len(btr_pending) > 0:  # since this is the only record
            raise UserError(_(
                "Sorry, There is a bowser to tank transfer record with ID - %s for %s with date on %s, that still need to be validated or deleted" % (
                    btr_pending[0].name, btr_pending[0].aviation_station_id.name,
                    datetime.strptime(btr_pending[0].date_move, "%Y-%m-%d").strftime("%d-%m-%Y"))))

        # check Bowser to Bowser transfer
        bbr_pending = self.env['kin.bowser.movement.bowser.aviation'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('state', 'in', ['draft', 'cancel'])])
        if bbr_pending._name == obj._name:
            bbr_pending = bbr_pending - obj
        if len(bbr_pending) > 0:  # since this is the only record
            raise UserError(_(
                "Sorry, There is a bowser to bowser transfer record with ID - %s for %s with date on %s, that still need to be validated or deleted" % (
                    bbr_pending[0].name, bbr_pending[0].aviation_station_id.name,
                    datetime.strptime(bbr_pending[0].date_move, "%Y-%m-%d").strftime("%d-%m-%Y"))))

        # check loading meter record
        lrr_pending = self.env['kin.loading.record'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('state', 'in', ['draft', 'cancel'])])
        if lrr_pending._name == obj._name :
            lrr_pending = lrr_pending - obj
        if len(lrr_pending) > 0:  # since this is the only record
            raise UserError(_(
                "Sorry, There is a loading meter record with ID - %s for %s with date on %s, that still need to be validated or deleted" % (
                    lrr_pending[0].name, lrr_pending[0].aviation_station_id.name,
                    datetime.strptime(lrr_pending[0].date_load, "%Y-%m-%d").strftime("%d-%m-%Y"))))

        # check delivery receipt record
        fdr_pending = self.env['kin.fuel.delivery.receipt'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('state', 'in', ['draft', 'cancel'])])
        if fdr_pending._name == obj._name :
            fdr_pending = fdr_pending - obj
        if len(fdr_pending) > 0:  # since this is the only record
            raise UserError(_(
                "Sorry, There is a delivery receipt record with ID - %s for %s with date on %s, that still need to be validated or deleted" % (
                    fdr_pending[0].name, fdr_pending[0].aviation_station_id.name,
                    datetime.strptime(fdr_pending[0].receipt_date, "%Y-%m-%d").strftime("%d-%m-%Y"))))

        # check aviation record
        avr_pending = self.env['kin.aviation.record'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('state', 'in', ['draft', 'confirm', 'cancel'])])
        if avr_pending._name == obj._name :
            avr_pending = avr_pending - obj
        if len(avr_pending) > 0:  # since this is the only record
            raise UserError(_(
                "Sorry, There is a aviation operation record with ID - %s for %s with date on %s, that still need to be validated or deleted" % (
                    avr_pending[0].name, avr_pending[0].aviation_station_id.name,
                    datetime.strptime(avr_pending[0].aviation_record_date, "%Y-%m-%d").strftime("%d-%m-%Y"))))

    def check_records(self,obj):
        #check later PRR
        if obj._name == 'product.received.register.aviation':
            aviation_station_id = obj.to_stock_location_id
        else:
            aviation_station_id = obj.aviation_station_id
        later_date = str(datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1))
        prr_later = obj.env['product.received.register.aviation'].search(
            [('to_stock_location_id', '=', aviation_station_id.id), ('create_date', '>', later_date)])
        for prr in prr_later:
            if not prr.is_company_product:
                later_date_str = str(
                    (datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime(
                        "%d-%m-%Y  %H:%M:%S"))
                prr_name = prr.name
                aviation_station_name = aviation_station_id.name
                raise UserError(_(
                    'Sorry, the product received record with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (
                                prr_name, later_date_str, aviation_station_name))


        #check tank to tank transfer
        ttr_later = obj.env['kin.internal.movement.aviation'].search([('aviation_station_id', '=', aviation_station_id.id), ('create_date', '>', later_date)])
        for ttr in ttr_later:
            later_date_str = str((datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime("%d-%m-%Y  %H:%M:%S"))
            ttr_name = ttr.name
            aviation_station_name = aviation_station_id.name
            raise UserError(_(
                    'Sorry, the Tank to Tank transfer record with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (
                                ttr_name, later_date_str, aviation_station_name))

        #check Tank to Bowser transfer
        tbr_later = obj.env['kin.bowser.movement.aviation'].search([('aviation_station_id', '=', aviation_station_id.id), ('create_date', '>', later_date)])
        for tbr in tbr_later:
            later_date_str = str((datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime("%d-%m-%Y  %H:%M:%S"))
            tbr_name = tbr.name
            aviation_station_name = aviation_station_id.name
            raise UserError(_(
                    'Sorry, the Tank to Bowser transfer record with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (
                                tbr_name, later_date_str, aviation_station_name))


        #check Bowser to Tank
        btr_later = obj.env['kin.bowser.movement.tank.aviation'].search([('aviation_station_id', '=', aviation_station_id.id), ('create_date', '>', later_date)])
        for btr in btr_later:
            later_date_str = str((datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime("%d-%m-%Y  %H:%M:%S"))
            btr_name = btr.name
            aviation_station_name = aviation_station_id.name
            raise UserError(_(
                    'Sorry, the Bowser to Tank transfer record with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (
                                btr_name, later_date_str, aviation_station_name))

        #check bowser to bowser
        btb_later = obj.env['kin.bowser.movement.bowser.aviation'].search([('aviation_station_id', '=', aviation_station_id.id), ('create_date', '>', later_date)])
        for btb in btb_later:
            later_date_str = str((datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime("%d-%m-%Y  %H:%M:%S"))
            btb_name = btb.name
            aviation_station_name = aviation_station_id.name
            raise UserError(_(
                    'Sorry, the Bowser to Bowser transfer record with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (
                                btb_name, later_date_str, aviation_station_name))

        #Check loading record
        lrr_later = obj.env['kin.loading.record'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('create_date', '>', later_date)])
        for lrr in lrr_later:
            later_date_str = str((datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime("%d-%m-%Y  %H:%M:%S"))
            lrr_name = lrr.name
            aviation_station_name = aviation_station_id.name
            raise UserError(_(
                    'Sorry, the loading meter record with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (
                                lrr_name, later_date_str, aviation_station_name))


        #check Fuel Delivery receipt
        fdr_later = obj.env['kin.fuel.delivery.receipt'].search([('aviation_station_id', '=', aviation_station_id.id), ('create_date', '>', later_date)])
        for fdr in fdr_later:
            later_date_str = str((datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime("%d-%m-%Y  %H:%M:%S"))
            fdr_name = fdr.name
            aviation_station_name = aviation_station_id.name
            raise UserError(_(
                'Sorry, the fuel delivery receipt with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (
                                fdr_name, later_date_str, aviation_station_name))

        #check aviation record
        avr_later = obj.env['kin.aviation.record'].search(
            [('aviation_station_id', '=', aviation_station_id.id), ('create_date', '>', later_date)])
        for avr in avr_later:
            later_date_str = str(
                (datetime.strptime(obj.create_date, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=1)).strftime(
                    "%d-%m-%Y  %H:%M:%S"))
            avr_name = avr.name
            aviation_station_name = aviation_station_id.name
            raise UserError(_(
                'Sorry, the aviation record with ID %s, created on or after %s, for the aviation station (%s), must be cancelled and deleted, to update the stock qty.') % (
                                avr_name, later_date_str, aviation_station_name))
