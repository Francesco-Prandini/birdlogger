
from google.appengine.ext.webapp import template

import os.path
import webapp2
import logging

import DataLayer

import json
import geojson

import forms

import time
import datetime

from decimal import *

#authentication imports
import authentication
from webapp2_extras import sessions

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

#facebook login imports
import authomatic_config
from authomatic import Authomatic
from authomatic.adapters import Webapp2Adapter

#Image recognition import
import requests
import requests_toolbelt.adapters.appengine
from eightbit.client import EightbitApi
requests_toolbelt.adapters.appengine.monkeypatch()


#postCollection: struttura dati iterable contenente istanze __geo_interface__
#restituisce una stringa codificata in formato geoJson
def encode(postCollection):
    postList=[]
    for post in postCollection:
        postList.append(post)
    
    features=geojson.FeatureCollection(postList)
    result=geojson.dumps(features)
    
    return result
    pass


def imageLookup(imageFile):

    api = EightbitApi(apikey='bc96db50-b14a-478a-8d30-7907d0bbe02b')
    apiCallResult=api.tag_file(imageFile)

    result = []

    for element in apiCallResult['results']:
        result.append(str(element['tag']))
        pass

    return result
    pass

def isBird(tagsList):
    result=False
    for tag in tagsList:
        if 'bird' in tag or 'Bird' in tag:
            result = True
            break
            pass
    return result
    pass


class BaseHandler(webapp2.RequestHandler):
    """
        Classe handler di base contenente metodi di utili
        che vengono ereditati da tutti gli altri handler
    """


    def handle_exception(self, exception, debug):
        logging.exception(exception)

        if isinstance(exception, webapp2.HTTPException):
            self.renderError(self.response, exception)
        else:
            exception.code=500
            self.renderError(self.response, exception)

    def renderTemplate(self, filename, params={}):
        """
        Esegue il rendering di un template, in risposta a una richiesta html.
        :param filename: nome del file che contiene il template
        :param params: parametri con cui popolare il template
        """
        path = os.path.join(os.path.dirname(__file__), filename)
        self.response.out.write(template.render(path, params))
        pass
    @staticmethod
    def renderError(response, exception, message=None):
        """
        Presenta un messaggio di errore all'utente
        :param response: oggetto WebOb Response
        :param exception: errore che deve essere presentato all'utente
        :param message: messaggio di spiegazione della condizione di errore
        :return:
        """
        response.set_status(exception.code)
        if not message:
            printMessage=str(exception)
        else:
            printMessage=message
        response.out.write("An error occurred.<br><h1>"+str(exception.code)+" - "+str(printMessage)+"</h1>")
        pass

    def renderJSONError(self,exceptionCode, title,details=None):
        """
        Presenta un messaggio di errore in formato JSON
        :param exceptionCode: codice di errore
        :param title: condizione di errore
        :param details: dettagli aggiuntivi
        :return:
        """
        message = {"errors":
            [{
                "status": exceptionCode,
                "title": title,
            }]}
        if details!=None:
            message['errors'][0]['details']=details
            pass
        self.response.out.write(json.dumps(message))
        pass
    def renderForm(self, form, action, message=None, template=None):
        """
        Presenta una form html all'utente
        :param form: istanza della form (oggetto wtform.form.Form)
        :param action: azione a cui corrisponde la pressione del pulsante 'submit'
        :param message: messaggio aggiuntivo
        :param template: template da utilizzare per il rendering della form
        :return:
        """
        if message:
            form.message=message
        params = {'form': form, 'action': action}
        if not template:
            self.renderTemplate( 'templates/birdlogger/form.html', params)
        else:
            self.renderTemplate(template, params)
        pass

    def renderMessage(self,message):
        self.out.write("<h1>"+str(message)+"</h1>")
        pass

    @webapp2.cached_property
    def auth(self):
        return authentication.get_auth()

    @webapp2.cached_property
    def userModel(self):
        return self.auth.store.user_model

    def isUser(self):
        if not self.auth.get_user_by_session():
            return False
        return True
        pass

    def getUserId(self):
        #restituisce l'identificatore dell'entity del Datastore
        #associata all'utente autenticato nella sessione corrente

        user_id = self.auth.get_user_by_session()['user_id']
        #user = self.userModel.get_by_auth_id(auth_id)
        #user=DataLayer.getUser(user_id)
        return user_id
        pass

    def checkUserExistence(self, auth_id):
        #controlla se esiste un utente associato a un certo identificatore
        if not self.userModel.get_by_auth_id(auth_id):
            return False
        return True
        pass

    def createUser(self, auth_id, dataDict, password=None):
        """
        Crea un nuovo utente
        :param auth_id: Identificatore usato nella fase di login assieme alla password
        :param dataDict: dizionario contenente i dati dell'utente
        :param password: password in chiaro (memorizzata sotto forma di hash)
        :return:
        """

        tmpDict=dataDict.copy() #copia per evitare di modificare il dict originale

        if dataDict['email']:
            unique_properties = ['email']
            pass
        else:
            unique_properties = []
            pass

        if tmpDict.has_key('name'):
            tmpDict['userName'] = tmpDict.pop('name')
            tmpDict['firstName'] = tmpDict.pop('first_name')
            tmpDict['lastName'] = tmpDict.pop('last_name')
            pass

        return self.userModel.create_user(auth_id,
                                          unique_properties,
                                          **tmpDict)
        pass

    def checkUserCreation(self, userData):
        """
        Controlla che l'operazione di creazione di un nuovo utente sia andata a buon fine
        :param userData: tupla restituita dal metodo createUser
        :return:
        """
        if not userData[0]:
            nonUniqueFieldValues = []
            for i in userData[1]:
                nonUniqueFieldValues.append(i)
            self.renderMessage(self.response, 'user creation failed, these values were already used: ' + str(
                nonUniqueFieldValues))
        pass

    def checkUserHasPassword(self, auth_id):
        return self.userModel.get_by_auth_id(auth_id).hasPassword
        pass

    def login(self, auth_id, password=None):
        """
        Esegue il login di un utente
        :param auth_id: Identificatore dell'utente (l'email o il Facebook ID a seconda
            della procedura di autenticazione seguita)
        :param password: mancante nel caso dell'autenticazione tramite Facebook
        :return:
        """
        if password:
            return self.auth.get_user_by_password(auth_id, password, remember=True)
            pass
        else:
            return self.auth.login(auth_id, remember=True)
            pass
        pass

    def logout(self):
        self.auth.unset_session()
        pass

    @staticmethod
    def user_required(handler):
        #decorator che controlla che l'utente corrente sia stato autenticato
        def check_login(self, *args, **kwargs):
            if not self.auth.get_user_by_session():
                self.redirect('/login')
            else:
                return handler(self, *args, **kwargs)

        return check_login

    def dispatch(self):
        # esegue il dispatch della richiesta e tiene traccia della sessione
        # metodo richiesto dal modulo sessions di webapp2
        self.session_store = sessions.get_store(request=self.request)

        try:

            webapp2.RequestHandler.dispatch(self)
        finally:

            self.session_store.save_sessions(self.response)
        pass


