# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _
from datetime import datetime, timedelta



class Grades(models.Model):
    _name = 'kin.grade'

    name = fields.Char('Grade')
    description = fields.Char('Description')


class Qualifications(models.Model):
    _name = 'kin.qualification'

    name = fields.Char('Qualification')
    description = fields.Char('Description')

class Employee(models.Model):
    _inherit = 'hr.employee'

    employee_kpi = fields.One2many('kin.kpi.employee','employee_id',string='Kpi Employee')
    employee_pa = fields.One2many('kin.personal.attribute.employee', 'employee_id', string='Personal Attribute Employee')
    employee_pe = fields.One2many('kin.performance.evaluation.employee','employee_id',string='Performance Evaluation Employee')


class KpiEmployee(models.Model):
    _name = 'kin.kpi.employee'

    kpi_id = fields.Many2one('kin.kpi',string='Kpi')
    employee_id = fields.Many2one('hr.employee',string='Employee')
    appraisee_score = fields.Float('Score by Appraisee')
    appraiser_score = fields.Float('Score by Appraiser')
    appraisal_id = fields.Many2one('kin.appraisal', string='Appraisal')


class Kpi(models.Model):
    _name = 'kin.kpi'

    name = fields.Char(string='Key Performance Indicator')
    kpi_employee_id = fields.One2many('kin.kpi.employee','kpi_id',string='Employee Kpi')


class PersonalAttributeEmployee(models.Model):
    _name = 'kin.personal.attribute.employee'

    pa_id = fields.Many2one('kin.personal.attribute',string='Personal Attribute')
    employee_id = fields.Many2one('hr.employee',string='Employee')
    score = fields.Float(string='Score')
    comment_grade = fields.Char(string='Comment on the grade given')
    appraisal_id = fields.Many2one('kin.appraisal', string='Appraisal')


class PersonalAttribute(models.Model):
    _name = 'kin.personal.attribute'

    name = fields.Char(string='Personal Attributes')
    pa_employee_id = fields.One2many('kin.personal.attribute.employee','pa_id',string='Employee PA')


class PerformanceEvaluationEmployee(models.Model):
    _name = 'kin.performance.evaluation.employee'

    pe_employee_id = fields.Many2one('kin.performance.evaluation',string='KPE Employee')
    pe_number = fields.Char(related='pe_employee_id.number', string='Number')
    pe_description = fields.Char(related='pe_employee_id.description',string='Interpretations')
    pe_score = fields.Float('Score')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    appraisal_id = fields.Many2one('kin.appraisal',string='Appraisal')


class PerformanceEvaluation(models.Model):
    _name = 'kin.performance.evaluation'

    number = fields.Char('No.')
    name = fields.Char('Performance Level')
    description = fields.Char('Interpretations')
    pe_employee_id = fields.One2many('kin.performance.evaluation.employee','pe_employee_id',string='Performance Evaluation Employee')


class TrainingDevelopment(models.Model):
    _name = 'kin.training.development'

    career_development_goal = fields.Char('Career Development goal')
    training_needs_identified = fields.Char('Training Needs Identified')
    action_plan = fields.Char('Action Plan')
    time_frame = fields.Char('Time Frame')
    appraisal_id = fields.Many2one('kin.appraisal', string='Appraisal')

class HRAppraisal(models.Model):
    _name = 'kin.appraisal'

    review_period = fields.date(string='Review Period')
    employee_name = fields.Char(string='Name')
    employment_date = fields.Date('Date of Employment')
    grade_assumption_id = fields.Many2one('kin.grade',string='Grade on Assumption')
    date_confirmed = fields.Date('Date Confirmed')
    grade_spent_years = fields.Float(string='Years spent on present grade')
    present_grade_id = fields.Many2one('kin.grade',string='Present Grade')
    department_id = fields.Many2one('hr.department',string='Department')
    qualification_id = fields.Many2one('kin.qualification',string='Qualifications')
    qualification_gained = fields.Text(string='Qualification (certificates) gained during period')
    trainings = fields.Text(string='Course and training attended during the period')
    aggregate_total_score = fields.Float(string='100% AGGREGATE TOTAL SCORE BY THE HOD')
    kpi_employee_ids = fields.One2many('kin.kpi.employee','appraisal_id',string='KPI Employees')
    pae_employee_ids = fields.One2many('kin.personal.attribute.employee', 'appraisal_id', string='Personal Attributes Employees')
    pee_employee_ids = fields.One2many('kin.performance.evaluation.employee', 'appraisal_id', string='Performance Evaluation Employees')
    appraiser_comment = fields.Text('General comments by the appraising officer')
    is_promotion = fields.Boolean('Promotion to the next level')
    is_salary_review = fields.Boolean('Salary review')
    is_promotion_salary_review = fields.Boolean('Promotion and Salary review')
    is_action_deferment = fields.Boolean('Action deferment')
    appraiser_date = fields.Date('Appraiser Date')
    training_development_plan_ids = fields.One2many('kin.training.development', 'appraisal_id', string='Training and Development Plan')
    main_points_discussion = fields.Text('Main Points of the discussion (To be completed by the appraising officer)')
    employee_comment = fields.Text('Employee Comment')
    employee_date = fields.Date('Employee Date')
    appraiser_hod_comment = fields.Text('Comments of Appraising Officer (HOD)')
    appraiser_hod_date = fields.Date('Appraiser HOD Date')
    present_salary = fields.Float('Present Salary')
    last_increment_date = fields.Date('Last Increment Date')
    new_salary = fields.Float('New Salary')
    effective_date = fields.Date('Effective Date')
    comment_hr = fields.Text('HR Comment')
    comment_md = fields.Text('MD Comment')
    md_date = fields.Date('MD Date')
    appraisal_state = fields.Selection([('appraisee', 'Appraisee'), ('appraiser', 'Appraiser'),('hod','HOD'),('hr','HR'),('md','MD')],
                                         string='Appraisal Status')

