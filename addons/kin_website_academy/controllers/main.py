from openerp import http

class Academy(http.Controller):

    #The Routes using the converter pattern are used to MATCH the request url to the route url, then VALIDATE and CONVERT/CAST it to the specific converter #http://werkzeug.pocoo.org/docs/0.14/routing/#rule-format   and https://www.odoo.com/documentation/9.0/reference/http.html#routing
    #if the converter is not specified, then string converter is the default converter.
    #The auth parameter in the route, is used to define the page as publicly acceptable
    #the website param should be used when teh template references the website module.



    @http.route('/kin/academy/qweb',website=True,auth='user') # the auth='user', takes the user to the login page, if not yet logged in
    def qweb_section(self,**kw):
        my_password = http.request.session.password
        response = http.request.render('kin_website_academy.qweb_section',{'my_pass':my_password})
        return response


    @http.route('/kin/academy/teacher/<model("academy.teachers"):teacher_person>/',website=True,auth='public') # the route matches the request url to the route url, then accepts the teacher parameter in the placeholder, and then CAST/CONVERT the teacher param to a model
    def teacherb(self,teacher_person,**kw):

        return http.request.render('kin_website_academy.biography', {'person': teacher_person})




    #@http.route('/kin/academy/<name>/',auth='public') #if the converter is not specified, then string converter is the default converter.
    # OR
    @http.route('/kin/academy/<string():name>/', auth='public') #string converter is the default converter. see http://werkzeug.pocoo.org/docs/0.14/routing/#rule-format
    def teacher1(self,name):
        return '<h1>{}</h1>'.format(name)


    @http.route('/kin/academy/<int():int_val>/<int:val>/',auth='public')
    def teacher(self,**kw):
        return '<h1>{} ({})</h1>'.format(kw['int_val'],type(kw['int_val']).__name__)


    @http.route('/kin/academy',auth='public',website=True)
    def index(self,**kw):
        # 1) return http.request.render('kin_website_academy.index',{'teachers':['Kingsley','Chidozie','Okonkwo']})

        Teachers = http.request.env['academy.teachers']
        # 2.) return http.request.render('kin_website_academy.index', {'teachers': Teachers.search([])})
        return http.request.render('kin_website_academy.index1', {'teachers': Teachers.search([])})