class MapHandler(BaseHandler):
    """
    handler che si occupa delle richieste per la homepage
    """

    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'html'

        if self.isUser():

            self.renderTemplate("templates/birdlogger/authenticatedMain.html")
        else:
            self.renderTemplate("templates/birdlogger/main.html")
        
    def options(self):      
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'


class GeoDataHandler(BaseHandler):
    """
    gestisce le richieste per dati geografici corrispondenti a insiemi di post
    """
    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/geojson'

        fromDateString=self.request.get('fromDate')
        toDateString = self.request.get('toDate')

        try:
            if fromDateString != '':
                fromDateList=self.dateToList(fromDateString,'-')
                self.dateListCut(fromDateList)
                fromDate = datetime.datetime(*fromDateList)

            else:
                fromDate=None

            if toDateString != '':
                toDateList=self.dateToList(toDateString,'-')
                self.dateListCut(toDateList)
                toDate = datetime.datetime(*toDateList)
            else:
                toDate=None
            self.response.out.write(encode(DataLayer.getPostsFromTo(fromDate, toDate)))
        except ValueError as e:
            self.renderJSONError(400,'Malformed parameter','dates should be in the format YYYY-MM-DD[-h-m-s]')

    def dateToList(self, dateString, separator):
        dateList=dateString.split(separator)
        for i in range(0,len(dateList)):
            dateList[i]=int(dateList[i])
        return dateList
        pass

    def dateListCut(self, dateList):
        if len(dateList) > 5:
            for i in range(5,len(dateList)):
                del dateList[i]
        pass

# class clearDatabaseHandler(BaseHandler):
#     def get(self):
#         DataLayer.dropDatabase()
#         self.redirect("/")
#     pass
#
#
# class getAllUsersHandler(BaseHandler):
#     def get(self):
#          params={'usersList' : DataLayer.User.query().fetch(100)}
#          self.renderTemplate('show_users.html',params)
#     pass


