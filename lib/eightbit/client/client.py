import os
import logging
import requests
import json
from StringIO import StringIO

try:
  from PIL import Image
  CAN_RESIZE = True
except ImportError:
  CAN_RESIZE = False
  print ('It is recommended to install PIL/Pillow with the desired image format support so that '
         'image resizing to the correct dimesions will be handled for you. '
         'If using pip, try "pip install Pillow"')


# set logging level
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

VERSION = 'v0.02'
IGNORE_FORMATS = ['GIF']  # these formats will not be resized.
IMG_QUALITY = 90
BASE_URL = "http://api.8bit.ai"

class EightbitApi(object):

    def __init__(self, apikey=None, wait_on_burst=True, lang=None):
        """
          Create a client object to send API requests

          Inputs:
            apikey        : APIKEY obtained for your application. If you don't
                            have one visit 8bit.ai.
            wait_on_burst : Wait the API server until it reponds.
            lang          : Language setting for API. It is eng by default.
        """

        if not apikey:
            self.APIKEY = os.environ.get('EIGHTBIT_APIKEY', None)
        else:
            self.APIKEY = apikey

        self.wait_on_burst = wait_on_burst
        self.LANG = self._sanitize_param(lang)
        self._urls = {
            'tag': '/'.join([BASE_URL, 'tag']),
            'fdet': '/'.join([BASE_URL, 'fdet']),
            'lmdet': '/'.join([BASE_URL, 'lmdet']),
            'hash': '/'.join([BASE_URL, 'hash']),
            'useinfo': '/'.join([BASE_URL, 'useinfo']),
            'quota': '/'.join([BASE_URL, 'quota']),
            'bandwidth': '/'.join([BASE_URL, 'bandwidth'])
        }
        self.api_info = self.get_useinfo()['results']

    def get_useinfo(self):
        """
            Get various information and constraints regarding the use of API.
        """
        url = self._urls['useinfo']
        data = {
            'apikey': self.APIKEY,
        }
        ans = self._request(url,data)
        return ans


    def get_quota(self):
        '''
            Get all related Quota information regarding user account
        '''
        url = self._urls['quota']
        data = {
            'apikey': self.APIKEY,
        }
        ans = self._request(url,data)
        return ans

    def get_bust_wait_time(self):
        '''
            Get burst wait time for the next call
        '''
        url = self._urls['bandwidth']
        data = {
            'apikey': self.APIKEY,
        }
        ans = self._request(url,data)
        return ans

    def tag_url(self, img_url, modelkey='concept'):
        '''
            Given image url retrieve tagging results

            Inputs:
              img_url   : web url for a publcly accessible image
              modelkey  : model name to be used for tagging.

            Example output:

              {u'code': 200,
               u'massage': u'OK',
               u'request_id': u'5765cf126c64b7fc0b5da9b0',
               u'results': [{u'score': 0.40961283445358276, u'tag': u'face', u'tagid': 671},
                {u'score': 0.10252203792333603, u'tag': u'male', u'tagid': 1404},
                {u'score': 0.09483663737773895, u'tag': u'young buck', u'tagid': 1443},
                {u'score': 0.0276748389005661, u'tag': u'eurasian', u'tagid': 10438},
                {u'score': 0.027616096660494804, u'tag': u'complexion', u'tagid': 1908}]}

        '''
        url = self._urls['tag']
        data = {
            'url': img_url,
            'apikey': self.APIKEY,
            'modelkey': modelkey
        }
        ans = self._request(url, data)
        return ans


    def tag_file(self, img, modelkey='concept'):
        '''
            Given local image path retrieve tagging results

            Inputs:
              img_path   : local file path for a publcly accessible image
              modelkey   : model name to be used for tagging.

            Example output:

              {u'code': 200,
               u'massage': u'OK',
               u'request_id': u'5765cf126c64b7fc0b5da9b0',
               u'results': [{u'score': 0.40961283445358276, u'tag': u'face', u'tagid': 671},
                {u'score': 0.10252203792333603, u'tag': u'male', u'tagid': 1404},
                {u'score': 0.09483663737773895, u'tag': u'young buck', u'tagid': 1443},
                {u'score': 0.0276748389005661, u'tag': u'eurasian', u'tagid': 10438},
                {u'score': 0.027616096660494804, u'tag': u'complexion', u'tagid': 1908}]}
        '''
        url = self._urls['tag']
        #img = open(img_path,'rb')
        img = self._correct_img_for_api([img])[0]
        files = {
            'file': img,
        }
        data = {
            'apikey': self.APIKEY,
            'modelkey': modelkey
        }
        ans = self._request(url, data, files)
        #img.close()
        return ans

    def fdet_url(self, img_url):
        '''
            Given image url retrieve bounding box locations
            for the detected faces.

            Inputs:
              img_url   : web url for a publcly accessible image

            Example output:

              {u'code': 200,
               u'massage': u'OK',
               u'request_id': u'5765cf6d6c64b7fc0b5da9b1',
               u'results': [{u'x1': 13.0,
                 u'x2': 87.33333333333333,
                 u'y1': 0.35625,
                 u'y2': 1.053125}]}
        '''
        url = self._urls['fdet']
        data = {
            'url': img_url,
            'apikey': self.APIKEY,
        }
        ans = self._request(url, data)
        return ans

    def fdet_file(self, img_path):
        '''
            Given local image path retrieve bounding box locations
            for the detected faces.

            Inputs:
              img_path   : local file path for a publcly accessible image

            Example output:

              {u'code': 200,
               u'massage': u'OK',
               u'request_id': u'5765cf6d6c64b7fc0b5da9b1',
               u'results': [{u'x1': 13.0,
                 u'x2': 87.33333333333333,
                 u'y1': 0.35625,
                 u'y2': 1.053125}]}
        '''
        url = self._urls['fdet']
        img = open(img_path,'rb')
        img = self._correct_img_for_api([img])[0]
        files = {
            'file': img,
        }
        data = {
            'apikey': self.APIKEY,
        }
        ans = self._request(url, data, files)
        img.close()
        return ans


    def lmdet_url(self, img_url):
        '''
            Given image url retrieve  bounding box locations
            for the detected faces and x,y locations for the
            detected face landmarks.

            Inputs:
              img_url   : web url for a publcly accessible image

            Example output:

              {u'code': 200,
               u'massage': u'OK',
               u'request_id': u'5765cf6d6c64b7fc0b5da9b1',
               u'results': [{u'x1': 13.0,
                 u'x2': 87.33333333333333,
                 u'y1': 0.35625,
                 u'y2': 1.053125}]}
        '''
        url = self._urls['lmdet']
        data = {
            'url': img_url,
            'apikey': self.APIKEY,
        }
        ans = self._request(url, data)
        return ans

    def lmdet_file(self, img_path):
        '''
            Given local image path bounding box locations
            for the detected faces and  x,y locations for the
            detected face landmarks. Algorithm detects faces and
            returns left eye (le), right eye (re), nose (no), left mouth (lm),
            right mouth (rm) locations.

            Inputs:
              img_path   : local file path for a publcly accessible image

            Example output:

              {u'code': 200,
                 u'massage': u'OK',
                 u'request_id': u'576be59f6c64b716fb3d6c4f',
                 u'results': [{u'img_height': 180,
                   u'img_width': 262,
                   u'le_x': 80.44068613052369,
                   u'le_y': 50.54854381084442,
                   u'lm_x': 75.685422205925,
                   u'lm_y': 74.6451919555664,
                   u'no_x': 92.82889728546144,
                   u'no_y': 68.01604690551758,
                   u're_x': 106.5858850479126,
                   u're_y': 54.67236037254333,
                   u'rm_x': 102.76025180816652,
                   u'rm_y': 79.13337917327881,
                   u'x1': 71.0,
                   u'x2': 112.0,
                   u'y1': 47.0,
                   u'y2': 89.0}]}
        '''
        url = self._urls['lmdet']
        img = open(img_path,'rb')
        img = self._correct_img_for_api([img])[0]
        files = {
            'file': img,
        }
        data = {
            'apikey': self.APIKEY,
        }
        ans = self._request(url, data, files)
        img.close()
        return ans

    def hash_url(self, img_url):
        '''
            Given image url retrieve hash values that can be used
            for near-duplicate matching. It returns binary and hex
            versions of the same hash value.

            Inputs:
              img_url   : web url for a publcly accessible image
        '''
        url = self._urls['hash']
        data = {
            'url': img_url,
            'apikey': self.APIKEY,
        }
        ans = self._request(url, data)
        return ans

    def hash_file(self, img_path):
        '''
            Given local image path retrieve hash values that can be used
            for near-duplicate matching. It returns binary and hex
            versions of the same hash value.

            Inputs:
              img_path   : local file path for a publcly accessible image
        '''
        url = self._urls['hash']
        img = open(img_path,'rb')
        img = self._correct_img_for_api([img])[0]
        files = {
            'file': img,
        }
        data = {
            'apikey': self.APIKEY,
        }
        ans = self._request(url, data, files)
        img.close()
        return ans

    def hash_similarity(self, h1, h2):
        """
          Given two hash values compute the distance. It returns a similarity
          value between 0 and 1 and 1 means the same and 0 means nothing similar.
          Possible threshold for detecting near duplicate images is 0.8. However,
          set the best threshold by experimenting.

          Inputs:
            h1  : result dictionary or binary hash value returned by hashing function
            h2  : result dictionary or binary hash value returned by hashing function

          Output:
            similarity  : similarity value between 0 and 1

          Example output:
            c = EightbitApi(apikey='...')
            // call hash API call
            r = c.hash_file('image/path.jpg')
            // obtain binary hash values as a python list
            h = r['results'][0]['binary']
            // compute distance
            c.hash_distance(h,h)
            -> 0.1
        """

        if type(h1) is dict:
            h1 = h1['results'][0]['binary']
        if type(h2) is dict:
            h2 = h2['results'][0]['binary']

        num_same = 0
        for c, b in enumerate(h1):
          if b == h2[c]:
            num_same += 1
        return num_same/64.0

    def _request(self, url, data, files=None):
        '''
            Send post request and decode returned json python dict
        '''
        if files:
            r = requests.post(url, files=files, data=data)
        else:
            r = requests.post(url, data)
        try:
            ans = json.loads(r.text)
        except ValueError:
            ans  = "Shame :((( .. Unknown return from server!"
        return ans


    def _sanitize_param(self, param, default=''):
      """Convert parameters into a form ready for the wire."""
      if param:
        # Can't send unicode. If it can't encode it as ascii something is wrong with this string
        try:
          param = param.encode('ascii')
        except UnicodeDecodeError:
          return default

        # convert it back to str
        param = param.decode('ascii')

      return param

    def _correct_img_for_api(self, image_tup):
      """ Resize the (image, name) so that it falls between MIN_SIZE and MAX_SIZE as the minimum
      dimension.
      """
      if self.api_info is None:
        self.get_info()  # sets the image size and other such info from server.
      try:
        MIN_SIZE = self.api_info['min_image_size']
        MAX_SIZE = self.api_info['max_image_size']
        # Will fail here if PIL does not work or is not an image.
        #img = Image.open(image_tup[0])
        img=Image.open(StringIO(image_tup))
        if img.format not in IGNORE_FORMATS:
          min_dimension = min(img.size)
          max_dimension = max(img.size)
          min_ratio = float(MIN_SIZE) / min_dimension
          max_ratio = float(MAX_SIZE) / max_dimension
          im_changed = False
          # Only resample if min size is > 512 or < 256
          if max_ratio < 1.0:  # downsample to MAX_SIZE
            newsize = (int(round(max_ratio * img.size[0])), int(round(max_ratio * img.size[1])))
            img = img.resize(newsize, Image.BILINEAR)
            im_changed = True
          elif min_ratio > 1.0:  # upsample to MIN_SIZE
            newsize = (int(round(min_ratio * img.size[0])), int(round(min_ratio * img.size[1])))
            img = img.resize(newsize, Image.BICUBIC)
            im_changed = True
          else:  # no changes needed so rewind file-object.
            img.verify()
            image_tup[0].seek(0)
            img = Image.open(image_tup[0])
          # Finally make sure we have RGB images.
          if img.mode != "RGB":
            img = img.convert("RGB")
            im_changed = True
          if im_changed:
            io = StringIO()
            img.save(io, 'jpeg', quality=IMG_QUALITY)
      except IOError as e:
        logger.warning('Could not open image file: %s, still sending to server.')#, image_tup[1])
      #finally:
        #image_tup[0].seek(0)  # rewind file-object to read() below is good to go.
      return image_tup
