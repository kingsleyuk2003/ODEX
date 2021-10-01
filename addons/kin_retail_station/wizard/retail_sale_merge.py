# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.exceptions import UserError
from datetime import  datetime


class RetailSaleMergeWizard(models.TransientModel):
    _name = 'retail.sale.merge.wizard'
    _description = 'Retail Sale Merge Wizard'


    @api.onchange('retail_station_id','date')
    def populate_shift_sale(self):
        if self.retail_station_id and self.date :
            retail_sale_obj = self.env['kin.retail.sale']
            retail_sales_approved = retail_sale_obj.search(
                [('retail_station_id', '=', self.retail_station_id.id), ('retail_sale_date', '=', self.date),
                 ('state', '=', 'approve')])

            self.sale_shift_ids = retail_sales_approved



    @api.multi
    def action_merge(self):
        retail_sale_obj = self.env['kin.retail.sale']
        shift_sales = retail_sale_obj.search([('retail_station_id', '=', self.retail_station_id.id),('retail_sale_date', '=', self.date)])
        if not shift_sales :
            raise UserError(_("No Retail Shift Sales for %s" % (
            datetime.strptime(self.date, '%Y-%m-%d').strftime('%d-%m-%Y'))))

        retail_sales_close = retail_sale_obj.search(
            [('retail_station_id', '=', self.retail_station_id.id), ('retail_sale_date', '=', self.date),
             ('state', '!=', 'approve')])
        if retail_sales_close:
            raise UserError(
                _("Sorry, There is still an On-going Shift with ID - %s for %s, that needs to be approved and closed by the retail manager. Please approve and close all shifts before merging the shifts" % (retail_sales_close[0].name,datetime.strptime(retail_sales_close[0].retail_sale_date , "%Y-%m-%d").strftime("%d-%m-%Y"))))

        #create the stock control
        stock_control_obj = self.env['kin.stock.control']
        fuel_pump_obj = self.env['kin.fuel.pump']
        tank_storage_obj = self.env['kin.tank.storage']
        fuel_pumps = fuel_pump_obj.search([('retail_station_id', "=", self.retail_station_id.id)])

        retail_sales_approved = []
        if self.retail_station_id and self.date :
            retail_sales_approved = retail_sale_obj.search(
                [('retail_station_id', '=', self.retail_station_id.id), ('retail_sale_date', '=', self.date),
                 ('state', '=', 'approve')])


        vals = {
            'stock_control_date': self.date,
            'retail_station_id': self.retail_station_id.id,
        }
        stock_control_id = stock_control_obj.create(vals)

        for fuel_pump in fuel_pumps:
            self.env['kin.pump.sale'].create({
                'pump_id': fuel_pump.id,
                'product_price': fuel_pump.selling_price,
                'stock_control_id':stock_control_id.id
            })

        # populate tank lines
        tanks = tank_storage_obj.search([('retail_station_id', "=", self.retail_station_id.id)])

        for tank in tanks:
            self.env['kin.tank.dipping'].create({
                    'tank_id': tank.id,
                    'opening_stock': tank.current_closing_stock,
                'stock_received' : tank.current_stock_received,
                'current_int_transfer_in': tank.current_int_transfer_in,
                'current_int_transfer_out': tank.current_int_transfer_out,
                'stock_control_id': stock_control_id.id
                })

        total_cash_sales_shift_sale = total_cash_collected_shift_sale = total_pos_card_shift_sale = total_voucher_shift_sale = other_payment_shift_sale = cash_difference_shift_sale = 0
        retail_sale_obj = self.env['kin.retail.sale']
        for pump_sale in stock_control_id.pump_sale_ids:
            thelist = []
            for ss in shift_sales:
                thelist.append(ss.id)
            earliest_shift = min(thelist)
            later_shift = max(thelist)
            for shift_sale_pump in retail_sale_obj.browse(earliest_shift).pump_sale_ids:
                if pump_sale.pump_id == shift_sale_pump.pump_id:
                    pump_sale.meter_start = shift_sale_pump.meter_start

            for shift_sale_pump in retail_sale_obj.browse(later_shift).pump_sale_ids:
                if pump_sale.pump_id == shift_sale_pump.pump_id:
                    pump_sale.meter_end = shift_sale_pump.meter_end


            total_cash_sales = total_cash_collected = total_pos_card = other_payment = cash_difference = 0
            for shift_sale in shift_sales:
                total_cash_sales += shift_sale.total_cash_sales
                total_cash_collected += shift_sale.total_cash_collected
                total_pos_card += shift_sale.total_pos_card
                total_voucher_shift_sale +=  shift_sale.total_voucher
                other_payment += shift_sale.other_payment
                cash_difference += shift_sale.cash_difference
                shift_sale.stock_control_id = stock_control_id

                for shift_sale_pump in shift_sale.pump_sale_ids:
                    if pump_sale.pump_id == shift_sale_pump.pump_id:
                        pump_sale.rtt += shift_sale_pump.rtt


        total_cash_sales_shift_sale = total_cash_sales
        total_cash_collected_shift_sale = total_cash_collected
        total_pos_card_shift_sale = total_pos_card
        other_payment_shift_sale = other_payment
        cash_difference_shift_sale = cash_difference


        for td in stock_control_id.tank_dipping_ids:
            td.opening_stock = td.tank_id.stock_level
            # if shift_sales:
            #     for shift_sale_tank in shift_sales[0].tank_dipping_ids :
            #         if td.tank_id == shift_sale_tank.tank_id :
            #


        vals = {
            'total_cash_sales_shift_sale': total_cash_sales_shift_sale,
            'total_cash_collected_shift_sale':total_cash_collected_shift_sale,
            'total_pos_card_shift_sale': total_pos_card_shift_sale ,
            'total_voucher_shift_sale': total_voucher_shift_sale,
            'other_payment_shift_sale' : other_payment_shift_sale,
            'cash_difference_shift_sale': cash_difference_shift_sale,
            'retail_station_id': self.retail_station_id.id
        }
        stock_control_id.write(vals)
        stock_control_id._amount_all()

        model_data_obj = self.env['ir.model.data']
        action = self.env['ir.model.data'].xmlid_to_object('kin_retail_station.action_kin_stock_control_form')
        form_view_id = model_data_obj.xmlid_to_res_id('kin_retail_station.view_stock_control_form')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,  #put this view mode to render properly, otherwise you will have an empty form
            'target': action.target,
            'domain': [('id', 'in', [x.id for x in stock_control_id])],
            'res_model': action.res_model,
        }

    def _get_user_retail_station(self):
        user = self.env.user
        retail_station_obj = self.env['kin.retail.station']
        retail_station = retail_station_obj.search([('retail_station_manager_id','=',user.id)])
        return retail_station and retail_station[0].id


    retail_station_id = fields.Many2one('kin.retail.station', string='Retail Station',required=True,default=_get_user_retail_station)
    date = fields.Date(string='Date', required=True)
    sale_shift_ids = fields.Many2many('kin.retail.sale',string='Approved Retail Pump Sales Shifts')