class PostRetrieveHandler(BaseHandler):

    def get(self):
        """
        Risponde richieste per un singolo post identificato dal parametro postId, restituendo una pagina html
        :return:
        """
        params=DataLayer.getInfo(self.request.get("postId"))
        if(params):
            self.renderTemplate('templates/birdlogger/view_post.html',  params)
        else:
           self.abort(404)
        pass
    def getJSON(self):
        """
        Risponde a richieste per un singolo post identificato dal parametro postId, restituendo le informazioni
        corrispondenti in formato JSON
        :return:
        """
        postId=self.request.get("postId")

        if postId == '':
            self.renderJSONError(400,'Missing parameter postId')
            return

        if not postId.isdigit():
            self.renderJSONError(400, 'Malformed parameter postId')
            return

        post=DataLayer.getPostAndImage(postId)

        if not post:
            self.renderJSONError(404, 'File not found')
            return

        self.response.out.write(post)

        pass


    pass


class ImageDownloadHandler(BaseHandler):
    def get(self):
        """
        Gestisce le richieste di download di una singola immagine identificat adal parametro imageId.

        :return:
        """
        imageSet=DataLayer.getImageById(self.request.get("imgId"))
        
        if (imageSet):
            image=imageSet.bf
            self.response.headers['Content-Type'] = "image/jpeg"
            self.response.out.write(image)
        else:
            self.abort(404)

    def getJSON(self):
        imageId=self.request.get("imageId")

        if imageId == '':
            self.renderJSONError(400, 'Missing parameter imageId')
            return

        if not imageId.isdigit():
            self.renderJSONError(400, 'Malformed parameter imageId')
            return

        image=DataLayer.getImageById(imageId)

        if not image:
            self.renderJSONError(404, 'File not found')
            return

        self.response.out.write(image)

        pass

    pass

class PostCreationHandler(BaseHandler):
    """
     gestisce la procedura di creazione di un nuovo post
    """

    @BaseHandler.user_required
    def get(self):
        """
        presenta all'utente la form per la creazione di un nuovo post.
        :return:
        """
        latitude=self.request.get('lat')
        longitude=self.request.get('lng')

        form = forms.PostCreationForm()

        if latitude != '' and longitude != '':
            form.latitude.data=Decimal(latitude)
            form.longitude.data=Decimal(longitude)

        self.renderForm( form, '/post_upload')
        pass

    @BaseHandler.user_required
    def post(self):
        """
        crea un nuovo post con i parametri ricevuti in input dalla form
        :return:
        """
        form = forms.PostCreationForm(self.request.POST)
        if form.validate():
            lat = form.latitude.data
            lng = form.longitude.data
            postText = form.text.data
            userId = self.getUserId()

            species = form.species.data
            tags = form.tags.data
            pic = self.request.get('image')

            # crea nuovo post
            postId = DataLayer.insertPost(userId, lat, lng, postText)
            DataLayer.addImageToPost(postId, pic, species, tags)
            time.sleep(1)
            self.redirect('/')
        else:
            self.renderForm( form, '/post_upload')
        pass

    pass

class ApiDocsHandler(BaseHandler):
    def get(self):
        self.renderTemplate( "templates/birdlogger/birdlogger_api.html")
        pass
    pass

class ImageRecognitionHandler(BaseHandler):
    @BaseHandler.user_required
    def get(self):
        form = forms.ImageRecognitionForm()
        self.renderForm( form, '/image_recognition')
        pass

    @BaseHandler.user_required
    def post(self):
        form = forms.ImageRecognitionForm(self.request.POST)
        if form.validate():
            pic=self.request.get('image')
            try:
                tagsList = imageLookup(pic)
                #self.renderForm( form, '/image_recognition', message='Tags suggestions: ' + str(tagsList))
                if isBird(tagsList):
                    message='These are the most likely tags for your image:'
                else:
                    message='Are you sure this image contains a bird?'
                params = {
                    'message' : message,
                    'itemsList' : tagsList,
                    'form' : form
                }

                self.renderTemplate('templates/birdlogger/BirdRecognitionResponse.html', params)
            except Exception as e:
                self.renderForm( form, '/image_recognition', message='Process Failed! Retry in a few minutes...')

            pass
        else:
            self.renderForm( form, '/image_recognition')
        pass

    pass

