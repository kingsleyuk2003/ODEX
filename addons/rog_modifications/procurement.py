# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_is_zero, float_compare
from urllib import urlencode
from urlparse import urljoin
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, Warning
from openerp.tools import amount_to_text
from datetime import datetime, time, timedelta

class PurchaseRequestLineExtend(models.Model):
    _inherit = 'purchase.request.line'

    rog_request_id = fields.Many2one(related='request_id.rog_request_id', string='ROG Request',store=True)

class PurchaseRequestExtend(models.Model):
    _inherit = 'purchase.request'

    @api.multi
    def button_approved(self):
        res = super(PurchaseRequestExtend,self).button_approved()
        #create the ROG procurement register
        for line in self.line_ids:
            self.rog_request_id = self.env['procurement.register'].create(
                {   'department_id' : line.department_id.id,
                    'request_received': line.specifications,
                    'date_request' : line.date_required  ,
                    'purchase_request_line_id': line.id,

                }
            )

        return res

    rog_request_id = fields.Many2one('procurement.register',string='ROG Request')
    is_budget_approved_item = fields.Selection([
        ('yes', 'YES'),
        ('no', 'NO')
    ], string='Budget Approved Items', copy=False, index=True, track_visibility='onchange')
    budget_ref_no = fields.Char(string='Budget Reference No.', track_visibility='onchange')
    req_type = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('very_urgent', 'Very Urgent')
    ], string='Type', copy=False, index=True, track_visibility='onchange')



class ActionTaken(models.Model):
    _name = 'action.taken'

    name = fields.Char(string='Action Taken')
    description = fields.Char(string='Description')

