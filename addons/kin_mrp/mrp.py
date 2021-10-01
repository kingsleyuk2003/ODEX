# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from datetime import datetime, timedelta


class StockProductionQuant(models.Model):
    _inherit = "stock.quant"

    def _create_account_move_line(self, cr, uid, quants, move, credit_account_id, debit_account_id, journal_id,
                                  context=None):
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

            model_name = context.get('active_model', False)
            manu_id = False
            if model_name == u'mrp.production':
                manu_id = context.get('active_id', False)

            new_move = move_obj.create(cr, uid, {'journal_id': journal_id,
                                                 'line_ids': move_lines,
                                                 'date': date,
                                                 'ref': move.picking_id.name,
                                                 'picking_id': move.picking_id.id,
                                                 'manu_id': manu_id
                                                 }, context=context)
            move_obj.post(cr, uid, [new_move], context=context)


class AccountMoveStockManuExtend(models.Model):
    _name = 'account.move'
    _inherit = ['account.move','mail.thread']


    picking_id = fields.Many2one('stock.picking', string="Inventory Transfer", track_visibility='onchange',
                                 readonly=True)
    manu_id = fields.Many2one('mrp.production', string="Manufacturing Order", track_visibility='onchange',
                                 readonly=True)


class AccountMoveLineManuExtend(models.Model):
    _inherit = 'account.move.line'

    manu_id = fields.Many2one(related='move_id.manu_id', string="Manufacturing Production", store=True)


class MrpBomLineExtend(models.Model):
    _inherit = 'mrp.bom.line'

    product_cost = fields.Float(related='product_id.standard_price',string='Unit Cost Price')



class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    _order = 'sequence, id'

    @api.multi
    def action_confirm(self):
        # check if it is a template
        if self.batch_id and self.batch_id.is_template :
            raise  UserError(_('You cannot confirm a manufacturing order for a manufacturing batch template'))
        return  super(MrpProduction,self).action_confirm()


    @api.multi
    def action_cancel(self):
        # check if it is a template
        if self.batch_id and self.batch_id.is_template:
            raise UserError(_('You cannot cancel a manufacturing order for a manufacturing batch template'))
        return super(MrpProduction, self).action_cancel()


    @api.multi
    def btn_view_moves(self):
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
            # 'target': 'new'
        }


    @api.depends('move_ids')
    def _compute_moves_count(self):
        for rec in self:
            rec.move_count = len(rec.move_ids)

    @api.multi
    def write(self, vals, update=True, mini=True):
        res = super(MrpProduction, self).write(vals,update=update, mini=mini)
        if self.batch_id and all([l.state  == 'done' for l in self.batch_id.manufacturing_ids]):
            self.batch_id.state = 'done'
        elif self.batch_id and any([l.state  == 'cancel' for l in self.batch_id.manufacturing_ids]):
            self.batch_id.state = 'cancel'
        elif self.batch_id and any([l.state  in ('confirmed','ready','in_production') for l in self.batch_id.manufacturing_ids]):
            self.batch_id.state = 'progress'
        elif self.batch_id and all([l.state  == 'draft' for l in self.batch_id.manufacturing_ids]):
            self.batch_id.state = 'draft'
        return res

    batch_id = fields.Many2one('mrp.production.batch',string='Production Batch',ondelete='cascade')
    sequence = fields.Integer(string='Sequence')
    move_ids = fields.One2many('account.move','manu_id',string='Journal Entry')
    move_count = fields.Integer(compute="_compute_moves_count", string='# Account Moves Count', copy=False, default=0)


class MrpBatch(models.Model):
    _name = 'mrp.production.batch'
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    @api.multi
    def unlink(self):
        if any([l.state not in ('draft') for l in self.manufacturing_ids]):
            raise UserError(_('Cannot delete this Batch due to an existing draft manufacturing order'))
        else:
            res = super(MrpBatch, self).unlink()
        return


    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        res = super(MrpBatch, self).copy(default)
        res.name = res.name + '_new_copy'
        for mo in self.manufacturing_ids :
            mo_copy = mo.copy(default)
            mo_copy.batch_id = res
        res.state = 'draft'
        return res

    name = fields.Char('Name')
    date_start = fields.Date(string='Start Date', select=True, readonly=True, copy=False)
    date_finished = fields.Date(string='End Date', select=True, readonly=True, copy=False)
    date_planned = fields.Date(string='Scheduled Date',copy=False)
    product_id = fields.Many2one('product.product', 'Product', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  domain=[('type', 'in', ['product', 'consu'])])
    product_qty = fields.Float('Product Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                                required=True, readonly=True, states={'draft': [('readonly', False)]})
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]})
    origin = fields.Char(string='Reference')
    manufacturing_ids = fields.One2many('mrp.production','batch_id', string='Manufacturing Orders')
    is_template = fields.Boolean('Is template',copy=False)
    state = fields.Selection([
        ('draft', 'New'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel','Cancelled')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')