# class AuthenticationHandler(BaseHandler):
#     def checkUserExistence(self, auth_id):
#         if not self.userModel.get_by_auth_id(auth_id):
#             return False
#         return True
#         pass
#
#     def createUser(self, auth_id, dataDict, password=None):
#
#         tmpDict=dataDict.copy() #copia per evitare di modificare il dict originale
#
#         if dataDict['email']:
#             unique_properties = ['email']
#             pass
#         else:
#             unique_properties = []
#             pass
#
#         if tmpDict.has_key('name'):
#             tmpDict['userName'] = tmpDict.pop('name')
#             tmpDict['firstName'] = tmpDict.pop('first_name')
#             tmpDict['lastName'] = tmpDict.pop('last_name')
#             pass
#
#         return self.userModel.create_user(auth_id,
#                                           unique_properties,
#                                           **tmpDict)
#         pass
#
#     def checkUserCreation(self, userData):
#         if not userData[0]:
#             nonUniqueFieldValues = []
#             for i in userData[1]:
#                 nonUniqueFieldValues.append(i)
#             self.renderMessage(self.response, 'user creation failed, these values were already used: ' + str(
#                 nonUniqueFieldValues))
#         pass
#
#     def checkUserHasPassword(self, auth_id):
#         return self.userModel.get_by_auth_id(auth_id).has_password
#         pass
#
#     def login(self, auth_id, password=None):
#         if password:
#             return self.auth.get_user_by_password(auth_id, password, remember=True)
#             pass
#         else:
#             return self.auth.login(auth_id, remember=True)
#             pass
#         pass
#     pass

class SignupHandler(BaseHandler):
    """
    gestisce la procedura di registrazione per un nuovo utente
    """
    def get(self):
        """
        presenta all'utente la form di registrazione
        :return:
        """
        form = forms.SignupForm()
        self.renderForm( form, '/signup')
        pass

    def post(self):
        """
        crea un nuovo utente con i parametri ottenuti in input dalla form
        :return:
        """
        form=forms.SignupForm(self.request.POST)
        if form.validate():

            data={}
            data['userName']=form.userName.data
            data['email'] = form.email.data
            data['password_raw'] = form.password.data
            data['hasPassword'] = True
            data['firstName'] = form.firstName.data
            data['lastName'] = form.lastName.data

            userData = self.createUser(data['email'], data)


            self.checkUserCreation(userData)
            self.redirect('/')
            pass
        else:
            self.renderForm( form, '/signup')
            pass
        pass
    pass

class LoginHandler(BaseHandler):
    """
    gestisce la procedura di login di un utente registrato
    """
    def get(self):
        form = forms.LoginForm()
        self.renderForm( form, '/login',template='templates/birdlogger/loginForm.html')
        pass

    def post(self):
        """
        crea un nuovo utente
        :return:
        """
        form=forms.LoginForm(self.request.POST)
        if form.validate():
            try:
                if self.checkUserExistence(form.email.data):
                    if not self.checkUserHasPassword(form.email.data):
                        self.renderForm( form, '/login', 'user without password... log in with facebook')
                        return

                self.login(form.email.data, form.password.data)
                self.redirect('/')
            except (InvalidAuthIdError, InvalidPasswordError) as e:
                logging.info('Login failed for user %s because of %s', form.email.data, type(e))
                self.renderForm(self.response, form, '/login', 'Login Failed!')

            pass
        else:
            self.renderForm( form, '/login')
            pass
        pass
    pass


class LogoutHandler(BaseHandler):
    def get(self):
        """
        esegue il logout dell'utente corrente
        :return:
        """
        self.logout()
        self.redirect('/')
    pass
# class ModifyInfoHandler(BaseHandler):
#     @user_required
#     def get(self):
#         form = forms.modifyInfoForm(data=self.user_info)
#         self.renderForm(self.response, form, '/modify_info')
#         pass
#     @user_required
#     def post(self):
#         form=forms.modifyInfoForm(self.request.POST)
#         if form.validate():
#             userName=self.request.get('userName')
#             email=self.request.get('email')
#             password=self.request.get('password')
#             unique_properties = ['email']
#             userData=self.user_model.create_user(userName, unique_properties,userName=userName,
#                                         email=email, password_raw=password)
#
#             if not userData[0]:
#                 #soluzione non soddisfacente, da rivedere
#                 nonUniqueFieldValues=[]
#                 for i in userData[1]:
#                     if i == 'auth_id':
#                         nonUniqueFieldValues.append('username')
#                     else:
#                         nonUniqueFieldValues.append(i)
#                 form.message='user creation failed, these values were already used: '+str(nonUniqueFieldValues)
#                 self.renderForm(self.response, form, '/modify_info')
#                 return
#             else:
#                 #debug
#                 time.sleep(1)
#                 params={'usersList' : DataLayer.User.query().fetch(100)}
#                 self.renderTemplate(self.response,'show_users.html',params)
#             pass
#         else:
#             self.renderForm(self.response, form, '/signup')
#             pass
#         pass
#     pass

