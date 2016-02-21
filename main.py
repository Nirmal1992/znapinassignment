import jinja2
import webapp2
from webapp2_extras import sessions
from google.appengine.api import images
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.blobstore import BlobKey
from google.appengine.ext.webapp import blobstore_handlers

jinja = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))


class User(ndb.Model):
    user_name = ndb.StringProperty(indexed=True , required=True)
    user_email = ndb.StringProperty(indexed=True , required=True)
    user_tel = ndb.StringProperty()
    user_password = ndb.StringProperty(required=True)
    user_key =ndb.KeyProperty()

class UserPhoto(ndb.Model):
    photoKey = ndb.BlobKeyProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    like = ndb.IntegerProperty(repeated=True)
    p_user_id = ndb.IntegerProperty(required=True)

class Comments(ndb.Model):
    c_user_id = ndb.IntegerProperty(required=True)
    comment = ndb.StringProperty(repeated=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    c_photo_id = ndb.IntegerProperty(required=True)


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend='datastore')

class UploadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    session_store = None
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend='datastore')

class UploadHandler1(blobstore_handlers.BlobstoreUploadHandler):

    session_store = None
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend='datastore')

class Logout(BaseHandler):
    def get(self):
        for nonsense in self.session_store.get_session():
            del nonsense
        self.redirect("/")

class MyHandler(BaseHandler):
    def get(self):

        template = jinja.get_template('index.html')
        self.response.write(template.render())

    def post(self):

        x = self.request.get('user_name')
        y = self.request.get('user_password')
        user_query = User.query(User.user_name == x).fetch()
        if (user_query == []):
                template = jinja.get_template('usernameAlert.html')
                self.response.write(template.render())
                self.response.write('</body></html>')
        else:
            for users in user_query:
                if users.user_password == y and users.user_name == x:
                    self.session['userid']=users.key.id()
                    self.redirect("/user/?id=%s" %users.key.id())
            template = jinja.get_template('passwordAlert.html')
            self.response.write(template.render())
            self.response.write('</body></html>')



class Register(MyHandler):

    def post(self):


        user1 = User(user_name=self.request.get('user_name'), user_email=self.request.get('user_email'),
                     user_tel=self.request.get('user_tel'), user_password=self.request.get('user_password'))
        user1.put()
        self.response.write('<html><body><script>window.alert("You are successfully registered %s!!"); window.location.assign("/")</script></body></html>'%user1.user_name)




class UserDashboard(UploadHandler):
    def get(self,key):
        template = jinja.get_template('userdashboard.html')
        x = ndb.Key("User",int(self.session['userid'])).get()
        upload_url = blobstore.create_upload_url('/upload/?id=')
        template_values = {'imgurl': upload_url,'username':x.user_name}
        self.response.write(template.render(template_values))
        y = UserPhoto.query().order(-UserPhoto.date).fetch()

        for photo in y:
                count12=0
                count=0
                self.response.write('<table width="500px" height="100%" align="center"> border="10px">')
                blob_info = blobstore.BlobInfo.get(photo.photoKey)
                url = images.get_serving_url(photo.photoKey)
                self.response.write('<tr border="10px" border-color=black><td align="center"><H2>%s</H2>' %blob_info.filename)
                self.session['photokey1']=photo.key.id()
                self.response.out.write(
                    '<img src="%s" style="width:500px;height:300px;"><br />' % url)
                comm = Comments.query().order(-Comments.date).fetch()

                for faltu in photo.like:
                    count12=count12+1
                for comment1 in comm:
                    if comment1.c_photo_id == photo.key.id():

                        self.response.write('<b>%s:</b>'%((ndb.Key("User",int(comment1.c_user_id)).get()).user_name))
                        count+=1
                        for apple in comment1.comment:
                            self.response.write('%s<br>'%apple)


                self.response.write("""
                <form action="/user/?photoid=%s" method="post">
                <div>
                    <input type="text" name="Comment">
                </div>
                <input type="submit" value="Comment">
                 </form>
                <form action="/like/?blobkey=%s" method="post">
                    <input type="submit" id="myBtn" onclick="alert('You liked the image!!')" value="Like">%d
                 </form>
                 </td>
                 </tr>
                 </table>

                 """%(photo.key.id(),photo.photoKey,count12 ))

        self.response.write('</body></html>')


    def post(self,nirmal):
        x = self.request.get("Comment").encode('utf8')
        comment_instance = Comments.query(Comments.c_photo_id == int(self.request.get("photoid")) , Comments.c_user_id ==int(self.session["userid"])).fetch()

        if comment_instance == []:
            nokia = Comments(c_user_id = self.session['userid'], c_photo_id = int(self.request.get("photoid")))
            nokia.comment.append(x)
            nokia.put()
            #self.response.write("hello %s"%self.request.get("photoid"))
        else:
            for htc in comment_instance:
                htc.comment.append(x)
                htc.put()
            #self.response.write("hello1 %s"%self.request.get("photoid"))
            #self.response.write(comment_instance)
        self.redirect('/user/?id=%s' %self.session['userid'])




class PhotoUploader(UploadHandler1):

    def post(self, key):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        user_photo = UserPhoto(
            photoKey=blob_info.key() , p_user_id=self.session['userid'])
        user_photo.put()
        self.redirect('/user/?id=%s' %self.session['userid'])

class LikeHandler(BaseHandler):
    def post(self,nirmal):
        photo_instance = UserPhoto.query(UserPhoto.photoKey == BlobKey(self.request.get("blobkey"))).fetch()
        for htc in photo_instance:
                if self.session["userid"] not in htc.like:
                    htc.like.append(int(self.session["userid"]))
                    htc.put()
        self.redirect("/user/?id=%s" %self.session['userid'])


config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
     'backends': {'datastore': 'webapp2_extras.appengine.sessions_ndb.DatastoreSessionFactory',
                 'memcache': 'webapp2_extras.appengine.sessions_memcache.MemcacheSessionFactory',
                 'securecookie': 'webapp2_extras.sessions.SecureCookieSessionFactory',}
    }

app = webapp2.WSGIApplication(
    [('/', MyHandler), ('/register', Register), ('/user/([^/]+)?', UserDashboard), ('/upload/([^/]+)?', PhotoUploader),
     ('/logout',Logout),('/like/([^/]+)?', LikeHandler) ], config=config,debug=True)
