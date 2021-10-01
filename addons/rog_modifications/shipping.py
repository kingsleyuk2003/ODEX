# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, time, timedelta


class ImportPermit(models.Model):
    _name = 'import.permit'
    _inherit = ['mail.thread']

    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_modifications.group_receive_import_permit_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_('%s for (%s), which is being initiated by %s.') %
                          (msg, self.name, self.env.user.name),
                          subject='%s' % (msg),
                          subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' %
                                  (user_names, msg))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('ip_code') or 'New'
        res = super(ImportPermit, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return

    @api.multi
    def button_app_form(self):
        self.state = 'app_form'
        self.email_dispatch('Obtain Application Form')
        return

    @api.multi
    def button_payment_remita(self):
        self.state = 'payment_remita'
        self.email_dispatch('Payment Made on Remita Portal')
        return

    @api.multi
    def button_app_form_submitted(self):
        self.state = 'app_form_submitted'
        self.email_dispatch('Application Form Filled and Submitted')
        return

    @api.multi
    def button_awaiting_issuance_license(self):
        self.state = 'awaiting_issuance_license'
        self.email_dispatch('Awaiting Issuance of License')
        return

    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    name = fields.Char('ID')
    document_no = fields.Char(string='Import Permit No.')
    date = fields.Date(string='Date of Issue')
    expiry_date = fields.Date(string="Expiry Date")
    company_name = fields.Char(string='Name of Company')
    user_id = fields.Many2one('res.users',
                              string='User',
                              default=lambda self: self.env.user.id,
                              ondelete='restrict')
    description = fields.Text(string='Description')
    state = fields.Selection(
        [('draft', 'Draft'), ('app_form', 'Obtain Application Form'),
         ('payment_remita', 'Payment Made on Remita Portal'),
         ('app_form_submitted', 'Application Form Filled and Submitted'),
         ('awaiting_issuance_license', 'Awaiting Issuance of License'),
         ('done', 'Done'), ('cancel', 'Cancel')],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='draft')
    reminder_ids = fields.One2many('kin.reminder',
                                   'import_permit_id',
                                   string='Reminders')
    import_permit_line_ids = fields.One2many('import.permit.lines','import_permit_id', string='Import Permit Lines')

class ImportPermitLines(models.Model):
    _name = 'import.permit.lines'

    product_id = fields.Many2one('product.product', string='Product')
    country_origin = fields.Char(string='Country of Origin')
    qty_approved = fields.Float(string='Quantity Approved (MT)')
    estimated_value = fields.Float(string='Estimated Value')
    inclusion = fields.Float(string='Inclusion')
    quantity_used = fields.Float(string='Quantity Used')
    bank = fields.Char(string='Bank')
    balance = fields.Float(string='Balance')
    import_permit_id = fields.Many2one('import.permit', string='Import Permit')


class ShipToShipTransfer(models.Model):
    _name = 'ship.to.ship'
    _inherit = ['mail.thread']

    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_modifications.group_receive_ship_to_ship_email_notification')
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_('%s for (%s), which is being initiated by %s.') %
                          (msg, self.name, self.env.user.name),
                          subject='%s' % (msg),
                          subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' %
                                  (user_names, msg))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'sts_code') or 'New'
        res = super(ShipToShipTransfer, self).create(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return

    @api.multi
    def btn_inspect_product_mv(self):
        self.state = 'inspect_product_mv'
        self.email_dispatch('Inspection of Product on Mother Vessel')
        return

    @api.multi
    def btn_confirm_integrity_dv(self):
        self.state = 'confirm_integrity_dv'
        self.email_dispatch('Confirm Integrity of Daughter Vessel')
        return

    @api.multi
    def btn_engage_independent_inspection(self):
        self.state = 'engage_independent_inspection'
        self.email_dispatch(
            'Engage Independent Inspector Company to Inspect Product on Mother Vessel'
        )
        return

    @api.multi
    def btn_operation_guideline_sent(self):
        self.state = 'operation_guideline_sent'
        self.email_dispatch('Operation Guideline Details Sent to Vessel Owner')
        return

    @api.multi
    def btn_terms_of_engagement_reviewed(self):
        self.state = 'terms_of_engagement_reviewed'
        self.email_dispatch('Terms of Engagement is Being Reviewed')
        return

    @api.multi
    def btn_vessel_cleared(self):
        self.state = 'vessel_cleared'
        self.email_dispatch('Vessels are Cleared')
        return

    @api.multi
    def btn_nominate_loading_vendors(self):
        self.state = 'nominate_loading_vendors'
        self.email_dispatch('Nominate Loading Vendors')
        return

    @api.multi
    def btn_loading_instruction_sent_daughter_vessel_company(self):
        self.state = 'loading_instruction_sent_daughter_vessel_company'
        self.email_dispatch(
            'Loading Instruction Sent to Daughter Vessel Company')
        return

    @api.multi
    def btn_npa_clearance(self):
        self.state = 'npa_clearance'
        self.email_dispatch('NPA Clearance for Arrival Purposes')
        return

    @api.multi
    def btn_nor_received(self):
        self.state = 'nor_received'
        self.email_dispatch(
            'Notice of Readiness is Received from Master Vessel on Arrival')
        return

    @api.multi
    def btn_sts_monitoring(self):
        self.state = 'sts_monitoring'
        self.email_dispatch('Ship To Ship Transfer Monitoring Commences')
        return

    @api.multi
    def btn_documentary_instructions_sent_mv(self):
        self.state = 'documentary_instructions_sent_mv'
        self.email_dispatch(
            'Documentary Instructions Sent to the Master Vessel')
        return

    @api.multi
    def btn_post_cargo_formalities(self):
        self.state = 'post_cargo_formalities'
        self.email_dispatch('Post Cargo Formalities Commences')
        return

    @api.multi
    def btn_transship_document_forwarded(self):
        self.state = 'transship_document_forwarded'
        self.email_dispatch(
            'Transship Documents are Forwarded to the Charterers')
        return

    @api.multi
    def btn_discharge_order_for_daughter_vessel(self):
        self.state = 'discharge_order_for_daughter_vessel'
        self.email_dispatch(
            'Daughter Vessel Discharge Order Forwarded for Disport Operation')
        return

    @api.multi
    def btn_naval_clearance_application(self):
        self.state = 'naval_clearance_application'
        self.email_dispatch('Naval Clearance Application Initiated')
        return

    @api.multi
    def btn_transship_document_nimasa_dues(self):
        self.state = 'transship_document_nimasa_dues'
        self.email_dispatch(
            'Port Agent Process Transship and Port Call Documents for Nimasa Dues'
        )
        return

    @api.multi
    def btn_processes_monitoring(self):
        self.state = 'processes_monitoring'
        self.email_dispatch('Processes Monitored')
        return

    @api.multi
    def btn_vendor_bill_received(self):
        self.state = 'vendor_bill_received'
        self.email_dispatch(
            'Vendor Bill Received and Sent to Finance Department for Payment Processing'
        )
        return

    @api.multi
    def btn_event_summary_mgt(self):
        self.state = 'event_summary_mgt'
        self.email_dispatch(
            'Event Summary Sent to Management after Documents Filing')
        return

    @api.multi
    def btn_done(self):
        self.state = 'done'
        self.email_dispatch('Done')
        return

    @api.multi
    def btn_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Cancel')
        return

    name = fields.Char('ID')
    document_no = fields.Char(string='Document No.')
    date = fields.Date(string='Date')
    product_vendor_id = fields.Many2one('res.partner',
                                        string='Product Vendor',
                                        related='purchase_id.partner_id')
    inspector_id = fields.Many2one('res.partner', string='Inspector Company')
    mother_vessel_location = fields.Char(string='STS Location')
    ullage_bdischarge_mt = fields.Float(string="Ullage b/4 DISCH(MT)")
    ullage_bdischarge_ltrs = fields.Float(string="Ullage b/4 DISCH(ltrs)")
    ullage_report_ltrs = fields.Float(string="Ullage Report (ltrs)")
    expected_inspection_date = fields.Date(string='Expected Inspection Date')
    user_id = fields.Many2one('res.users',
                              string='User',
                              default=lambda self: self.env.user.id,
                              ondelete='restrict')
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('inspect_product_mv', 'Inspection of Product on Mother Vessel'),
        ('confirm_integrity_dv', 'Confirm Integrity of Daughter Vessel'),
        ('engage_independent_inspection',
         'Engage Independent Inspector Company to Inspect Product on Mother Vessel'
         ),
        ('operation_guideline_sent',
         'Operation Guideline Details Sent to Vessel Owner'),
        ('terms_of_engagement_reviewed',
         'Terms of Engagement is Being Reviewed'),
        ('vessel_cleared', 'Vessels are Cleared'),
        ('nominate_loading_vendors', 'Nominate Loading Vendors'),
        ('loading_instruction_sent_daughter_vessel_company',
         'Loading Instruction Sent to Daughter Vessel Company'),
        ('npa_clearance', 'NPA Clearance for Arrival Purposes'),
        ('nor_received',
         'Notice of Readiness is Received from Master Vessel on Arrival'),
        ('sts_monitoring', 'Ship To Ship Transfer Monitoring Commences'),
        ('documentary_instructions_sent_mv',
         'Documentary Instructions Sent to the Master Vessel'),
        ('post_cargo_formalities', 'Post Cargo Formalities Commences'),
        ('transship_document_forwarded',
         'Transship Documents are Forwarded to the Charterers'),
        ('discharge_order_for_daughter_vessel',
         'Daughter Vessel  Discharge Order Forwarded for Disport Operation'),
        ('naval_clearance_application',
         'Naval Clearance Application Initiated'),
        ('transship_document_nimasa_dues',
         'Port Agent Process Transship and Port Call Documents for Nimasa Dues'
         ), ('processes_monitoring', 'Processes Monitored'),
        ('vendor_bill_received',
         'Vendor Bill Received and Sent to Finance Department for Payment Processing'
         ),
        ('event_summary_mgt',
         'Event Summary Sent to Management after Documents Filing'),
        ('done', 'Done'), ('cancel', 'Cancel')
    ],
                             string='Status',
                             readonly=True,
                             copy=False,
                             index=True,
                             track_visibility='onchange',
                             default='draft')
    reminder_ids = fields.One2many('kin.reminder',
                                   'shiptoship_id',
                                   string='Reminders')

    mf = fields.Char(string='MF', store=True)
    bank_qty = fields.Float(string='Bank Qty (MT)')
    supplier_id = fields.Many2one('res.partner', string='Supplier', store=True)
    mv_vessel = fields.Char(string='MV Vessel')
    dv_vessel = fields.Char(string='DV Vessel')
    dv_bl_qty = fields.Float(string='DV BL Qty. (MT)')
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 store=True)
    tank_farm = fields.Char(string='Tank Farm')
    discharge_date = fields.Date(string='Discharged Date')
    shore_receipt = fields.Float(string='Shore Receipt (Ltrs)',
                                 track_visibility='onchange')
    shore_tank = fields.Float(string='Shore Tank (MT)')
    purchase_id = fields.Many2one('purchase.order',
                                  string='Procurement with Form M',
                                  ondelete='cascade')

    mf = fields.Char(string='MF', related='purchase_id.form_m_no', store=True)
    supplier_id = fields.Many2one('res.partner',
                                  string='Supplier',
                                  related='purchase_id.partner_id',
                                  store=True)
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 related='purchase_id.product_id',
                                 store=True)
    purchase_id = fields.Many2one('purchase.order',
                                  string='Procurement with Form M',
                                  ondelete='cascade')


