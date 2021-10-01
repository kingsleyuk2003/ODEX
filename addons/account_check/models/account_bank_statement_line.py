# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, api, _
from openerp.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.multi
    def button_cancel_reconciliation(self):
        """
        Avoid deletion of move if it was a debit created from checks
        """
        for st_line in self:
            for move in st_line.journal_entry_ids:
                if self.env['account.check.operation'].search(
                        [('origin', '=', 'account.move,%s' % move.id)]):
                    move.write({'statement_line_id': False})
                    move.line_ids.filtered(
                        lambda x: x.statement_id == st_line.statement_id
                    ).write({'statement_id': False})
                    self -= st_line
        return super(
            AccountBankStatementLine, self).button_cancel_reconciliation()

    def process_reconciliation(
            self, counterpart_aml_dicts=None, payment_aml_rec=None,
            new_aml_dicts=None):
        """
        If the counterpart move line is a check delivered, then
        we record the debit from the statement on the check
        EVERYTHING: for now if the line of extract is canceled we do not erase the
        debit, we would have to see if we want to do that by modifying the function of
        up directly
        """

        check = False
        if counterpart_aml_dicts:
            for line in counterpart_aml_dicts:
                move_line = line.get('move_line')
                check = move_line and move_line.payment_id.check_id or False
        moves = super(AccountBankStatementLine, self).process_reconciliation(
            counterpart_aml_dicts=counterpart_aml_dicts,
            payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
        if check and check.state == 'handed':
            if check.journal_id != self.statement_id.journal_id:
                raise ValidationError(_(
                    'To record the debit of a check from the statement,, '
                    'the check and extract journal should be the same'
                ))
            if len(moves) != 1:
                raise ValidationError(_(
                    'To record the debit of a check from the extract '
                    'there should only be one counterpart line'))
            check._add_operation('debited', moves, date=moves.date)
        return moves
