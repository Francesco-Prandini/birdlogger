

from google.appengine.ext import ndb

from webapp2_extras.appengine.auth import models

from webapp2_extras import security

class BaseModel(ndb.Model):
    @property
    def id(self):
        return str(self.key.id())
    pass

class User(BaseModel, models.User):
     userName=ndb.StringProperty()
     email=ndb.StringProperty()
     firstName=ndb.StringProperty()
     lastName=ndb.StringProperty()
     hasPassword=ndb.BooleanProperty(default=False)

     def set_password(self, raw_password):
        """Sets the password for the current user
         :param raw_password:
             The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)
        self.hasPassword=True
     pass

class Post(BaseModel):
    userKey=ndb.KeyProperty()
    text=ndb.StringProperty()
    geoPt=ndb.GeoPtProperty()
    date=ndb.DateTimeProperty(auto_now_add=True)
    
    @property
    def __geo_interface__(self):
        return {'type': 'Feature', 'properties': {'date': str(self.date),  'postId' : self.id,
                                                  'userId': self.userKey.id(), 'text' : self.text},
                'geometry': {'type': 'Point', 'coordinates': [self.geoPt.__dict__.get("lon"),
                                                              self.geoPt.__dict__.get("lat")]}}
        pass
    pass

class Image(BaseModel):
    postId=ndb.StringProperty()
    bf=ndb.BlobProperty(compressed=True)
    species=ndb.StringProperty()
    tags=ndb.StringProperty(repeated=True)

    @property
    def __geo_interface__(self):
        return {'type': 'Feature', 'properties': {'species': self.species,  'tags':self.tags}}
        pass
    pass



#restituisce una <struttura dati iterable> contenente tutti i post
def getAllPosts():
    return Post.query().order(-Post.date)
    pass

def getPostsFromTo(fromDate,toDate):

    if fromDate and toDate:
        return Post.query().filter(Post.date >= fromDate, Post.date <= toDate)
        pass
    elif fromDate:
        return Post.query().filter(Post.date >= fromDate).order(-Post.date)
        pass
    elif toDate:
        return Post.query().filter(Post.date <= fromDate).order(-Post.date)
        pass
    return getAllPosts()

    pass


#restituisce il post avente come identificatore id 
def getPost(postId):
    return ndb.Key('Post', long(postId)).get()
    pass

def getUserIdByEmail(email):
    return User.query().filter(User.email == email).fetch(1)[0].id
    pass
#crea un nuovo post e lo inserisce nel datastore
# throws BadPropertyError exception
def insertPost(userId, lat, lng, postText):
    new_post=Post()
    new_post.userKey=ndb.Key('User',userId)
    new_post.text=postText
    new_post.geoPt=ndb.model.GeoPt(lat, lng)
    return str(new_post.put().id())
    pass

#elimina tutte le istanze del modello cls presenti nel datastore
def __drop(cls):
    query=cls.query()
    for entity in query:
        entity.key.delete()
        pass
    pass

def dropDatabase():
    __drop(Post)
    __drop(Image)
    __drop(models.Unique)
    __drop(User)
    pass

#aggiunge un'immagine a un post memorizzato nel datastore
def addImageToPost(postId, imageContent, species, tags):
    new_image=Image()
    new_image.postId=postId
    new_image.bf=imageContent
    new_image.species=species
    new_image.tags=tags
    new_image.put()
    pass


#restituisce al max number immagini corrispondenti al post identificato da postId
#se nessuna immagine viene trovata restituisce None
def getImage(postId, number):
     result=Image.query().filter(Image.postId == postId).fetch(number)
     if(len(result) > 0):
         return result
     else:
         return None
     pass

#restituisce l'immagine avente come identificatore id
def getImageById(imageId):
    return ndb.Key('Image', long(imageId)).get()
    pass

#recupera tutte le informazioni relative a un determinato post
# (join naturale )
def getInfo(postId):
    post=getPost(postId)
    user=post.userKey.get()#getUser(post.userId)
    imgSet=getImage(postId, 1)
    if(imgSet):
        img=imgSet[0]
    else:
        img=None
    if(user and post and img):
        params={
        'userId' : user.id,
        'username' : user.userName,
        'postId' : postId, 
        'date' : post.date, 
        'latitude' : post.geoPt.__dict__.values()[0], 
        'longitude' : post.geoPt.__dict__.values()[1], 
        'text' : post.text,
        'imgId' : img.id,
        'species' : img.species, 
        'tags' : img.tags
        }
    else:
        params = None
    return params
    pass

def getPostAndImage(postId):
    post = getPost(postId)
    imgSet = getImage(postId, 1)
    if (imgSet):
        img = imgSet[0]
    else:
        img = None
    if (post and img):
        imageData=[img.id,img.species,img.tags]
        result=post.__geo_interface__
        result['properties']['image']=imageData
        return result
        pass
    return None
    pass

def modifyPostInfo(postId, lat, lng, text):
    post=getPost(postId)
    post.lat=lat
    post.lng=lng
    post.text=text
    post.put()
    pass
def modifyImageInfo(imageId, species, tags):
    img=getImageById(imageId)
    img.species=species
    img.tags=tags
    img.put()
    pass

def getUserIdFromImageId(imageId):
    savedImg = getImageById(imageId)

    if savedImg:
        post = getPost(savedImg.postId)
        if post:
            return post.userKey.get()#userId
    return None
    pass

# def getUserImageFromPost(postId):
#     savedPost=getPost(postId)
#     if savedPost:
#         return savedPost.userId
#     return None
#     pass

def getUser(userId):
    return ndb.Key('User', userId).get()
    pass



# def modifyUser(userId,userName=None,email=None,password=None):
#     user=ndb.Key('User', long(userId)).get()
#
#     if userName and _isUnique(User.userName,userName):
#         user.auth_id=userName
#     if email and _isUnique(User.email,email):
#         user.email=email
#     if password:
#         user.set_password(password)
#     pass
