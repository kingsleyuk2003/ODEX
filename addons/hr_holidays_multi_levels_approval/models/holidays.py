#-*- coding:utf-8 -*-

from openerp import models, fields, api
from urllib import urlencode
from urlparse import urljoin
from datetime import datetime, time, timedelta
from openerp.exceptions import UserError

class Holidays(models.Model):
    _name = "hr.holidays"
    _inherit = "hr.holidays"


    def _default_approver(self):
        employee = self.env['hr.employee'].browse(self._employee_get())
        if employee.holidays_approvers:
            return employee.holidays_approvers[0].approver.id

    # In case of ERROR , during installation, just remove the default=_default_approver, then install again.
    # then after installation, put (default=_default_approver it back on the following code and reinstall again.
    pending_approver = fields.Many2one('hr.employee', string="Pending Approver", readonly=True, default=_default_approver)
    pending_approver_user = fields.Many2one('res.users', string='Pending approver user', related='pending_approver.user_id', related_sudo=True, store=True, readonly=True)
    current_user_is_approver = fields.Boolean(string= 'Current user is approver', compute='_compute_current_user_is_approver')
    approbations = fields.One2many('hr.employee.holidays.approbation', 'holidays', string='Approvals', readonly=True)
    pending_transfered_approver_user = fields.Many2one('res.users', string='Pending transfered approver user', compute="_compute_pending_transfered_approver_user", search='_search_pending_transfered_approver_user')

    @api.multi
    def holidays_refuse(self):
        return  {
             'name': 'Confirm Leave Request Disapproval',
              'view_mode': 'form',
             'view_type': 'form',
             'res_model': 'leave.request.disapprove.wizard',
             'type': 'ir.actions.act_window',
             'target': 'new'
            }

    
    @api.multi
    def holidays_confirm(self):
        res = super(Holidays, self).holidays_confirm()
        approver = False
        requester = self.employee_id.user_id
        for holiday in self:
            if self.type == 'add':
                hr_officer_approver = self.env.user.company_id.leave_allocation_approver_id
                if not hr_officer_approver:
                    raise UserError('Please contact the IT administrator to set the default Human Resources Leave Allocation Approver in the company settings  ')
                if not hr_officer_approver.user_id :
                    raise UserError('Human Resources Leave Allocation Approver is not related to any user in the system')
                holiday.pending_approver = approver = hr_officer_approver
            elif  holiday.employee_id.holidays_approvers :
                holiday.pending_approver = approver = holiday.employee_id.holidays_approvers[0].approver

        if requester and approver:
            self.send_email(requester, approver,final_approval=False)
        return res


    def _get_final_url(self, module_name, menu_id, action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name, menu_id)[1]
        fragment['model'] = 'hr.holidays'
        fragment['view_type'] = 'form'
        fragment['action'] = model_data.get_object_reference(module_name, action_id)[1]
        query = {'db': self.env.cr.dbname}
        # for displaying tree view. Remove if you want to display form view
        #         fragment['page'] = '0'
        #         fragment['limit'] = '80'
        #         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


        # For displaying a single record. Remove if you want to display tree view
        fragment['id'] = context.get("holiday_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res

    def _get_url(self, module_name, menu_id, action_id, context=None):
        fragment = {}
        res = {}
        model_data = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fragment['menu_id'] = model_data.get_object_reference(module_name, menu_id)[1]
        fragment['model'] = 'hr.holidays'
        fragment['view_type'] = 'form'
        fragment['action'] = model_data.get_object_reference('hr_holidays_multi_levels_approval', action_id)[1]
        query = {'db': self.env.cr.dbname}
        # for displaying tree view. Remove if you want to display form view
        #         fragment['page'] = '0'
        #         fragment['limit'] = '80'
        #         res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))


        # For displaying a single record. Remove if you want to display tree view
        fragment['id'] = context.get("holiday_id")
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res


    def send_email(self,requester,approver,final_approval=False):

        company_email = self.env.user.company_id.email and self.env.user.company_id.email.strip() or False
        requester_email = requester.email and requester.email or False
        approver_email = approver.user_id and approver.user_id.email or False
        if requester_email and approver_email and company_email and not final_approval:
            # Custom Email Template
            mail_template = self.env.ref('hr_holidays_multi_levels_approval.mail_templ_leave_approval')
            ctx = {}
            ctx.update({'holiday_id': self.id})
            the_url = self._get_url('hr_holidays', 'menu_open_department_leave_approve', 'open_holidays_approve', ctx)
            ctx = {'system_email': company_email,
                    'requester_email': requester_email,
                    'approver_email' : approver_email,
                    'requester_name': self.employee_id.name,
                    'approver_name': approver.name,
                    'url': the_url,
                }
            mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        elif requester_email and approver_email and company_email and final_approval and self.date_from and self.date_to:
            mail_template = self.env.ref('hr_holidays_multi_levels_approval.mail_templ_leave_final_approval')
            ctx = {}
            ctx.update({'holiday_id': self.id})
            the_url = self._get_final_url('hr_holidays', 'menu_hr_holidays_my_leaves', 'open_ask_holidays', ctx)
            ctx = {'system_email': company_email,
                   'requester_email': requester_email,
                   'approver_email': approver_email,
                   'requester_name': self.employee_id.name,
                   'approver_name': approver.name,
                   'url': the_url,
                   'date_from' : datetime.strptime(self.date_from,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S'),
                   'date_to' : datetime.strptime(self.date_to,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
                   }
            mail_template.with_context(ctx).send_mail(self.id, force_send=False)


    @api.multi
    def action_approve(self):
        for holiday in self:

            is_last_approbation = False
            sequence = 0
            next_approver = None
            for approver in holiday.employee_id.holidays_approvers:
                sequence = sequence + 1
                if holiday.pending_approver.id == approver.approver.id:
                    if sequence == len(holiday.employee_id.holidays_approvers):
                        is_last_approbation = True
                        next_approver = approver.approver
                    else:
                        next_approver = holiday.employee_id.holidays_approvers[sequence].approver

            if is_last_approbation or self.type == 'add':
                holiday.action_validate()
            else:
                holiday.write({'state': 'confirm', 'pending_approver': next_approver.id})
                self.env['hr.employee.holidays.approbation'].create({'holidays': holiday.id, 'approver': self.env.uid, 'sequence': sequence, 'date': fields.Datetime.now()})

            requester =  self.employee_id.user_id
            approver = next_approver and next_approver.user_id
            if requester and approver and not is_last_approbation :
                self.send_email(requester, approver,final_approval=False)
            elif requester and approver and is_last_approbation :
                self.send_email(requester, approver,final_approval=True)
        return

    @api.multi
    def action_disapprove(self, msg):
        super(Holidays, self).holidays_refuse()
        reason_for_dispproval = msg

        # Send Email
        company_email = self.env.user.company_id.email.strip()
        approver_email = self.env.user.partner_id.email.strip()

        if self.type == 'add':
            requester_email = False
        else:
            requester_email = self.employee_id.user_id.email.strip()


        if company_email and approver_email and not self.type == 'add':
            # Custom Email Template
            mail_template = self.env.ref('hr_holidays_multi_levels_approval.mail_templ_leave_disapproval')
            ctx = {}
            ctx.update({'holiday_id': self.id})
            the_url = self._get_final_url('hr_holidays', 'menu_hr_holidays_my_leaves', 'open_ask_holidays', ctx)
            ctx = {'system_email': company_email,
                   'requester_email': requester_email,
                   'approver_email': approver_email,
                   'requester_name': self.employee_id.name,
                   'approver_name': self.env.user.name,
                   'url': the_url,
                   'reason_for_dispproval': reason_for_dispproval,
                   'date_from': datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S'),
                   'date_to': datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
                   }
            mail_template.with_context(ctx).send_mail(self.id, force_send=False)
        else:
            self.message_post('Leave Allocation Rejection Reason: %s.' % (reason_for_dispproval),
                                      subject='Leave Allocation Rejection Reason',
                                      subtype='mail.mt_comment')
        return

    @api.multi
    def action_validate(self):
        self.write({'pending_approver': None})
        for holiday in self:
            self.env['hr.employee.holidays.approbation'].create({'holidays': holiday.id, 'approver': self.env.uid, 'date': fields.Datetime.now()})
        super(Holidays, self).holidays_validate()

    
    @api.one
    def _compute_current_user_is_approver(self):
        if self.pending_approver.user_id.id == self.env.user.id or self.pending_approver.transfer_holidays_approvals_to_user.id == self.env.user.id :
            self.current_user_is_approver = True
        else:
            self.current_user_is_approver = False
    
    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.employee_id and self.employee_id.holidays_approvers:
            self.pending_approver = self.employee_id.holidays_approvers[0].approver.id
        else:
            self.pending_approver = False
            
    @api.one
    def _compute_pending_transfered_approver_user(self):
        self.pending_transfered_approver_user = self.pending_approver.transfer_holidays_approvals_to_user
    
    def _search_pending_transfered_approver_user(self, operator, value):
        replaced_employees = self.env['hr.employee'].search([('transfer_holidays_approvals_to_user', operator, value)])
        employees_ids = []
        for employee in replaced_employees:
            employees_ids.append(employee.id)
        return [('pending_approver', 'in', employees_ids)]






class ResCompanyExtend(models.Model):
    _inherit = "res.company"

    leave_allocation_approver_id = fields.Many2one('hr.employee',string='Human Resources Leave Allocation Approver', help="The hr officer who approves leave allocations")

    