class VesselCharterContract(models.Model):
    _name = 'vessel.charter.contract'
    _inherit = ['mail.thread']

    def email_dispatch(self, msg=''):
        user_ids = []
        user_names = ''
        group_obj = self.env.ref(
            'rog_modifications.group_receive_charter_contract_email_notification'
        )
        for user in group_obj.users:
            user_names += user.name + ", "
            user_ids.append(user.id)
        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_('%s for (%s), which is being initiated by %s.') %
                          (msg, self.name, self.env.user.name),
                          subject='%s' % (msg),
                          subtype='mail.mt_comment')
        self.env.user.notify_info('%s Will Be Notified by Email for %s Stage' %
                                  (user_names, msg))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'vesselc_code') or 'New Contract'
        res = super(VesselCharterContract, self).create(vals)

        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        self.email_dispatch('Draft')
        return

    @api.multi
    def button_done(self):
        self.state = 'done'
        self.email_dispatch('Completed Process')
        return

    @api.multi
    def button_engage_fendering_company(self):
        self.state = 'engage_fendering_company'
        self.email_dispatch('Fendering Company Engagement')
        return

    @api.multi
    def button_source_vessel(self):
        self.state = 'source_vessel'
        self.email_dispatch('Sourcing Vessel')
        return

    @api.multi
    def button_new_contract(self):
        self.state = 'new_contract'
        self.email_dispatch('New Charter Contract')
        return

    @api.multi
    def button_cancel(self):
        self.state = 'cancel'
        self.email_dispatch('Charter Contract Cancelled')
        return

    name = fields.Char('ID')
    document_no = fields.Char(string='Document No.')
    vehicle_contract_date = fields.Date(string='Date')
    vessel_owner_id = fields.Many2one('res.partner', string='Vessel Owner')
    agent_id = fields.Many2one('res.partner',
                               string='Agent for Sourcing Vessel')
    fendering_company_id = fields.Many2one('res.partner',
                                           string='Fendering Company')
    user_id = fields.Many2one('res.users',
                              string='User',
                              default=lambda self: self.env.user.id,
                              ondelete='restrict')
    description = fields.Text(string='Description')
    state = fields.Selection(
        [('draft', 'Draft'), ('new_contract', 'New Contract'),
         ('source_vessel', 'Agent Sourcing Vessel'),
         ('engage_fendering_company', 'Engage Fendering Company'),
         ('done', 'Done'), ('cancel', 'Cancel')],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='draft')   
    reminder_ids = fields.One2many('kin.reminder',
                                   'charter_id',
                                   string='Reminders')


class Reminder(models.Model):
    _inherit = 'kin.reminder'

    charter_id = fields.Many2one('vessel.charter.contract',
                                 string='Vessel Charter Contract')
    shiptoship_id = fields.Many2one('ship.to.ship',
                                    string='Ship To Ship Transfer')
    import_permit_id = fields.Many2one('import.permit', string='Import Permit')
