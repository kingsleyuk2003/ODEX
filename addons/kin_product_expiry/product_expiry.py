# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from datetime import datetime, timedelta
from openerp import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin

class StockQuantExtend(models.Model):
    _inherit = 'stock.quant'

    def _compute_remaining_days(self):
        for lot in self :
            if lot.expiry_date :
                exp_date = lot.expiry_date
                today = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), DEFAULT_SERVER_DATETIME_FORMAT)
                expiry_date = datetime.strptime(exp_date,'%Y-%m-%d')
                date_diff = expiry_date - today
                remaining_days = date_diff.days
                lot.days_remaining = remaining_days

    days_remaining = fields.Integer(string='Remaining Days to Expire', compute='_compute_remaining_days')


class StockPackOperationExtend(models.Model):
    _inherit = 'stock.pack.operation.lot'

    expiry_date = fields.Date(related='lot_id.expiry_date',string='Expiry Date',store=True,help="Expiry Date when the batch/lot becomes dangerous")




class StockProductionLotExtend(models.Model):
    _inherit = 'stock.production.lot'

    days_remaining = fields.Integer(string='Remaining Days to Expire', compute='_compute_remaining_days',store=True)

    @api.model
    def run_product_expiry_date_check(self):

        is_send_expiry_alert  = self.env.user.company_id.is_send_expiry_alert
        is_colour_alert = self.env.user.company_id.is_colour_alert
        red_alert = self.env.user.company_id.red_alert or 0
        yellow_alert = self.env.user.company_id.yellow_alert or 0
        green_alert = self.env.user.company_id.green_alert or 0

        if  is_send_expiry_alert :

            the_date = datetime.today().strftime('%d-%m-%Y')
            msg = "<style> " \
                    "table, th, td {" \
                    "border: 1px solid black; " \
                    "border-collapse: collapse;" \
                    "}" \
                    "th, td {" \
                    "padding-left: 5px;"\
                    "}" \
                    "</style>"
            msg += "<p>Hello,</p>"
            msg += "<p>Please see the Stock List Expiry Alert Notification as at %s</p><p></p>"  % (the_date)
            msg += "<table width='100%' >"
            msg += "<tr><td colspan='7' align='center' style='margin:35px' ><h3>Stock List Expiry Items</h3></td></tr>" \
                  "<tr align='left' ><th>S/N</th><th>Batch/Lot No.</th><th>Product Name</th><th>Qty</th><th>Expiry Date</th><th>Remaining Days to Expire</th><th>Location</th></tr>"

            self.search([('expiry_date','!=', None)])._compute_remaining_days()
            at_least_one = False
            sql_statement = """
                        SELECT
                          stock_production_lot.expiry_date,
                          stock_production_lot.name,
                          stock_production_lot.days_remaining,
                          stock_location.usage,
                          stock_location.name as stock_location_name,
                          product_product.name_template,
                          stock_quant.qty
                        FROM
                          public.stock_production_lot,
                          public.stock_quant,
                          public.stock_location,
                          public.product_product
                        WHERE
                          stock_production_lot.id = stock_quant.lot_id AND
                          stock_quant.location_id = stock_location.id AND
                          product_product.id = stock_quant.product_id AND
                          usage = 'internal' AND
                          expiry_date <= %s;
                        """
            today = datetime.today().strftime('%Y-%m-%d')
            args = (today,)
            self.env.cr.execute(sql_statement, args)
            dictAll = self.env.cr.dictfetchall()

            count = 0
            for item in dictAll :
                lot_name = item['name']
                product_name = item['name_template']
                remaining_days = item['days_remaining']
                qty = item['qty']
                location_name = item['stock_location_name']
                status_color = ""
                if is_colour_alert :
                    if remaining_days <= red_alert :
                        status_color = "#ff4d4d"
                    elif remaining_days <= yellow_alert :
                        status_color = "#fffddd"
                    elif remaining_days <= green_alert:
                        status_color = "ffeehhh"
                expiry_date_format = datetime.strptime(item['expiry_date'],'%Y-%m-%d').strftime('%d-%m-%Y')
                count += 1
                at_least_one = True
                msg += "<tr bgcolor='%s' ><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (status_color,count,lot_name,product_name,qty,expiry_date_format,remaining_days,location_name)

            msg += "</table> <p></p><p>Incase you want any of the items to be exempted from the daily alert list. Please log in and clear the alert date for the batch/lot in the inventory application for the specific product. You can as well include other batch products by setting the expiry date and the alert date for each specific product in the inventory application</p>" \
				  "<p>Regards and Thanks</p>" \
				  "<p>This is an auto-generated message from %s ERP System</p>" % (self.env.user.company_id.name)


            #Send Email
            company_email = self.env.user.company_id.email.strip()
            if company_email and at_least_one :
                user_ids = []
                mail_obj = self.env['mail.mail']
                group_obj = self.env.ref('kin_product_expiry.group_receive_expiry_alert_email')
                for user in group_obj.users:
                    #Send Email
                    mail_data = {
                            'model': 'stock.production.lot',
                            'res_id': self.id,
                            'record_name': 'Expiry Alert Stock Notification',
                            'email_from': company_email,
                            'reply_to': company_email,
                            'subject': "Expiry Alert Stock Notification for the date %s" % (the_date),
                            'body_html': '%s' % msg,
                            'auto_delete': True,
                            #'recipient_ids': [(4, id) for id in new_follower_ids]
                            'email_to': user.partner_id.email
                        }
                    mail_id = mail_obj.create(mail_data)
                    mail_obj.send([mail_id])

            return True


    def _compute_remaining_days(self):
        for lot in self :
            if lot.expiry_date :
                exp_date = lot.expiry_date
                today = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), DEFAULT_SERVER_DATETIME_FORMAT)
                expiry_date = datetime.strptime(exp_date,'%Y-%m-%d')
                date_diff = expiry_date - today
                remaining_days = date_diff.days
                lot.days_remaining = remaining_days




class ResCompanyProductExpiryExtend(models.Model):
    _inherit = "res.company"


    is_send_expiry_alert = fields.Boolean(string='Send Stock Alert Expiry Notification',default=True)
    is_colour_alert = fields.Boolean(string='Product Alert with Colour Lines',default=True)
    red_alert = fields.Integer(string='Red Alert Days to Product Expiry', help="Highlight Product Alert Lines in Red",default=90)
    yellow_alert = fields.Integer(string='Yellow Alert Days to Product Expiry', help="Highlight Product Alert Lines in Yellow",default=180)
    green_alert = fields.Integer(string='Green Alert Days to Product Expiry', help="Highlight Product Alert Lines in Green",default=360)