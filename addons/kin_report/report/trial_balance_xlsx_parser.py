# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api
from datetime import datetime

class TrialBalanceReportParser(models.TransientModel):

    _name = 'trial.balance.parser'


    def _get_data(self,form):
        journal_ids = form['journal_ids']
        operating_unit_ids = form['operating_unit_ids']
        account_ids = form['account_ids']
        start_date = form['start_date']
        end_date = form['end_date']
        where_start_date = ''
        from_ou = ''
        where_ou = ''
        if not start_date :
            where_start_date = ''
        else:
            where_start_date = "account_move_line.date >= '%s' AND"%(start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-12-31')

        if operating_unit_ids :
            from_ou = "INNER JOIN operating_unit ON account_move_line.operating_unit_id = operating_unit.id"
            where_ou = "account_move_line.operating_unit_id in (%s) AND" % ','.join(str(ou_id) for ou_id in operating_unit_ids)

        sql_statement = """
            SELECT
              account_account.code,
              account_account.id,
              account_account.name,
              sum(account_move_line.debit) as debit,
              sum(account_move_line.credit) as credit,
              sum(account_move_line.balance) as balance
            FROM
            account_move_line
            INNER JOIN account_journal ON  account_move_line.journal_id = account_journal.id
            """ + from_ou + """
            INNER JOIN account_account ON account_move_line.account_id = account_account.id
            WHERE
              account_move_line.account_id in %s AND
              account_move_line.journal_id in %s AND
              """ + where_ou + """
              """ + where_start_date + """
              account_move_line.date <= %s AND
              NOT account_account.deprecated
            GROUP BY
              account_account.id
            ORDER BY
              account_account.code ASC;
            """
        args = (tuple(account_ids),tuple(journal_ids),end_date,)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll






