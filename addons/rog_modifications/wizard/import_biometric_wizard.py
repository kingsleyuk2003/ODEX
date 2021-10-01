# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models
from openerp.tools.translate import _
from datetime import datetime, timedelta
from openerp.exceptions import UserError
import csv
import base64
import pandas
import StringIO

class ImportBiometricWizard(models.TransientModel):
    _name = 'import.biometric.wizard'

    #learn more about zip()  from https://www.programiz.com/python-programming/methods/built-in/zip
    @api.multi
    def btn_import_biometric(self):
        wiz_data = self.read([])[0]
        file_excel = self.file_csv
        decoded_data = base64.b64decode(file_excel)
        bio_data = pandas.read_excel(StringIO.StringIO(decoded_data))

        ff = bio_data[bio_data['NAME OF PFA'] == 'IBTC Pension Managers Ltd'].columns
        vals =  bio_data[bio_data['NAME OF PFA'] == 'IBTC Pension Managers Ltd'].values[0]
        ffs = zip(list(ff),list(vals))
        fdg = dict(ffs)

        return ff


    @api.multi
    def btn_refund_rule(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0]  # converts all objects to lists that can be easily be passed to the report
        active_id = context.get('active_id')
        date_from = datetime.strptime(wiz_data['date_from'], '%Y-%m-%d')
        date_to = datetime.strptime(wiz_data['date_to'], '%Y-%m-%d')

        #check if the date is within the range of the current rule adjustment
        rule_adjust_obj = self.env['rule.adjustment']
        ra_obj = rule_adjust_obj.browse(active_id)
        rule_date_from = datetime.strptime(ra_obj.date_from, '%Y-%m-%d')
        rule_date_to = datetime.strptime(ra_obj.date_to, '%Y-%m-%d')
        employee = ra_obj.employee_id
        is_refunded = ra_obj.is_refunded
        rule_type = ra_obj.rule_type

        no_of_days = 0
        for rul_ref in ra_obj.refund_rule_ids :
            no_of_days += rul_ref.no_of_days

        wkdays = ra_obj.get_default_working_days(wiz_data['date_from'],wiz_data['date_to']) + 1

        if ra_obj.no_of_days - wkdays < 0 :
            raise UserError('Sorry, you cannot refund more days than the total cumulative %s days' % ra_obj.no_of_days)

        if ra_obj.is_refund :
            raise UserError(_('Sorry, you cannot refund a refund rule'))

        refund_rule_type = False
        if rule_date_from <= date_from and rule_date_to >= date_to :

            for rul_ref in ra_obj.refund_rule_ids:
                ref_date_from = datetime.strptime(rul_ref.date_from, '%Y-%m-%d')
                ref_date_to =datetime.strptime( rul_ref.date_to, '%Y-%m-%d')

                if (date_from <=  ref_date_from  and date_to >= ref_date_from) or  (date_from <=  ref_date_to and date_to >= ref_date_to):
                    raise UserError(_('Overlapping Date Range with previous refund rules'))

            # create a new rule adjustment, open it and send notification
            if rule_type == 'absent' :
                refund_rule_type = 'absent_refund'
            elif rule_type == 'lieo' :
                refund_rule_type = 'lieo_refund'
            elif rule_type == 'lwp':
                refund_rule_type = 'lwpr_refund'

            vals = {
                'employee_id': employee.id,
                'rule_type': refund_rule_type,
                'date_from': date_from,
                'date_to': date_to,
                'ra_id': ra_obj.id,
                'is_refund' : True,

            }
            res = rule_adjust_obj.create(vals)
            res.action_confirm()
            ra_obj.is_refunded = True
        else:
            raise UserError(_('Please check your date range'))

        #open the refund rule adjustment
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'rule.adjustment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', res.id)]
        }











    file_csv = fields.Binary(string='Biometric CSv File')








