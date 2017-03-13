from wtforms import form, fields, validators, widgets
from wtforms.validators import ValidationError



class TagListField(fields.Field):
    widget = widgets.TextInput()

    def _value(self):
        if self.data:
            return ' '.join(self.data)
        else:
            return ''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split()]
        else:
            self.data = []
            
    pass

class BaseForm(form.Form):
    @property
    def allErrors(self):
        result = []

        for field in self.errors:
            string = field + " : "
            for error in self.errors[field]:
                string = string + error + "; "
            pass
            result.append(string)
        pass

        return result
        pass

    def insertMessage(self, message):
        self.message=message
        pass


class ImageUploadForm(BaseForm):
    image = fields.FileField('Image Path')

    def validate_image(form, field):
        print field.data
        if str(field.data) == '':
            raise ValidationError(u'field required')

    pass

class PostCreationForm(ImageUploadForm):
    latitude=fields.DecimalField('Latitude', places=None, validators=
    [validators.InputRequired(message='field required'),
    validators.NumberRange(min=-90, max=90, message='must be in the [-90,90] range')
    ])
    
    longitude=fields.DecimalField('Longitude',places=None, validators=
    [validators.InputRequired('field required'),
    validators.NumberRange(min=-180, max=180, message='must be in the [-180,180] range')
    ])
    
    species=fields.StringField('Species', validators=[validators.InputRequired('field required')])
    text=fields.TextAreaField('Description')
    tags=TagListField('Tags')
    #submit=fields.SubmitField('Done')
    
    pass

class ImageRecognitionForm(ImageUploadForm):
    #submit = fields.SubmitField('Done')
    pass

class SignupForm(BaseForm):
    userName=fields.StringField('user name', validators=[validators.InputRequired('field required')])
    email=fields.StringField('email', validators=[validators.InputRequired('field required'),
                                                  validators.Email(message='you  must submit a valid emil address')])
    firstName = fields.StringField('first name')
    lastName = fields.StringField('last name')
    password = fields.PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords must match')])
    confirm = fields.PasswordField('Repeat Password')
    #submit=fields.SubmitField('Done')
    pass


class LoginForm(BaseForm):
    email=fields.StringField('email', validators=[validators.InputRequired('field required'),
                                                  validators.Email(message='you  must submit a valid emil address')])
    password=fields.PasswordField('password', validators=[validators.InputRequired('field required')])
    #submit=fields.SubmitField('Done')
    pass

class modifyInfoForm(BaseForm):
    userName = fields.StringField('user name')
    email = fields.StringField('email', validators=[validators.Email(message='you  must submit a valid emil address')])
    # oldPassword = fields.PasswordField('Old Password', [
    #     validators.InputRequired()])
    newPassword = fields.PasswordField('New Password', [
        validators.EqualTo('confirm', message='Passwords must match')])
    confirmNewPassword = fields.PasswordField('Repeat Password')
    #submit = fields.SubmitField('Done')
    pass