class ProcurementRegister(models.Model):
    _name = 'procurement.register'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def btn_ongoing(self):
        self.state = 'ongoing'

    @api.multi
    def btn_completed(self):
        self.state = 'completed'

    @api.multi
    def btn_cancel(self):
        self.state = 'cancel'

    @api.multi
    def btn_reset(self):
        self.state = 'draft'

    @api.depends('estimated_cost_saving_curr', 'current_cost','advance_paid')
    def _compute_cost_saving_perc(self):
        for line in self:
            #Anu of the approach works fine here
           # line.estimated_cost_saving_perc =  (line.estimated_cost_saving_curr / (line.current_cost + line.advance_paid)) * 100
            if line.estimated_cost_saving_curr :
                line.update({
                    'estimated_cost_saving_perc': (line.estimated_cost_saving_curr / (line.current_cost + line.advance_paid)) * 100
                })



    @api.depends('date_request','po_confirm_date')
    def _compute_duration(self):
        for rec in self :
            if rec.date_request and rec.po_confirm_date :
                date_request = datetime.strptime(rec.date_request , '%Y-%m-%d')
                po_confirm_date = datetime.strptime(rec.po_confirm_date , '%Y-%m-%d')

                employees = self.env['hr.employee'].search([])
                special_days = self.env['hr.holidays'].get_special_days(str(date_request),str(po_confirm_date),employees[0].company_id)

                date_diff = (po_confirm_date - date_request).days - len(special_days)
                rec.indent_po_days = date_diff


    department_id = fields.Many2one('hr.department',string='Department')
    request_received = fields.Char(string='Request Received')
    date_request = fields.Date(string='Date')
    action_taken = fields.Many2one('action.taken',string='Action Taken')
    vendor_awarded_id = fields.Many2one('res.partner',string='Vendor Awarded')
    current_cost = fields.Float(string='Current Cost')
    advance_paid = fields.Float(string='Advance Paid')
    status = fields.Char(string='Status')
    remark = fields.Text(basestring='Remark')
    estimated_cost_saving_curr = fields.Float(string='Estimated Cost Savings (N)')
    estimated_cost_saving_perc = fields.Float(string='Estimated Cost Savings (%)',compute=_compute_cost_saving_perc,store=True)
    po_confirm_date = fields.Date(string='PO Confirmed Date')
    po_id = fields.Many2one('purchase.order',string='Purchase Order')
    indent_po_days = fields.Integer(string='Indent to PO (days)',compute='_compute_duration',store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'ONGOING'),
        ('completed', 'COMPLETED'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', copy=False, index=True, track_visibility='onchange')

    purchase_request_line_id = fields.Many2one('purchase.request.line',string='Purchase Request Line')



class SupplierEvaluation(models.Model):
    _name = 'supplier.evaluation'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('sev_code') or 'New'
        res = super(SupplierEvaluation, self).create(vals)
        return res

    @api.multi
    def btn_user_supplier_evaluation(self):
        self.user_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.user_id = self.env.user
        self.state = 'user_sup_eval'

    @api.multi
    def btn_proc_supplier_evaluation(self):
        self.user_proc_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.user_proc_id = self.env.user
        self.state = 'proc_sup_eval'

    @api.multi
    def btn_cancel(self):
        self.state = 'cancel'

    @api.multi
    def btn_reset(self):
        self.state = 'draft'

    @api.depends('handling_of_rejections','condition_of_goods_on_arrival','frequency_of_rejections','handling_of_complaints','compliance_with_qhsse','technical_assistance','other_user_kpi','on_time_delivery','adherence_to_agreement','delivers_information','information_dissemination','interpersonal_communication','other_procurement_kpi')
    def compute_rating(self):
        overall_score = 0
        highest_score = 0
        count = 0
        if self.handling_of_rejections :
            overall_score += int(self.handling_of_rejections)
            count += 1
        if self.condition_of_goods_on_arrival:
            overall_score += int(self.condition_of_goods_on_arrival)
            count += 1
        if self.frequency_of_rejections :
            overall_score += int(self.frequency_of_rejections)
            count += 1
        if self.handling_of_complaints :
            overall_score += int(self.handling_of_complaints)
            count += 1
        if self.compliance_with_qhsse :
            overall_score += int(self.compliance_with_qhsse)
            count += 1
        if self.technical_assistance :
            overall_score += int(self.technical_assistance)
            count += 1
        if self.other_user_kpi :
            overall_score += int(self.other_user_kpi)
            count += 1
        if self.on_time_delivery :
            overall_score += int(self.on_time_delivery)
            count += 1
        if self.adherence_to_agreement :
            overall_score += int(self.adherence_to_agreement)
            count += 1
        if self.delivers_information :
            overall_score += int(self.delivers_information)
            count += 1
        if self.information_dissemination :
            overall_score += int(self.information_dissemination)
            count += 1
        if self.interpersonal_communication:
            overall_score += int(self.interpersonal_communication)
            count += 1
        if self.other_procurement_kpi :
            overall_score += int(self.other_procurement_kpi)
            count += 1
        highest_score = count * 4
        if highest_score :
            perc_score = (float(overall_score) / float(highest_score)) * 100
        else:
            perc_score = 0
        overall_rating = ''

        if perc_score < 50:
            overall_rating = 'Poor'
        elif perc_score >= 50 and perc_score <= 59 :
            overall_rating = 'Room for Improvement'
        elif perc_score >= 60 and perc_score <= 79 :
            overall_rating = 'Satisfactory'
        elif perc_score >= 80 :
            overall_rating = 'Excellent'
        self.percentage_score = perc_score
        self.overall_rating = overall_rating






    name = fields.Char('Indent Serial No')
    supplier_id = fields.Many2one('res.partner',string='Supplier / Vendor')
    department_id = fields.Many2one('hr.department',string='Department')
    address = fields.Char(string='Address')
    product_id = fields.Char(string='Good / Service')
    received_on = fields.Date(string='Received on')
    handling_of_rejections = fields.Selection([('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'),  ('1','Poor (1)'),], string='Handling of Rejections', copy=False, index=True, track_visibility='onchange')
    condition_of_goods_on_arrival = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Condition of Goods on Arrival', copy=False, index=True, track_visibility='onchange')
    frequency_of_rejections = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Frequency of Rejections', copy=False, index=True, track_visibility='onchange')
    handling_of_complaints = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Handling of Complaints', copy=False, index=True, track_visibility='onchange')
    compliance_with_qhsse = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Compliance with QHSSE', copy=False, index=True, track_visibility='onchange')
    technical_assistance = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Technical Assistance', copy=False, index=True, track_visibility='onchange')
    other_user_kpi = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Other', copy=False, index=True, track_visibility='onchange')
    on_time_delivery = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='On time Delivery', copy=False, index=True, track_visibility='onchange')
    adherence_to_agreement = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Adherence to Agreement', copy=False, index=True, track_visibility='onchange')
    delivers_information = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Delivers Information Without Constant Follow - Up', copy=False, index=True, track_visibility='onchange')
    information_dissemination = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Information Dissemination', copy=False, index=True, track_visibility='onchange')
    interpersonal_communication = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Interpersonal Communication', copy=False, index=True, track_visibility='onchange')
    other_procurement_kpi = fields.Selection(
        [('4', 'Excellent (4)'), ('3', 'Good (3)'), ('2', 'Fair (2)'), ('1', 'Poor (1)'), ],
        string='Handling of Rejections', copy=False, index=True, track_visibility='onchange')
    percentage_score = fields.Float(string='% Score',compute=compute_rating,store=True)
    overall_rating = fields.Char(string='Overall Rating',compute=compute_rating,store=True)
    action_to_be_taken  = fields.Text(string='Action to be Taken')
    user_id = fields.Many2one('res.users',string='User')
    user_date = fields.Date(string='User Date')
    user_proc_id = fields.Many2one('res.users', string='User')
    user_proc_date = fields.Date(string='Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('user_sup_eval', 'User Supplier Evaluation'),
        ('proc_sup_eval', 'Procurement Supplier Evaluation'),
        ('cancel','Cancelled')
    ], string='Status', default='draft',copy=False, index=True, track_visibility='onchange')
    po_id = fields.Many2one('purchase.order', string='Purchase Order')



