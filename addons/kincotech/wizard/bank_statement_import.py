


import csv
import base64
import StringIO
from datetime import datetime
# import pytz
# from openerp import SUPERUSER_ID
# from dateutil.relativedelta import relativedelta
# from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
# from operator import itemgetter
from openerp.tools.translate import _
# from openerp import netsvc
from openerp import models, fields, api
from openerp.exceptions import ValidationError

class BankStatementImport(models.TransientModel):
    _name = 'bank.statement.import'
    _description = 'Bank Statement Import'
        
    input_file = fields.Binary('Import CSV File', required=True)
 
    
    def bank_statement_import_btn(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        bank_stmt_id = context.get('active_id',False)
        
        bank_statement_line_obj = self.pool.get('account.bank.statement.line')
#         delIDS = bank_statement_line_obj.search(cr,uid,[])
#         bank_statement_line_obj.unlink(cr,uid,delIDS,context=context) # Empty the table first
         
        total_import = 0
        # reference: ../attendance_import/attendance_import.py from mattobell
        for line in self.browse(cr, uid, ids, context=context):
            bb = base64.decodestring (line.input_file)            
            sttr = StringIO.StringIO(bb)
            lines = csv.reader(StringIO.StringIO(base64.b64decode(line.input_file)), delimiter=';',)  
            for i in range(0,17) :
                header = lines.next()
            for ln in lines:
                line_value = dict(zip(header, ln))
                if line_value:
                    #ch_date = line_value['Transaction Date'].split(' AM')[0].split(' PM')[0]#split AM,PM
                    
                    ref_no = line_value['Reference No.'].strip("'")
                    transaction_date = datetime.strptime(line_value['Transaction Date'],'%d-%b-%y').strftime('%Y-%m-%d')
                    description = line_value['Description ']                 
                    
                    #reference: by Tim Pietzcker at http://stackoverflow.com/questions/6609895/efficiently-replace-bad-characters
                    deposit = line_value['Deposit'].encode("ascii", "ignore").strip().replace(",","").strip().strip('"')
                    withdrawal = line_value['Withdrawal'].encode("ascii", "ignore").replace(",","").strip('",').strip()
                        
                    rec = bank_statement_line_obj.search(cr,uid,[('ref','=',ref_no),('date','=',transaction_date),('name','=',description),('amount','=',deposit),('amount','=',withdrawal)])
                    if rec != []:
                        raise ValidationError(_('It seems the bank statement line has already been imported for Reference No. "%s" and Transaction Date "%s"  !') % (line_value['Reference No.'], transaction_date))
                  
                    else :
                        amount = 0
                        
#                         deposit = line_value['Deposit'].strip('"').strip()
#                         withdrawal = line_value['Withdrawal'].strip('",').strip()
                        
                        if len(withdrawal) != 0 :                            
                            amount = -float(withdrawal) 
                        
                        if len(deposit) != 0 :
                            ans = repr(deposit)
                            amount = float(deposit) 
                        
                        if len(deposit) != 0 or len(withdrawal) != 0 : 
                            bank_statement_line_obj.create(cr, uid, {
                                    'date': line_value['Transaction Date'],
                                    'name': line_value['Description '],
                                    'ref': ref_no,
                                    'amount':amount,                               
                                    'statement_id': bank_stmt_id,
                                })
  
                            #self.write(cr,uid,[bank_stmt_id],{'input_file':line.input_file},context=context)    
        return 
             
    
