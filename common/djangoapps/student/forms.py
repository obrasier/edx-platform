"""
Utility functions for validating forms
"""
from importlib import import_module
import re

from django import forms
from django.forms import widgets, ModelForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.tokens import default_token_generator

from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _
from django.template import loader

from django.conf import settings
from microsite_configuration import microsite
from student.models import CourseEnrollmentAllowed
from util.password_policy_validators import (
    validate_password_length,
    validate_password_complexity,
    validate_password_dictionary,
)
from student.models import StudentProfile, TeacherProfile, School, ClassSet, Subject 
from django.core.validators import RegexValidator
from student.helpers import is_teacher

class PasswordResetFormNoActive(PasswordResetForm):
    error_messages = {
        'unknown': _("That e-mail address doesn't have an associated "
                     "user account. Are you sure you've registered?"),
        'unusable': _("The user account associated with this e-mail "
                      "address cannot reset the password."),
    }

    def clean_email(self):
        """
        This is a literal copy from Django 1.4.5's django.contrib.auth.forms.PasswordResetForm
        Except removing the requirement of active users
        Validates that a user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        #The line below contains the only change, removing is_active=True
        self.users_cache = User.objects.filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if any((user.password.startswith(UNUSABLE_PASSWORD_PREFIX))
               for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email

    def save(
            self,
            domain_override=None,
            subject_template_name='registration/password_reset_subject.txt',
            email_template_name='registration/password_reset_email.html',
            use_https=False,
            token_generator=default_token_generator,
            from_email=settings.DEFAULT_FROM_EMAIL,
            request=None
    ):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        # This import is here because we are copying and modifying the .save from Django 1.4.5's
        # django.contrib.auth.forms.PasswordResetForm directly, which has this import in this place.
        from django.core.mail import send_mail
        for user in self.users_cache:
            if not domain_override:
                site_name = microsite.get_value(
                    'SITE_NAME',
                    settings.SITE_NAME
                )
            else:
                site_name = domain_override
            context = {
                'email': user.email,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                'platform_name': microsite.get_value('platform_name', settings.PLATFORM_NAME)
            }
            subject = loader.render_to_string(subject_template_name, context)
            # Email subject *must not* contain newlines
            subject = subject.replace('\n', '')
            email = loader.render_to_string(email_template_name, context)
            send_mail(subject, email, from_email, [user.email])


class TrueCheckbox(widgets.CheckboxInput):
    """
    A checkbox widget that only accepts "true" (case-insensitive) as true.
    """
    def value_from_datadict(self, data, files, name):
        value = data.get(name, '')
        return value.lower() == 'true'


class TrueField(forms.BooleanField):
    """
    A boolean field that only accepts "true" (case-insensitive) as true
    """
    widget = TrueCheckbox


_USERNAME_TOO_SHORT_MSG = _("Username must be minimum of two characters long")
_EMAIL_INVALID_MSG = _("A properly formatted e-mail is required")
_EMAIL_CONFIRM_INVALID_MSG = _("Please enter your e-mail twice")
_PASSWORD_INVALID_MSG = _("A valid password is required")
_NAME_TOO_SHORT_MSG = _("Your legal name must be a minimum of two characters long")
_PASSWORD_DOES_NOT_MATCH = _("Your password fields do not match")
_PASSWORD_CONFIRM_INVALID_MSG = _("Please enter your password twice")
_PHONE_INVALID_MESSAGE = _("Invalid phone number. Please enter your phone number in one of these formats +61299999999 or 0299999999")

class AccountCreationForm(forms.Form):
    """
    A form to for account creation data. It is currently only used for
    validation, not rendering.
    """
    # TODO: Resolve repetition
    username = forms.SlugField(
        min_length=2,
        max_length=30,
        error_messages={
            "required": _USERNAME_TOO_SHORT_MSG,
            "invalid": _("Usernames must contain only letters, numbers, underscores (_), and hyphens (-)."),
            "min_length": _USERNAME_TOO_SHORT_MSG,
            "max_length": _("Username cannot be more than %(limit_value)s characters long"),
        }
    )
    email = forms.EmailField(
        max_length=75,  # Limit per RFCs is 254, but User's email field in django 1.4 only takes 75
        error_messages={
            "required": _EMAIL_INVALID_MSG,
            "invalid": _EMAIL_INVALID_MSG,
            "max_length": _("Email cannot be more than %(limit_value)s characters long"),
        }
    )
    email_confirm = forms.EmailField(
        max_length=75,  # Limit per RFCs is 254, but User's email field in django 1.4 only takes 75
        error_messages={
            "required": _EMAIL_CONFIRM_INVALID_MSG,
        }
    )
    password = forms.CharField(
        min_length=2,
        error_messages={
            "required": _PASSWORD_INVALID_MSG,
            "min_length": _PASSWORD_INVALID_MSG,
        }
    )
    password_confirm = forms.CharField(
        error_messages={
            "required": _PASSWORD_CONFIRM_INVALID_MSG,
        }
    )
    name = forms.CharField(
        required = False,
        #error_messages={
        #    "required": _NAME_TOO_SHORT_MSG,
        #    "min_length": _NAME_TOO_SHORT_MSG,
        #}
    )
    first_name = forms.CharField(
        min_length=2,
        error_messages={
            "required": _NAME_TOO_SHORT_MSG,
            "min_length": _NAME_TOO_SHORT_MSG,
        }
    )
    last_name = forms.CharField(
        min_length=2,
        error_messages={
            "required": _NAME_TOO_SHORT_MSG,
            "min_length": _NAME_TOO_SHORT_MSG,
        }
    )
    reg_type = forms.ChoiceField(
        widget = forms.RadioSelect,
        choices = ((1,'Student'),(2,'Teacher')),
    )


    def __init__(
            self,
            data=None,
            extra_fields=None,
            extended_profile_fields=None,
            enforce_username_neq_password=False,
            enforce_password_policy=False,
            tos_required=True
    ):
        super(AccountCreationForm, self).__init__(data)

        extra_fields = extra_fields or {}
        self.extended_profile_fields = extended_profile_fields or {}
        self.enforce_username_neq_password = enforce_username_neq_password
        self.enforce_password_policy = enforce_password_policy
        if tos_required:
            self.fields["terms_of_service"] = TrueField(
                error_messages={"required": _("You must accept the terms of service.")}
            )

        # TODO: These messages don't say anything about minimum length
        error_message_dict = {
            "level_of_education": _("A level of education is required"),
            "gender": _("Your gender is required"),
            "year_of_birth": _("Your year of birth is required"),
            "mailing_address": _("Your mailing address is required"),
            "goals": _("A description of your goals is required"),
            "city": _("A city is required"),
            "country": _("A country is required")
        }
        for field_name, field_value in extra_fields.items():
            if field_name not in self.fields:
                if field_name == "honor_code":
                    if field_value == "required":
                        self.fields[field_name] = TrueField(
                            error_messages={
                                "required": _("To enroll, you must follow the honor code.")
                            }
                        )
                else:
                    required = field_value == "required"
                    min_length = 1 if field_name in ("gender", "level_of_education") else 2
                    error_message = error_message_dict.get(
                        field_name,
                        _("You are missing one or more required fields")
                    )
                    self.fields[field_name] = forms.CharField(
                        required=required,
                        min_length=min_length,
                        error_messages={
                            "required": error_message,
                            "min_length": error_message,
                        }
                    )

        for field in self.extended_profile_fields:
            if field not in self.fields:
                self.fields[field] = forms.CharField(required=False)
    
    def clean_email_confirm(self):
        email = self.cleaned_data["email"]
        email_confirm = self.cleaned_data["email_confirm"]
        if email and email != email_confirm:
            raise ValidationError(_("E-mail fields don't match"))
        return email_confirm
 
#    def clean_password_confirm(self):
#        password = self.cleaned_data["password"]
#        password_confirm = self.cleaned_data["password_confirm"]
#        if password and password != password_confirm:
#            raise ValidationError(_("Password fields don't match"))
#        return password_confirm

       
    def clean_password(self):
        """Enforce password policies (if applicable)"""
        password = self.cleaned_data["password"]
        if (
                self.enforce_username_neq_password and
                "username" in self.cleaned_data and
                self.cleaned_data["username"] == password
        ):
            raise ValidationError(_("Username and password fields cannot match"))
        if self.enforce_password_policy:
            try:
                validate_password_length(password)
                validate_password_complexity(password)
                validate_password_dictionary(password)
            except ValidationError, err:
                raise ValidationError(_("Password: ") + "; ".join(err.messages))
        return password

    def clean_email(self):
        """ Enforce email restrictions (if applicable) """
        email = self.cleaned_data["email"]
        if settings.REGISTRATION_EMAIL_PATTERNS_ALLOWED is not None:
            # This Open edX instance has restrictions on what email addresses are allowed.
            allowed_patterns = settings.REGISTRATION_EMAIL_PATTERNS_ALLOWED
            # We append a '$' to the regexs to prevent the common mistake of using a
            # pattern like '.*@edx\\.org' which would match 'bob@edx.org.badguy.com'
            if not any(re.match(pattern + "$", email) for pattern in allowed_patterns):
                # This email is not on the whitelist of allowed emails. Check if
                # they may have been manually invited by an instructor and if not,
                # reject the registration.
                if not CourseEnrollmentAllowed.objects.filter(email=email).exists():
                    raise ValidationError(_("Unauthorized email address."))
        return email
    def clean_year_of_birth(self):
        """
        Parse year_of_birth to an integer, but just use None instead of raising
        an error if it is malformed
        """
        try:
            year_str = self.cleaned_data["year_of_birth"]
            return int(year_str) if year_str is not None else None
        except ValueError:
            return None

    @property
    def cleaned_extended_profile(self):
        """
        Return a dictionary containing the extended_profile_fields and values
        """
        return {
            key: value
            for key, value in self.cleaned_data.items()
            if key in self.extended_profile_fields and value is not None
        }
    
    #NEW: clean multiple fields
    def clean(self):
        """
        Checks email repeat field and password repeat field
        """
        # Checks if e-mail fields match
        
        # Checks if password fields match
        super(AccountCreationForm, self).clean()
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password != password_confirm:
            self.add_error('password',ValidationError(_("Password fields don't match.")))


def get_registration_extension_form(*args, **kwargs):
    """
    Convenience function for getting the custom form set in settings.REGISTRATION_EXTENSION_FORM.

    An example form app for this can be found at http://github.com/open-craft/custom-form-app
    """
    if not settings.FEATURES.get("ENABLE_COMBINED_LOGIN_REGISTRATION"):
        return None
    if not getattr(settings, 'REGISTRATION_EXTENSION_FORM', None):
        return None
    module, klass = settings.REGISTRATION_EXTENSION_FORM.rsplit('.', 1)
    module = import_module(module)
    return getattr(module, klass)(*args, **kwargs)

# Student and Teacher Registration Form are used to 
#     1. Validate Fields
#     2. Responsible for addressing student/teacher specific required fields.
#        These aren't handled for fields with reg_type in json Logistration form.

class StudentRegistrationForm(forms.Form):
    # aboriginal or torres strait islander
    indigenous = forms.BooleanField(
        error_messages = {
            "invalid" : _("Invalid Boolean input")
        },
        label = _("I am of Aboriginal or Torres Strait Islander origin."),
        required = False   #This will assume False by model definitions for unspecified.
    )
    
    # school grade
    SCHOOL_GRADES = StudentProfile.SCHOOL_GRADES
    school_grade = forms.ChoiceField(
        choices = SCHOOL_GRADES,
        required = False
    )

    # class code
    class_code = forms.CharField(
        #max_length = 8, length can be handled by the regex validator. To avoid brute forcing 8 character classcodes
        #min_length = 8,
        error_messages={
            #"min_length" :  _("Your class code should be 8 characters long"),
            #"max_length" :  _("Your class code should be 8 characters long"),
            "invalid" : _("Your class code contains only letters (A-Z) and numbers (0-9)"),
            "required": _("A class code is required. Please check with your supervising teacher."),
        },
        label = _("Your Class Code"),
        required = True
    )
    
    # validate classcode is 8 characters long with A_Z0-9
    def clean_class_code(self):
        class_code = self.cleaned_data["class_code"].upper()
        if not re.match('^[\dA-Z]{8}$',class_code):
            raise ValidationError(_("Invalid format for class code. Please check your class code with your supervising teacher."))
        else:
            return class_code
   

class TeacherRegistrationForm(forms.Form):
    # school name
    school = forms.CharField(
        max_length = 100,
        required = True,
        label= _("School Name"),
        error_messages={
            "required": _("School Required: Please search for your school")
        }
    )
    
    school_id = forms.CharField(
        max_length=10,
        required = True,
        label= _("School ID"),
        validators = [RegexValidator(regex="^\d*$",message="School_id is given in an invalid format.")]
    )
    # contact phone number
    phone = forms.CharField(
        max_length = 16,
        min_length = 10,    
        label = _("Contact Phone Number"),
        #instructions = _("Enter a valid Australian mobile or landline number"),
        required = True,
        #validators = [RegexValidator(regex="^\+?[0-9\)\(\- ]*$",message=_("Phone number uses invalid characters. Can only use digits, +, ,(,),-, or spaces"))]
        error_messages={
            "min_length" : _PHONE_INVALID_MESSAGE,
            "max_length" :  _PHONE_INVALID_MESSAGE,
            "invalid" : _PHONE_INVALID_MESSAGE,
        },
    )

    # how did you hear about us
    HEAR_FROM = TeacherProfile.HEAR_FROM
    hear_about_us = forms.ChoiceField(
        choices = HEAR_FROM,
        label = _("How did you hear about us?"),
        required = False,
    )
    ##validators

    def clean_phone(self):
        """
        Clean phone number into valid phone number format
        """
        phone = self.cleaned_data.get("phone")
        phone = re.sub('(\(|\)|-)', '', phone)
        if not re.match("^(\+\d{9,12}|0\d{9})$",phone):
            raise ValidationError(_("Invalid phone format."))
        return phone
    
class SchoolRegistrationForm(forms.Form):

    # school address
    street_address = forms.CharField(
        max_length = 30,
    )
    suburb = forms.CharField(
        max_length = 30,
    )
    state = forms.CharField(
        max_length = 3,    
    )
    postcode = forms.CharField(
        max_length = 6,
    )

class TextSelectMultiple(widgets.SelectMultiple):
    """
    Set checked values based on a comma separated list instead of a python list
    """
    def render(self, name, value, **kwargs):
        if isinstance(value, basestring):
            value = value.split(",")
        return super(TextSelectMultiple, self).render(name, value, **kwargs)

class TextMultiField(forms.MultipleChoiceField):
    """
    Work in conjunction with TextCheckboxSelectMultiple to store a
    comma separated list of multiple choice values in a CharField/TextField
    """
    widget = TextSelectMultiple
    def clean(self, value):
        val = super(TextMultiField, self).clean(value)
        return ",".join(val)
    
class ClassSetForm(ModelForm):
    assessment = forms.TypedChoiceField(
               coerce=lambda x: x == 'True',
               choices=((True, 'Yes'), (False, 'No')),
               widget=forms.RadioSelect
            )
    grade = TextMultiField(choices = StudentProfile.SCHOOL_GRADES)
    no_of_students = forms.IntegerField(required=True, min_value=0)
    class Meta:
        model = ClassSet
        
        fields = ['short_name','class_name','assessment','subject','grade','no_of_students']
        labels = {
            'short_name': _('Short Name'),
            'class_name':_('Class Team Name'),
            'assessment':_('Assessment'),
            'no_of_students': _('Number of students in class'),
        }
        help_texts = {
            'short_name': _('A quick personal reference name.'),
            'class_name':_('A team name for your class. This will be displayed your student\'s profiles'),
            'assessment':_('Will you be using the course grades as part of your teaching rubric?'),
            'grade': _('Hold down Ctrl or cmd to select multiple grades'),
            'no_of_students': _('The size of your class (not necessarily how many students have signed up with accounts).'),
        }
        error_messages = {
            'short_name': {
                'max_length': _("This name is too long."),
            },
            'class_name': {
                'max_length': _("This name is too long."),
            },
            'no_of_students': {
                'required': _("Enter the number of students in your class. If you are uncertain, you can estimate and change this field later."),
            },
        }
        widgets = {
            'short_name': forms.TextInput(attrs = {'placeholder': 'e.g. Yr09LineB'}),
            'class_name': forms.TextInput(attrs = {'placeholder': 'e.g. The Mighty Ducks'}),
            'subject': forms.Select(),
        }

class OtherSubjectForm(ModelForm):
    class Meta:
        model = Subject
        fields = ['description']
        help_texts = {'description': _('Please specify.')}
        def save(self, *args, **kwargs):
            instance = super(OtherSubjectForm, self).save(commit=False)
            default_list = False
            instance.save()