#funzioni di gestione per le HttpExceptions


class FacebookLoginHandler(BaseHandler):
    """
    gestisce la procedura di autenticazione tramite facebook
    """
    def any(self):
        """
        Autentica un utente tramite il suo account facebook.
        Se e' la prima volta che l'utente accede tramite facebook, viene creato un nuovo oggetto User
        per memorizzare i suoi dati.
        (per il corretto funzionamento della libreria authomatic,
        il metodo deve accettare sia richieste GET che POST)
        :return:
        """
        result = authomatic.login(Webapp2Adapter(self),'facebook')

        if result:
            if result.error:
                self.renderMessage( result.error.message)
                pass
            elif result.user:
                if not (result.user.name and result.user.id):
                    result.user.update()

                if result.user.credentials:
                    url = self.buildApiUrl(result.user.id, result.user.credentials.token)
                    response = result.provider.access(url)

                    if response.status == 200:
                        data = response.data
                        if not self.checkUserExistence(data['id']):
                            userData = self.createUser(data['id'], data)
                            self.checkUserCreation(userData)
                            pass
                        try:
                            time.sleep(1)
                            self.login(data['id'])
                            self.redirect('/')
                        except (InvalidAuthIdError, InvalidPasswordError) as e:
                            logging.info('Login failed for user %s because of %s', data['name'], type(e))
                            self.renderMessage('Login failed!')

                    pass

        pass

    def buildApiUrl(self, id, accessToken):
        url = 'https://graph.facebook.com/v2.8/'
        return url + id + '?access_token' + accessToken + '&fields=id,name,email,first_name,last_name'
        pass


def handle_400(request, response, exception):
    logging.exception(exception)
    BaseHandler.renderError(response, exception, 'Error')

def handle_401(request, response, exception):
    logging.exception(exception)
    BaseHandler.renderError(response, exception, 'Seems like you should not be here')

def handle_404(request, response, exception):
    logging.exception(exception)
    BaseHandler.renderError(response, exception, 'The page you are searching does not exists')

def handle_500(request, response, exception):
    logging.exception(exception)
    exception.code=500
    BaseHandler.renderError(response, exception, str(exception))

config = {
             'webapp2_extras.auth': {
                 'user_model': 'DataLayer.User',
                 'user_attributes': ['userName', 'email']
             },
             'webapp2_extras.sessions': {
                 'secret_key': '#########'
             }
         }

authomatic = Authomatic(config=authomatic_config.config,
                        secret=authomatic_config.SECRET,
                        report_errors=True,
                        logging_level=logging.DEBUG)

app = webapp2.WSGIApplication([
    webapp2.Route('/', MapHandler),
    webapp2.Route('/signup', SignupHandler),
    webapp2.Route('/login', LoginHandler),
    webapp2.Route('/fb_login', FacebookLoginHandler, handler_method='any'),
    #('/modify_info', ModifyInfoHandler),
    webapp2.Route('/logout', LogoutHandler),
    webapp2.Route('/post',  PostRetrieveHandler),
    webapp2.Route('/post_upload', PostCreationHandler),
    webapp2.Route('/image_recognition', ImageRecognitionHandler),
    webapp2.Route('/image_download', ImageDownloadHandler),
    webapp2.Route('/data.json', GeoDataHandler),
    webapp2.Route('/api/1.0/', ApiDocsHandler),
    webapp2.Route('/api/1.0/geodata', GeoDataHandler),
    webapp2.Route('/api/1.0/post', PostRetrieveHandler, handler_method='getJSON'),
    webapp2.Route('/api/1.0/image', ImageDownloadHandler, handler_method='getJSON'),
    #webapp2.Route('/clear', clearDatabaseHandler),
    #webapp2.Route('/users', getAllUsersHandler)
 ], debug=True, config=config)



app.error_handlers[400] = handle_400
app.error_handlers[401] = handle_401
app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500