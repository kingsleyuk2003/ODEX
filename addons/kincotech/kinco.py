# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import api, fields, models, _
import time
from openerp.osv import  fields

class res_currency_rate(models.Model):

    _inherit = "res.currency.rate"

    _columns = {
        'rate': fields.float('Rate', digits=(12, 20), help='The rate of the currency to the currency of rate 1'),
        }
    

# see the journal entry  BILL/2015/0017 on KCT database for example
# An explanation of why the second line has N2309.01 intstead of N2309.00 . It is because of basic calculation round-off error. customization was done on it, otherwise the system will prompt you to setup the exchange difference journal so that it can post the 0.01 difference. Which is not what should be.
#
# see line of code to debug: ../odoo-9.0/openerp/addons/base/res/res_currency.py:232
# customized module : ../odoo-9.0/addons/custom/mine/kincotech/kinco.py:43  we can't help it. another alternative is to configure the exchange rate journal (but this will allow differences to be posted against your will. it is better the system stops/prompts you for posting that, because it is still thesame exact exchange rate that is used. so why post exchange rate difference)
# see demonstration of the problem section in wikipedia. https://en.wikipedia.org/wiki/Loss_of_significance
# see: http://effbot.org/pyfaq/why-are-floating-point-calculations-so-inaccurate.htm
# see: http://stackoverflow.com/questions/15930381/python-round-off-error
#
# ================================
# Invoicing part:
# from_amount = 140
# currency_rate = 212.419984047  i.e. 140×212.419984047
# to_amount = 29738.79776658
# returns = 29738.80
#
# from_amount = 10.87
# currency_rate = 212.419984047
# to_amount = 2309.00522659 i.e. 10.87×212.419984047
# returns = 2309.01
# =========================================
#
# ++++++++++++++++++++++++++++++++++++++++++++++
# Payment Part for the whole $150.87:
# currency_rate = 212.419984047
# to_amount = 32047.8029932
# returns  = 32047.8
# ++++++++++++++++++++++++++++++++++++++++++++++++
#
# Conclusion:
# the total from Invoice  = 29738.79776658+2309.00522659 = 32047.80299317
# the total rounded invoice = 29738.80+2309.01 = 32047.81
#
# thus 32047.81 != 32047.80  , so the system prompt a box for exchange difference journal, because of the .01
#

class ResCurrency(models.Model):

    _inherit = "res.currency"

    @api.v7
    def compute(self, cr, uid, from_currency_id, to_currency_id, from_amount,round=True, context=None):
        round = False
        return super(ResCurrency,self).compute( cr, uid, from_currency_id, to_currency_id, from_amount, round, context=context)

    @api.v8
    def compute(self, from_amount, to_currency, round=True):
        round = False
        return super(ResCurrency,self).compute( from_amount, to_currency, round)



# class account_move_line(osv.Model):
#
#     _inherit = "account.move.line"
#
#     #ref: ../addons/account/account_move_line.py line 616
#     # See someone (MONDIN) who tried it also at: https://www.odoo.com/forum/help-1/question/error-occurred-while-validating-the-field-s-currency-id-the-selected-account-of-your-journal-entry-forces-to-provide-a-seconda-31026
#     def _check_currency(self, cr, uid, ids, context=None):
#         for l in self.browse(cr, uid, ids, context=context):
#             if l.account_id.currency_id:
#                 if not l.currency_id or not l.currency_id.id == l.account_id.currency_id.id:
#                     return True   # This is Changed to True, to allow reconciling my bank statement to work with the Intermiediary account with a different currency but converted to the companie's currrency
#         return True
#
#     _constraints = [
#         (_check_currency, 'The selected account of your Journal Entry forces to provide a secondary currency. You should remove the secondary currency on the account or select a multi-currency view on the journal.', ['currency_id']),
#          ]
#

# class account_move(osv.Model):
#     _inherit = 'account.move'
#
#     def validate(self, cr, uid, ids, context=None):
#         if context and ('__last_update' in context):
#             del context['__last_update']
#
#         valid_moves = [] #Maintains a list of moves which can be responsible to create analytic entries
#         obj_analytic_line = self.pool.get('account.analytic.line')
#         obj_move_line = self.pool.get('account.move.line')
#         for move in self.browse(cr, uid, ids, context):
#             journal = move.journal_id
#             amount = 0
#             line_ids = []
#             line_draft_ids = []
#             company_id = None
#             for line in move.line_id:
#                 amount += line.debit - line.credit
#                 line_ids.append(line.id)
#                 if line.state=='draft':
#                     line_draft_ids.append(line.id)
#
#                 if not company_id:
#                     company_id = line.account_id.company_id.id
#                 if not company_id == line.account_id.company_id.id:
#                     raise osv.except_osv(_('Error!'), _("Cannot create moves for different companies."))
#
# #                 if line.account_id.currency_id and line.currency_id:
# #                     if line.account_id.currency_id.id != line.currency_id.id and (line.account_id.currency_id.id != line.account_id.company_id.currency_id.id):
# #                         raise osv.except_osv(_('Error!'), _("""Cannot create move with currency different from ..""") % (line.account_id.code, line.account_id.name))
#
#             if abs(amount) < 10 ** -4:
#                 # If the move is balanced
#                 # Add to the list of valid moves
#                 # (analytic lines will be created later for valid moves)
#                 valid_moves.append(move)
#
#                 # Check whether the move lines are confirmed
#
#                 if not line_draft_ids:
#                     continue
#                 # Update the move lines (set them as valid)
#
#                 obj_move_line.write(cr, uid, line_draft_ids, {
#                     'state': 'valid'
#                 }, context, check=False)
#
#                 account = {}
#                 account2 = {}
#
#                 if journal.type in ('purchase','sale'):
#                     for line in move.line_id:
#                         code = amount = 0
#                         key = (line.account_id.id, line.tax_code_id.id)
#                         if key in account2:
#                             code = account2[key][0]
#                             amount = account2[key][1] * (line.debit + line.credit)
#                         elif line.account_id.id in account:
#                             code = account[line.account_id.id][0]
#                             amount = account[line.account_id.id][1] * (line.debit + line.credit)
#                         if (code or amount) and not (line.tax_code_id or line.tax_amount):
#                             obj_move_line.write(cr, uid, [line.id], {
#                                 'tax_code_id': code,
#                                 'tax_amount': amount
#                             }, context, check=False)
#             elif journal.centralisation:
#                 # If the move is not balanced, it must be centralised...
#
#                 # Add to the list of valid moves
#                 # (analytic lines will be created later for valid moves)
#                 valid_moves.append(move)
#
#                 #
#                 # Update the move lines (set them as valid)
#                 #
#                 self._centralise(cr, uid, move, 'debit', context=context)
#                 self._centralise(cr, uid, move, 'credit', context=context)
#                 obj_move_line.write(cr, uid, line_draft_ids, {
#                     'state': 'valid'
#                 }, context, check=False)
#             else:
#                 # We can't validate it (it's unbalanced)
#                 # Setting the lines as draft
#                 not_draft_line_ids = list(set(line_ids) - set(line_draft_ids))
#                 if not_draft_line_ids:
#                     obj_move_line.write(cr, uid, not_draft_line_ids, {
#                         'state': 'draft'
#                     }, context, check=False)
#         # Create analytic lines for the valid moves
#         for record in valid_moves:
#             obj_move_line.create_analytic_lines(cr, uid, [line.id for line in record.line_id], context)
#
#         valid_moves = [move.id for move in valid_moves]
#         return len(valid_moves) > 0 and valid_moves or False