class GoodVerificationCompare(models.Model):
    _name = 'goods.verification.compare'

    description = fields.Text(string='Description')
    verification_result = fields.Text(string='Verification Result / Observation (As Specified)')
    qhsse_risk_factor = fields.Selection([
        ('high', 'High'),
        ('low', 'Low'),
        ('zero', 'Zero')
    ], string='QHSSE Risk Factor', copy=False, index=True, track_visibility='onchange')
    acceptable_reject = fields.Selection([
        ('acceptable', 'Acceptable'),
        ('reject', 'Reject')
    ], string='Acceptable / Reject', copy=False, index=True, track_visibility='onchange')
    goods_verification_compare_id = fields.Many2one('goods.verification',string='Goods Verification')


class GoodVerification(models.Model):
    _name = 'goods.verification'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('gv_code') or 'New'
        res = super(GoodVerification, self).create(vals)
        return res

    @api.multi
    def btn_user_acceptance(self):
        self.state = 'user_acceptance'
        self.user_id = self.env.user

    @api.multi
    def btn_qhsse_acceptance(self):
        self.state = 'qhsse_acceptance'
        self.qhsse_user_id = self.env.user

    @api.multi
    def btn_ica_acceptance(self):
        self.state = 'ica_acceptance'
        self.ica_user_id = self.env.user

    @api.multi
    def btn_cancel(self):
        self.state = 'cancel'

    @api.multi
    def btn_reset(self):
        self.state = 'draft'


    name = fields.Char('Indent Serial No')
    supplier_id = fields.Many2one('res.partner', string='Supplier Name')
    contact_details = fields.Text(string='Contact Details')
    goods_information = fields.Text(string='Goods Information')
    po_no = fields.Char(string='PO Number')
    delivery_slip_invoice = fields.Char(string='Delivery Slip | Invoice No.')
    date = fields.Date(string='Date')
    good_received_on = fields.Date(string='Goods Received On')
    total_received_qty = fields.Float(string='Total Received Quantity')
    total_acceptable_qty = fields.Float(string='Total Acceptable Quantity')
    total_rejected_qty = fields.Float(string='Total Rejected Quantity')
    returned_qty_supplier = fields.Float(string='Returned Quantity to Supplier')
    under_testing_observation_qty = fields.Float(string='Under testing / Observation Quantity')
    ica_user_id = fields.Many2one('res.users', string='I & CA User')
    qhsse_user_id = fields.Many2one('res.users', string='QHSSE User')
    user_id = fields.Many2one('res.users', string='User')
    state = req_type = fields.Selection([
        ('draft', 'Draft'),
        ('user_acceptance', 'User Acceptance'),
        ('qhsse_acceptance', 'QHSSE Acceptance'),
        ('ica_acceptance', 'ICA Acceptance'),
        ('cancel','Cancelled')
    ], string='Status', default='draft', copy=False, index=True, track_visibility='onchange')
    goods_verification_compare_ids = fields.One2many('goods.verification.compare', 'goods_verification_compare_id',string='Specification vs Actual')
    po_id = fields.Many2one('purchase.order',string='Purchase Order')

