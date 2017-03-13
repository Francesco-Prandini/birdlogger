import requests
import requests_toolbelt.adapters.appengine
#import webapp2
from os.path import basename


class Client:
	token = None

	def __init__(self, client_id=None, client_secret=None):
		'''Initialize the 'Blippar Vision API' Client object, '''
		''' if id and secret parameters are not passed,'''
		''' default params set in the class will be used.'''
		self.client_id = client_id or Client._client_id
		self.client_secret = client_secret or Client._client_secret

	@classmethod
	def init(cls, client_id, client_secret):
		'''Initialize the 'Blippar Vision API' Client class in the App with the id and secret'''
		cls._client_id = client_id
		cls._client_secret = client_secret

	def get_token(self, grant_type=None, client_id=None, client_secret=None, load=None):
		params = {
			'grant_type': grant_type or 'client_credentials',
			'client_id': client_id or self.client_id,
			'client_secret': client_secret or self.client_secret
		}
		token = self.get('https://bauth.blippar.com/token', data=params, auth=False)
		if load or load is None:
			self.token = token.json()
		return token

	def get(self, url, data=None, auth=None):
		'''Internal method for quickly make an API:GET request to a specified URL'''
		param_headers = {}
		if auth or auth is None:
			param_headers['Authorization'] = "{} {}".format(self.token['token_type'], self.token['access_token'])
		return requests.get(url, params=data, headers=param_headers)

	def post(self, url, data=None, files=None, auth=None):
		'''Internal method for quickly make an API:POST request to a specified URL'''
		param_headers = {}
		if auth or auth is None:
			param_headers['Authorization'] = "{} {}".format(self.token['token_type'], self.token['access_token'])
		return requests.post(url, data=data, files=files, headers=param_headers)

	def image_lookup(self, image_content, image_type=None):
		'''POST	/v1/imageLookup'''
		param_files = [('input_image', ('image', image_content, image_type or 'image/png'))]
		return self.post('https://bapi.blippar.com/v1/imageLookup', files=param_files)


#	def image_lookup(self, image_path, image_type=None):
#		'''POST	/v1/imageLookup'''
#		param_files = [
#			('input_image', (basename(image_path), open(image_path, 'rb'), image_type or 'image/png'))
#		]
#		return self.post('https://bapi.blippar.com/v1/imageLookup', files=param_files)

requests_toolbelt.adapters.appengine.monkeypatch()
Client.init('7d2c5bbd39944c39b72175ab1ff27d39', '3bba562aac874b529e4b8a85b3d6bad6')

c = Client()
##x1=c.get_token()
##print(x1.json())
#
#x2 = c.image_lookup('/home/francesco/Scrivania/test_set_image_recognition/gazza.jpg')
#print(x2.json())