class FinalPaymemtTerm(models.Model):
    _name = 'final.payment.term'

    product_id = fields.Many2one('product.product',string='Item')
    partner_id = fields.Many2one('res.partner',string='Vendor Name')
    detail = fields.Text(string='Details')
    tender_proposal_evaluation_id = fields.Many2one('tender.proposal.evaluation', string='Tender Proposal Evaluation')

class FinalApproval(models.Model):
    _name = 'final.approval'

    @api.depends('qty', 'rate')
    def _compute_amount(self):
        for line in self:
            line.update({
                'amount': line.rate * line.qty
            })


    product_id = fields.Many2one('product.product',string='Item')
    partner_id = fields.Many2one('res.partner',string='Vendor Name')
    qty = fields.Float(string='Qty.')
    rate = fields.Float(string='Rate')
    amount = fields.Float(string='Amount',compute='_compute_amount',store=True)
    tender_proposal_evaluation_id = fields.Many2one('tender.proposal.evaluation', string='Tender Proposal Evaluation')

class PaymemtTerm(models.Model):
    _name = 'payment.term'

    product_id = fields.Many2one('product.product',string='Item')
    partner_id = fields.Many2one('res.partner',string='Vendor Name')
    detail = fields.Text(string='Details')
    tender_proposal_evaluation_id = fields.Many2one('tender.proposal.evaluation', string='Tender Proposal Evaluation')


class FinalEvaluation(models.Model):
    _name = 'final.evaluation'

    @api.depends('qty', 'rate')
    def _compute_amount(self):
        for line in self:
            line.update({
                'amount': line.rate * line.qty
            })


    product_id = fields.Many2one('product.product',string='Item')
    partner_id = fields.Many2one('res.partner',string='Vendor Name')
    qty = fields.Float(string='Qty.')
    rate = fields.Float(string='Rate')
    amount = fields.Float(string='Amount',compute='_compute_amount',store=True)
    tender_proposal_evaluation_id = fields.Many2one('tender.proposal.evaluation', string='Tender Proposal Evaluation')

class InitialEvaluation(models.Model):
    _name = 'initial.evaluation'

    @api.depends('qty', 'rate')
    def _compute_amount(self):
        for line in self:
            line.update({
                'amount': line.rate * line.qty
            })

    product_id = fields.Many2one('product.product',string='Item')
    partner_id = fields.Many2one('res.partner',string='Vendor Name')
    qty = fields.Float(string='Qty.')
    rate = fields.Float(string='Rate')
    amount = fields.Float(string='Amount',compute='_compute_amount',store=True)
    tender_proposal_evaluation_id = fields.Many2one('tender.proposal.evaluation', string='Tender Proposal Evaluation')



class TenderProposalEvaluation(models.Model):
    _name = 'tender.proposal.evaluation'
    _inherit = ['mail.thread', 'ir.needaction_mixin']


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('tpe_code') or 'New'
        res = super(GoodVerification, self).create(vals)
        return res

    @api.multi
    def btn_initiate(self):
        self.state = 'initiate'
        self.initiated_by_id = self.env.user

    @api.multi
    def btn_recommend(self):
        self.state = 'recommend'
        self.recommended_by_id = self.env.user


    @api.multi
    def btn_cancel(self):
        self.state = 'cancel'

    @api.multi
    def btn_reset(self):
        self.state = 'draft'

    name = fields.Char('Indent Serial No')
    proposal_purpose = fields.Char('Proposal Purpose / Objective')
    tender_floated_date = fields.Date('Tender Floated on')
    number_parties_sent = fields.Integer('No of Parties RFQ sent')
    nature_job = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('very_urgent', 'Very Urgent')],string='Nature of Job')
    is_budget_approved_item = fields.Selection([
        ('yes', 'YES'),
        ('no', 'NO')
    ], string='Budget Approved Items', copy=False, index=True, track_visibility='onchange')
    budget_ref_no = fields.Char('Budget Reference Number')
    evaluation_offers = fields.Char('Evaluation of offers as under')
    initial_evaluation_ids = fields.One2many('initial.evaluation','tender_proposal_evaluation_id',string='Initial Evaluation')
    final_evaluation_ids = fields.One2many('final.evaluation', 'tender_proposal_evaluation_id', string='Final Evaluation')
    payment_term_ids = fields.One2many('payment.term', 'tender_proposal_evaluation_id', string='Payment Term')
    final_approval_ids = fields.One2many('final.approval', 'tender_proposal_evaluation_id',string='Final Approval')
    final_payment_term_ids = fields.One2many('final.payment.term', 'tender_proposal_evaluation_id', string='Final Payment Term')
    finance_user_id = fields.Many2one('res.users',string='Finance Member')
    user_user_id = fields.Many2one('res.users', string='User Member')
    audit_user_id = fields.Many2one('res.users', string='Audit Member')
    date_negotiation = fields.Date(string='Date of Negotiations Held')
    initiated_by_id = fields.Many2one('res.users', string='Initiated By')
    recommended_by_id = fields.Many2one('res.users', string='Recommended By')
    state = req_type = fields.Selection([
        ('draft', 'Draft'),
        ('initiate', 'Initiated'),
        ('recommend', 'Recommended'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', copy=False, index=True, track_visibility='onchange')



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        for line in self.order_line:
            for prline in line.purchase_request_lines:
                rog_request = prline.rog_request_id
                rog_request.po_confirm_date = self.date_order
                rog_request.current_cost = line.price_subtotal
                rog_request.vendor_awarded_id = self.partner_id
                rog_request.po_id = self
                rog_request.state = 'ongoing'
        return super(PurchaseOrder,self).button_confirm()

    @api.multi
    def button_approve(self):
        #create Goods verication form and Supplier Evaluation form
        if not self.is_lc_purchase :
            self.good_verification_id = self.env['goods.verification'].create({
                'supplier_id':self.partner_id.id,
                'po_id':self.id
            })

            self.supplier_evaluation_id = self.env['supplier.evaluation'].create({
                'supplier_id':self.partner_id.id,
                'po_id':self.id,
            })


        res = super(PurchaseOrder, self).button_approve()
        return res

    def _compute_duration(self):
        for rec in self :
            if rec.date_rfq and rec.date_order :
                date_rfq = datetime.strptime(rec.date_rfq , DEFAULT_SERVER_DATETIME_FORMAT)
                date_order = datetime.strptime(rec.date_order , DEFAULT_SERVER_DATETIME_FORMAT)
                date_diff =  str(date_order - date_rfq)
                rec.duration =  date_diff

    duration = fields.Char(string='Duration(days)', compute='_compute_duration')
    good_verification_id = fields.Many2one('goods.verification',string='Goods Verification Form')
    supplier_evaluation_id = fields.Many2one('supplier.evaluation',string='Supplier Evaluation Form')