"""
Instructor Dashboard Views
"""

import logging
import datetime
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
import uuid
import pytz
import mimetypes
import json
import pdb
import os
import hashlib

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _, ugettext_noop
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from edxmako.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.http import Http404, HttpResponseServerError, HttpResponseRedirect
from django.conf import settings
from util.json_request import JsonResponse
from mock import patch

from lms.djangoapps.lms_xblock.runtime import quote_slashes
from openedx.core.lib.xblock_utils import wrap_xblock
from xmodule.html_module import HtmlDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.tabs import CourseTab
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from courseware.access import has_access
from courseware.courses import get_course_by_id, get_studio_url
from django_comment_client.utils import has_forum_access
from django_comment_common.models import FORUM_ROLE_ADMINISTRATOR
from student.models import CourseEnrollment
from shoppingcart.models import Coupon, PaidCourseRegistration, CourseRegCodeItem
from course_modes.models import CourseMode, CourseModesArchive
from student.roles import CourseFinanceAdminRole, CourseSalesAdminRole
from certificates.models import (
    CertificateGenerationConfiguration,
    CertificateWhitelist,
    GeneratedCertificate,
    CertificateStatuses,
    CertificateGenerationHistory,
    CertificateInvalidation,
)
from certificates import api as certs_api
from util.date_utils import get_default_time_display

from class_dashboard.dashboard_data import get_section_display_name, get_array_section_has_problem
from .tools import get_units_with_due_date, title_or_url, bulk_email_is_enabled_for_course
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from .tools import get_student_from_identifier
from student.forms import ClassSetForm, CompetitionSubmissionForm
from django.forms.models import model_to_dict
from student.helpers import is_teacher, get_my_classes, get_class_size
from student.models import ClassSet, CompetitionSubmission

from instructor.utils import get_class_codes_of_teacher, get_last_submission_summary
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.clickjacking import xframe_options_exempt

from django.contrib.auth.models import User
from student.helpers import get_my_classes, get_class_size, is_teacher, is_student, get_student_class_info
from instructor.views.api import _get_assignment_names as get_assignment_names

from django.core.files.storage import default_storage
from django.core.files import File

log = logging.getLogger(__name__)

#NEW: TeacherDashboardTab
class TeacherDashboardTab(CourseTab):
    """
    Defines the Teacher Dashboard view type that is shown as a course tab.
    """

    type = "teacher"
    title = ugettext_noop('Teacher Dashboard')
    view_name = "teacher_dashboard"
    is_dynamic = True    # The "Teacher Dashboard" tab is instead dynamically added when it is enabled

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns true if the specified user has staff access.
        """
        return bool(user and has_access(user, 'teacher', course.id))

class InstructorDashboardTab(CourseTab):
    """
    Defines the Instructor Dashboard view type that is shown as a course tab.
    """

    type = "instructor"
    title = ugettext_noop('Instructor')
    view_name = "instructor_dashboard"
    is_dynamic = True    # The "Instructor" tab is instead dynamically added when it is enabled

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns true if the specified user has staff access.
        """
        return bool(user and has_access(user, 'staff', course, course.id))

@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def teacher_dashboard(request, course_id):
    """ Display the teacher dashboard for a course. """
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        log.error(u"Unable to find course with course key %s while loading the Teacher Dashboard.", course_id)
        return HttpResponseServerError()

    course = get_course_by_id(course_key, depth=0)

    access = {
        'admin': request.user.is_staff,
        'instructor': bool(has_access(request.user, 'instructor', course)),
        'finance_admin': CourseFinanceAdminRole(course_key).has_user(request.user),
        'sales_admin': CourseSalesAdminRole(course_key).has_user(request.user),
        'staff': bool(has_access(request.user, 'staff', course)),
        'forum_admin': has_forum_access(request.user, course_key, FORUM_ROLE_ADMINISTRATOR),
        'teacher' : bool(has_access(request.user,'teacher', course_key)),
    }

    if not access['teacher']:
        raise Http404("You do not have access to this page")

    # This should never need to be raised, since assigning teacher access should always check for this first.
    #if not is_teacher(request.user):
    #    raise Http404("You have the wrong user type to access this page. Please contact the site administrator.")

    is_white_label = CourseMode.is_white_label(course_key)
    
    class_form_dict = {}
    class_set_form = ClassSetForm()
    competition_form = CompetitionSubmissionForm(initial={'contact_email':request.user.email,'contact_name':" ".join([request.user.first_name,request.user.last_name]),'contact_ph':request.user.teacherprofile.phone})
    competition_dict = {'competition_submission_form':competition_form}

    if request.method == 'POST':
        if request.POST.get("formtype") == "competition":
            competition_dict.update(_competition_submission_form_handler(request,course_id))
        else:
            class_set_form = ClassSetForm(request.POST.copy())
            if class_set_form.is_valid():
                _create_new_class(class_set_form, course_key, request.user)
                class_form_dict.update( {'success': 'Class successfully added!'})
                return HttpResponseRedirect(reverse('teacher_dashboard',kwargs={'course_id':unicode(course_key)})+'#view-my_classes')
                #class_set_form = ClassSetForm() # refresh to blank form
            else:
                pass                            # errors will be updated

    new_class_dict = _section_my_classes(course,access,request.user)
    new_class_dict.update({'class_set_form': class_set_form})
    class_code_list = get_class_codes_of_teacher(request.user,course_key)

    submission_history = []

    for c in class_code_list:
        s = get_last_submission_summary(c['class_code'])
        if s:
            submission_history.append(s)


    # arrange competition section, and update with any POST results
    competition_section = _section_competition_submission(course,access,class_code_list)
    competition_section.update(competition_dict)
    competition_section.update({'submission_history': submission_history})
    

    # competition success redirection
    if request.method =='POST' and competition_section['success'] == True:
        return HttpResponseRedirect(reverse('teacher_dashboard',kwargs={'course_id':unicode(course_key)})+'?success=true#view-competition_submission')
    
    # after competition success redirection
    if request.method == 'GET' and request.GET.get('success',None)=="true":
        competition_section.update({'success': True})
    
    sections = [
        #_section_course_info(course, access),
        new_class_dict,
        _section_my_students(course, access, is_white_label, request.user, class_code_list),
        _section_grade_centre(course, access,class_code_list),
        competition_section,
    ]
    
    context = {
        'course': course,
        'sections': sections,
    }

    return render_to_response('instructor/teacher_dashboard/teacher_dashboard.html', context)

def _competition_submission_form_handler(request,course_id):
    """
    Handles validating the competition submission form.
    
    Validation Rules
    - Basic Form Rules
    - Either video or URL must be uploaded
    - All file sizes must be under 20MB

    - If all rules are satisfied, calls function _upload_competition_submission
      to handle the file storage and create a CompetitionSubmission model

    Returns: A dictionary of fields to be updated to the section data by the parent view.
    """
    competition_dict = {}
    competition_dict['video_url_errors']=""
    competition_form= CompetitionSubmissionForm(request.POST.copy()) 
    competition_dict['success'] = False # presumes unsuccessful
    if competition_form.is_valid():
        log.warning("Form is valid")
        if not (request.FILES.get('video_upload',False) or request.POST.get('video_url',False)):
            competition_dict.update({'video_url_errors':"You require at least a File Upload or URL."})
        else:
            # upload and process the submission fields and files
            success = _upload_competition_submission(request,course_id,competition_form)
            competition_dict.update(success)
            
    else:
        log.warning("Form is invalid") 
        
    if not competition_dict['success']:
        competition_dict['competition_submission_form'] = competition_form #assume for now that the form will need to be returned this way, unless there is a success

    return competition_dict

def _upload_competition_submission(request,course_id,competition_form):
    """
    Handles the entry of a new submission
    """
    try:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        class_code = request.POST.get('class_code')
        class_set = ClassSet.objects.get(class_code=class_code)

        video_entry = {}
        video_url = request.POST.get('video_url',None)
        video_file = request.FILES.get('video_upload',None)

        media_entry = {}
        media_release_files = request.FILES.getlist('media_release_upload')

        src_files = request.FILES.getlist('src_upload')
        src_entry = {}

        # Create entry (without committing to writing to the db yet)
        entry = CompetitionSubmission(
            device_name=competition_form.cleaned_data['device_name'],
            device_description = competition_form.cleaned_data['device_description'],
            contact_name = competition_form.cleaned_data['contact_name'],
            contact_ph = competition_form.cleaned_data['contact_ph'],
            contact_email = competition_form.cleaned_data['contact_email'],
            acknowledge_toc = competition_form.cleaned_data['acknowledge_toc'],
            attempt_number = CompetitionSubmission.objects.filter(class_set__class_code=class_code).count()+1,
            class_set = class_set,
            school = class_set.school,
        )

        # first find out how many submissions this class has made
            # first prepare the JSON additions tos 
        # if there is an easy video URL (sweet no problems)
        ###
        # Video Upload
        ###
        if video_url:
            video_entry['url'] = request.POST.get('video_url')
        
        if video_file:
            date = datetime.date.today().isoformat()
            sha1 = _comp_get_sha1(video_file.name,unicode(course_key),class_code,date)
            path = _comp_file_storage_path(sha1,video_file.name,course_key,class_code,entry.attempt_number,'video')
            video_entry['video_file_sha1'] = sha1
            video_entry['video_file_mimetype'] = mimetypes.guess_type(video_file.name)[0] 
            video_entry['video_file_name'] = video_file.name
            if not default_storage.exists(path):
                default_storage.save(path,File(video_file.file))
            
        entry.video_entry = json.dumps(video_entry)
        
        ###
        # Media Release
        ###
        if len(media_release_files)>0:
            media_entry['media_file_names'] = []
            media_entry['media_file_sha1s'] = []
            media_entry['media_file_mimetypes'] = []

        for f in media_release_files:
            date = datetime.date.today().isoformat()
            sha1 = _comp_get_sha1(f.name,unicode(course_key),class_code,date)
            path = _comp_file_storage_path(sha1,f.name,course_key,class_code,entry.attempt_number,'media')
            media_entry['media_file_sha1s'].append(sha1)
            media_entry['media_file_mimetypes'].append(mimetypes.guess_type(f.name)[0])
            media_entry['media_file_names'].append(f.name)

            if not default_storage.exists(path):
                default_storage.save(path,File(f.file))
            
        entry.media_release = json.dumps(media_entry)

        ###
        # Src Upload
        ###
        if len(src_files)>0:
            src_entry['src_file_names'] = []
            src_entry['src_file_sha1s'] = []
            src_entry['src_file_mimetypes'] = []

        for f in src_files:
            date = datetime.date.today().isoformat()
            sha1 = _comp_get_sha1(f.name,unicode(course_key),class_code,date)
            path = _comp_file_storage_path(sha1,f.name,course_key,class_code,entry.attempt_number,'src')
            src_entry['src_file_sha1s'].append(sha1)
            src_entry['src_file_mimetypes'].append(mimetypes.guess_type(f.name)[0])
            src_entry['src_file_names'].append(f.name)

            if not default_storage.exists(path):
                default_storage.save(path,File(f.file))

        entry.src_code_entry = json.dumps(src_entry)

        entry.save()
        log.warning("Saved model")
        return {'success': True}

    except Exception:
        log.error(type(Exception))
        log.error(Exception)
        return {'success': False, 'error_msg': True }

def _comp_file_storage_path(sha1, filename,course_key,class_code,attempt,sub_type):
    path = (
        'competition_submissions/{course_key.org}/{course_key.course}/{class_code}/'
        '{attempt}/{sub_type}/{sha1}{ext}'.format(
            course_key=course_key,
            sha1=sha1,
            class_code=class_code,
            sub_type=sub_type,
            attempt=attempt,
            ext=os.path.splitext(filename)[1]
        )
    )
    return path

def _comp_get_sha1(filename,course_id,class_code,date):
    sha1 = hashlib.sha1()
    sha1.update(course_id)
    sha1.update(class_code)
    sha1.update(date)
    return sha1.hexdigest()

    
def _create_new_class(form, course_key, user):
    """ Create a new class in the database """
    class_set = ClassSet(
                    created_by=user,
                    teacher=user,
                    short_name=form.cleaned_data['short_name'],
                    class_name=form.cleaned_data['class_name'],
                    school=user.teacherprofile.school,
                    course_id=course_key,
                    grade=form.cleaned_data['grade'],
                    subject=form.cleaned_data['subject'],
                    assessment=form.cleaned_data['assessment'],
                    no_of_students=form.cleaned_data['no_of_students'])
    try:
        class_set.save()
    except Exception:
        log.error("Error creating class set for %s"%user)
        raise 

def _section_my_students_old(course,access, is_white_label,user,class_code_list=None):
    course_key = course.id
    section_data = {
   }
    section_data = {
        'section_key': 'my_students',
        'section_display_name':_('My Students'),
        'access': access,
        'course_id': course_key,
        'ccx_is_enabled': False,
        'num_sections': len(course.children),
        'is_white_label': is_white_label,        
        'list_students_of_class_code_url': reverse('list_students_of_class_code',kwargs={'course_id': unicode(course_key)}),
	'list_course_role_members_url': reverse('list_course_role_members', kwargs={'course_id': unicode(course_key)}),
	'update_forum_role_membership_url': reverse('update_forum_role_membership', kwargs={'course_id': unicode(course_key)}),
	'class_code_list': class_code_list, 
        'enroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'unenroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'upload_student_csv_button_url': reverse('register_and_enroll_students', kwargs={'course_id': unicode(course_key)}),
        'modify_beta_testers_button_url': reverse('bulk_beta_modify_access', kwargs={'course_id': unicode(course_key)}),
        'list_course_role_members_url': reverse('list_course_role_members', kwargs={'course_id': unicode(course_key)}),
        'modify_access_url': reverse('modify_access', kwargs={'course_id': unicode(course_key)}),
        'list_forum_members_url': reverse('list_forum_members', kwargs={'course_id': unicode(course_key)}),
        'update_forum_role_membership_url': reverse('update_forum_role_membership', kwargs={'course_id': unicode(course_key)}),
 
	}
    return section_data


# MM NEW: Inherited from membership and modified to return user specific fields.
def _section_my_classes(course, access, user):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id

    section_data = {
        'section_key': 'my_classes',
        'section_display_name': _('My Classes'),
        'access': access,
        'course_id': course_key,
        'num_sections': len(course.children),
        'class_set_form': ClassSetForm(),
    }
    
    # get classes (a list of dictionaries)
    classes = get_my_classes(user,course_key)
    classes_info = []
    for c in classes:
        cdict = {}
        cdict['total_accounts']=get_class_size(c)
        cdict['active_accounts']=get_class_size(c,True)
        cdict.update(model_to_dict(c,fields=['short_name','class_name','class_code','grade','no_of_students' ,'assessment']))
        cdict['school_name'] = c.school.__unicode__()
        subjects = dict(ClassSetForm.SUBJECTS)
        cdict['subject'] = subjects[c.subject]
        
        classes_info.append(cdict)
    
    section_data['my_classes'] = classes_info

    return section_data

#def _section_students(course, access, user):
#    """ List the students and link to their profile page. """
#    course_key = course.id
#
#    section_data = {
#        'section_key': 'students',
#        'section_display_name': _('Students'),
#        'access': access,
#        'course_id': course_key,
#        'num_sections': len(course.children),
#    }
#
#    return section_data



@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard_2(request, course_id):
    """ Display the instructor dashboard for a course. """
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        log.error(u"Unable to find course with course key %s while loading the Instructor Dashboard.", course_id)
        return HttpResponseServerError()

    course = get_course_by_id(course_key, depth=0)

    access = {
        'admin': request.user.is_staff,
        'instructor': bool(has_access(request.user, 'instructor', course)),
        'finance_admin': CourseFinanceAdminRole(course_key).has_user(request.user),
        'sales_admin': CourseSalesAdminRole(course_key).has_user(request.user),
        'staff': bool(has_access(request.user, 'staff', course)),
        'forum_admin': has_forum_access(request.user, course_key, FORUM_ROLE_ADMINISTRATOR),
    }

    if not access['staff']:
        raise Http404()

    is_white_label = CourseMode.is_white_label(course_key)

    sections = [
        _section_course_info(course, access),
        _section_membership(course, access, is_white_label),
        _section_cohort_management(course, access),
        _section_student_admin(course, access),
        _section_data_download(course, access),
    ]

    analytics_dashboard_message = None
    if settings.ANALYTICS_DASHBOARD_URL:
        # Construct a URL to the external analytics dashboard
        analytics_dashboard_url = '{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, unicode(course_key))
        link_start = "<a href=\"{}\" target=\"_blank\">".format(analytics_dashboard_url)
        analytics_dashboard_message = _(
            "To gain insights into student enrollment and participation {link_start}"
            "visit {analytics_dashboard_name}, our new course analytics product{link_end}."
        )
        analytics_dashboard_message = analytics_dashboard_message.format(
            link_start=link_start, link_end="</a>", analytics_dashboard_name=settings.ANALYTICS_DASHBOARD_NAME)

        # Temporarily show the "Analytics" section until we have a better way of linking to Insights
        sections.append(_section_analytics(course, access))

    # Check if there is corresponding entry in the CourseMode Table related to the Instructor Dashboard course
    course_mode_has_price = False
    paid_modes = CourseMode.paid_modes_for_course(course_key)
    if len(paid_modes) == 1:
        course_mode_has_price = True
    elif len(paid_modes) > 1:
        log.error(
            u"Course %s has %s course modes with payment options. Course must only have "
            u"one paid course mode to enable eCommerce options.",
            unicode(course_key), len(paid_modes)
        )

    if settings.FEATURES.get('INDIVIDUAL_DUE_DATES') and access['instructor']:
        sections.insert(3, _section_extensions(course))

    # Gate access to course email by feature flag & by course-specific authorization
    if bulk_email_is_enabled_for_course(course_key):
        sections.append(_section_send_email(course, access))

    # Gate access to Metrics tab by featue flag and staff authorization
    if settings.FEATURES['CLASS_DASHBOARD'] and access['staff']:
        sections.append(_section_metrics(course, access))

    # Gate access to Ecommerce tab
    if course_mode_has_price and (access['finance_admin'] or access['sales_admin']):
        sections.append(_section_e_commerce(course, access, paid_modes[0], is_white_label, is_white_label))

    # Gate access to Special Exam tab depending if either timed exams or proctored exams
    # are enabled in the course

    # NOTE: For now, if we only have procotred exams enabled, then only platform Staff
    # (user.is_staff) will be able to view the special exams tab. This may
    # change in the future
    can_see_special_exams = (
        ((course.enable_proctored_exams and request.user.is_staff) or course.enable_timed_exams) and
        settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False)
    )
    if can_see_special_exams:
        sections.append(_section_special_exams(course, access))

    # Certificates panel
    # This is used to generate example certificates
    # and enable self-generated certificates for a course.
    certs_enabled = CertificateGenerationConfiguration.current().enabled
    if certs_enabled and access['admin']:
        sections.append(_section_certificates(course))

    disable_buttons = not _is_small_course(course_key)

    certificate_white_list = CertificateWhitelist.get_certificate_white_list(course_key)
    generate_certificate_exceptions_url = reverse(  # pylint: disable=invalid-name
        'generate_certificate_exceptions',
        kwargs={'course_id': unicode(course_key), 'generate_for': ''}
    )
    generate_bulk_certificate_exceptions_url = reverse(  # pylint: disable=invalid-name
        'generate_bulk_certificate_exceptions',
        kwargs={'course_id': unicode(course_key)}
    )
    certificate_exception_view_url = reverse(
        'certificate_exception_view',
        kwargs={'course_id': unicode(course_key)}
    )

    certificate_invalidation_view_url = reverse(  # pylint: disable=invalid-name
        'certificate_invalidation_view',
        kwargs={'course_id': unicode(course_key)}
    )

    certificate_invalidations = CertificateInvalidation.get_certificate_invalidations(course_key)

    context = {
        'course': course,
        'studio_url': get_studio_url(course, 'course'),
        'sections': sections,
        'disable_buttons': disable_buttons,
        'analytics_dashboard_message': analytics_dashboard_message,
        'certificate_white_list': certificate_white_list,
        'certificate_invalidations': certificate_invalidations,
        'generate_certificate_exceptions_url': generate_certificate_exceptions_url,
        'generate_bulk_certificate_exceptions_url': generate_bulk_certificate_exceptions_url,
        'certificate_exception_view_url': certificate_exception_view_url,
        'certificate_invalidation_view_url': certificate_invalidation_view_url,
    }

    return render_to_response('instructor/instructor_dashboard_2/instructor_dashboard_2.html', context)


## Section functions starting with _section return a dictionary of section data.

## The dictionary must include at least {
##     'section_key': 'circus_expo'
##     'section_display_name': 'Circus Expo'
## }

## section_key will be used as a css attribute, javascript tie-in, and template import filename.
## section_display_name will be used to generate link titles in the nav bar.


def _section_e_commerce(course, access, paid_mode, coupons_enabled, reports_enabled):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    coupons = Coupon.objects.filter(course_id=course_key).order_by('-is_active')
    course_price = paid_mode.min_price

    total_amount = None
    if access['finance_admin']:
        single_purchase_total = PaidCourseRegistration.get_total_amount_of_purchased_item(course_key)
        bulk_purchase_total = CourseRegCodeItem.get_total_amount_of_purchased_item(course_key)
        total_amount = single_purchase_total + bulk_purchase_total

    section_data = {
        'section_key': 'e-commerce',
        'section_display_name': _('E-Commerce'),
        'access': access,
        'course_id': unicode(course_key),
        'currency_symbol': settings.PAID_COURSE_REGISTRATION_CURRENCY[1],
        'ajax_remove_coupon_url': reverse('remove_coupon', kwargs={'course_id': unicode(course_key)}),
        'ajax_get_coupon_info': reverse('get_coupon_info', kwargs={'course_id': unicode(course_key)}),
        'get_user_invoice_preference_url': reverse('get_user_invoice_preference', kwargs={'course_id': unicode(course_key)}),
        'sale_validation_url': reverse('sale_validation', kwargs={'course_id': unicode(course_key)}),
        'ajax_update_coupon': reverse('update_coupon', kwargs={'course_id': unicode(course_key)}),
        'ajax_add_coupon': reverse('add_coupon', kwargs={'course_id': unicode(course_key)}),
        'get_sale_records_url': reverse('get_sale_records', kwargs={'course_id': unicode(course_key)}),
        'get_sale_order_records_url': reverse('get_sale_order_records', kwargs={'course_id': unicode(course_key)}),
        'instructor_url': reverse('instructor_dashboard', kwargs={'course_id': unicode(course_key)}),
        'get_registration_code_csv_url': reverse('get_registration_codes', kwargs={'course_id': unicode(course_key)}),
        'generate_registration_code_csv_url': reverse('generate_registration_codes', kwargs={'course_id': unicode(course_key)}),
        'active_registration_code_csv_url': reverse('active_registration_codes', kwargs={'course_id': unicode(course_key)}),
        'spent_registration_code_csv_url': reverse('spent_registration_codes', kwargs={'course_id': unicode(course_key)}),
        'set_course_mode_url': reverse('set_course_mode_price', kwargs={'course_id': unicode(course_key)}),
        'download_coupon_codes_url': reverse('get_coupon_codes', kwargs={'course_id': unicode(course_key)}),
        'enrollment_report_url': reverse('get_enrollment_report', kwargs={'course_id': unicode(course_key)}),
        'exec_summary_report_url': reverse('get_exec_summary_report', kwargs={'course_id': unicode(course_key)}),
        'list_financial_report_downloads_url': reverse('list_financial_report_downloads',
                                                       kwargs={'course_id': unicode(course_key)}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
        'look_up_registration_code': reverse('look_up_registration_code', kwargs={'course_id': unicode(course_key)}),
        'coupons': coupons,
        'sales_admin': access['sales_admin'],
        'coupons_enabled': coupons_enabled,
        'reports_enabled': reports_enabled,
        'course_price': course_price,
        'total_amount': total_amount
    }
    return section_data


def _section_special_exams(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id

    section_data = {
        'section_key': 'special_exams',
        'section_display_name': _('Special Exams'),
        'access': access,
        'course_id': unicode(course_key)
    }
    return section_data


def _section_certificates(course):
    """Section information for the certificates panel.

    The certificates panel allows global staff to generate
    example certificates and enable self-generated certificates
    for a course.

    Arguments:
        course (Course)

    Returns:
        dict

    """
    example_cert_status = None
    html_cert_enabled = certs_api.has_html_certificates_enabled(course.id, course)
    if html_cert_enabled:
        can_enable_for_course = True
    else:
        example_cert_status = certs_api.example_certificates_status(course.id)

        # Allow the user to enable self-generated certificates for students
        # *only* once a set of example certificates has been successfully generated.
        # If certificates have been misconfigured for the course (for example, if
        # the PDF template hasn't been uploaded yet), then we don't want
        # to turn on self-generated certificates for students!
        can_enable_for_course = (
            example_cert_status is not None and
            all(
                cert_status['status'] == 'success'
                for cert_status in example_cert_status
            )
        )
    instructor_generation_enabled = settings.FEATURES.get('CERTIFICATES_INSTRUCTOR_GENERATION', False)
    certificate_statuses_with_count = {
        certificate['status']: certificate['count']
        for certificate in GeneratedCertificate.get_unique_statuses(course_key=course.id)
    }

    return {
        'section_key': 'certificates',
        'section_display_name': _('Certificates'),
        'example_certificate_status': example_cert_status,
        'can_enable_for_course': can_enable_for_course,
        'enabled_for_course': certs_api.cert_generation_enabled(course.id),
        'instructor_generation_enabled': instructor_generation_enabled,
        'html_cert_enabled': html_cert_enabled,
        'active_certificate': certs_api.get_active_web_certificate(course),
        'certificate_statuses_with_count': certificate_statuses_with_count,
        'status': CertificateStatuses,
        'certificate_generation_history':
            CertificateGenerationHistory.objects.filter(course_id=course.id).order_by("-created"),
        'urls': {
            'generate_example_certificates': reverse(
                'generate_example_certificates',
                kwargs={'course_id': course.id}
            ),
            'enable_certificate_generation': reverse(
                'enable_certificate_generation',
                kwargs={'course_id': course.id}
            ),
            'start_certificate_generation': reverse(
                'start_certificate_generation',
                kwargs={'course_id': course.id}
            ),
            'start_certificate_regeneration': reverse(
                'start_certificate_regeneration',
                kwargs={'course_id': course.id}
            ),
            'list_instructor_tasks_url': reverse(
                'list_instructor_tasks',
                kwargs={'course_id': course.id}
            ),
        }
    }


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_POST
@login_required
def set_course_mode_price(request, course_id):
    """
    set the new course price and add new entry in the CourseModesArchive Table
    """
    try:
        course_price = int(request.POST['course_price'])
    except ValueError:
        return JsonResponse(
            {'message': _("Please Enter the numeric value for the course price")},
            status=400)  # status code 400: Bad Request

    currency = request.POST['currency']
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course_honor_mode = CourseMode.objects.filter(mode_slug='honor', course_id=course_key)
    if not course_honor_mode:
        return JsonResponse(
            {'message': _("CourseMode with the mode slug({mode_slug}) DoesNotExist").format(mode_slug='honor')},
            status=400)  # status code 400: Bad Request

    CourseModesArchive.objects.create(
        course_id=course_id, mode_slug='honor', mode_display_name='Honor Code Certificate',
        min_price=course_honor_mode[0].min_price, currency=course_honor_mode[0].currency,
        expiration_datetime=datetime.datetime.now(pytz.utc), expiration_date=datetime.date.today()
    )
    course_honor_mode.update(
        min_price=course_price,
        currency=currency
    )
    return JsonResponse({'message': _("CourseMode price updated successfully")})

def _section_my_students(course, access, is_white_label, user, class_code_list=None):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    ccx_enabled = settings.FEATURES.get('CUSTOM_COURSES_EDX', False) and course.enable_ccx
    section_data = {
        'section_key': 'membership',
        'section_display_name': _('My Students'),
        'access': access,
        'ccx_is_enabled': ccx_enabled,
        'class_code_list': class_code_list,
        'is_white_label': is_white_label,
        'list_students_of_class_code_url': reverse('list_students_of_class_code',kwargs={'course_id': unicode(course_key)}),
        'modify_students_of_class_code_url': reverse('modify_students_of_class_code',kwargs={'course_id': unicode(course_key)}),#TODO: ADD URLS IN
        'enroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'unenroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'upload_student_csv_button_url': reverse('register_and_enroll_students', kwargs={'course_id': unicode(course_key)}),
        'modify_beta_testers_button_url': reverse('bulk_beta_modify_access', kwargs={'course_id': unicode(course_key)}),
        'list_course_role_members_url': reverse('list_course_role_members', kwargs={'course_id': unicode(course_key)}),
        'modify_access_url': reverse('modify_access', kwargs={'course_id': unicode(course_key)}),
        'list_forum_members_url': reverse('list_forum_members', kwargs={'course_id': unicode(course_key)}),
        'update_forum_role_membership_url': reverse('update_forum_role_membership', kwargs={'course_id': unicode(course_key)}),
    }
    return section_data



def _section_course_info(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id

    section_data = {
        'section_key': 'course_info',
        'section_display_name': _('Course Info'),
        'access': access,
        'course_id': course_key,
        'course_display_name': course.display_name,
        'has_started': course.has_started(),
        'has_ended': course.has_ended(),
        'start_date': get_default_time_display(course.start),
        'end_date': get_default_time_display(course.end) or _('No end date set'),
        'num_sections': len(course.children),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
    }

    if settings.FEATURES.get('DISPLAY_ANALYTICS_ENROLLMENTS'):
        section_data['enrollment_count'] = CourseEnrollment.objects.enrollment_counts(course_key)

    if settings.ANALYTICS_DASHBOARD_URL:
        dashboard_link = _get_dashboard_link(course_key)
        message = _("Enrollment data is now available in {dashboard_link}.").format(dashboard_link=dashboard_link)
        section_data['enrollment_message'] = message

    if settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'):
        section_data['detailed_gitlogs_url'] = reverse('gitlogs_detail', kwargs={'course_id': unicode(course_key)})

    try:
        sorted_cutoffs = sorted(course.grade_cutoffs.items(), key=lambda i: i[1], reverse=True)
        advance = lambda memo, (letter, score): "{}: {}, ".format(letter, score) + memo
        section_data['grade_cutoffs'] = reduce(advance, sorted_cutoffs, "")[:-2]
    except Exception:  # pylint: disable=broad-except
        section_data['grade_cutoffs'] = "Not Available"
    # section_data['offline_grades'] = offline_grades_available(course_key)

    try:
        section_data['course_errors'] = [(escape(a), '') for (a, _unused) in modulestore().get_course_errors(course.id)]
    except Exception:  # pylint: disable=broad-except
        section_data['course_errors'] = [('Error fetching errors', '')]

    return section_data


def _section_membership(course, access, is_white_label):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    ccx_enabled = settings.FEATURES.get('CUSTOM_COURSES_EDX', False) and course.enable_ccx
    section_data = {
        'section_key': 'membership',
        'section_display_name': _('Membership'),
        'access': access,
        'ccx_is_enabled': ccx_enabled,
        'is_white_label': is_white_label,
        'enroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'unenroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'upload_student_csv_button_url': reverse('register_and_enroll_students', kwargs={'course_id': unicode(course_key)}),
        'modify_beta_testers_button_url': reverse('bulk_beta_modify_access', kwargs={'course_id': unicode(course_key)}),
        'list_course_role_members_url': reverse('list_course_role_members', kwargs={'course_id': unicode(course_key)}),
        'modify_access_url': reverse('modify_access', kwargs={'course_id': unicode(course_key)}),
        'list_forum_members_url': reverse('list_forum_members', kwargs={'course_id': unicode(course_key)}),
        'update_forum_role_membership_url': reverse('update_forum_role_membership', kwargs={'course_id': unicode(course_key)}),
    }
    return section_data


def _section_cohort_management(course, access):
    """ Provide data for the corresponding cohort management section """
    course_key = course.id
    section_data = {
        'section_key': 'cohort_management',
        'section_display_name': _('Cohorts'),
        'access': access,
        'course_cohort_settings_url': reverse(
            'course_cohort_settings',
            kwargs={'course_key_string': unicode(course_key)}
        ),
        'cohorts_url': reverse('cohorts', kwargs={'course_key_string': unicode(course_key)}),
        'upload_cohorts_csv_url': reverse('add_users_to_cohorts', kwargs={'course_id': unicode(course_key)}),
        'discussion_topics_url': reverse('cohort_discussion_topics', kwargs={'course_key_string': unicode(course_key)}),
    }
    return section_data


def _is_small_course(course_key):
    """ Compares against MAX_ENROLLMENT_INSTR_BUTTONS to determine if course enrollment is considered small. """
    is_small_course = False
    enrollment_count = CourseEnrollment.objects.num_enrolled_in(course_key)
    max_enrollment_for_buttons = settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")
    if max_enrollment_for_buttons is not None:
        is_small_course = enrollment_count <= max_enrollment_for_buttons
    return is_small_course


def _section_student_admin(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    is_small_course = _is_small_course(course_key)

    section_data = {
        'section_key': 'student_admin',
        'section_display_name': _('Student Admin'),
        'access': access,
        'is_small_course': is_small_course,
        'get_student_progress_url_url': reverse('get_student_progress_url', kwargs={'course_id': unicode(course_key)}),
        'enrollment_url': reverse('students_update_enrollment', kwargs={'course_id': unicode(course_key)}),
        'reset_student_attempts_url': reverse('reset_student_attempts', kwargs={'course_id': unicode(course_key)}),
        'reset_student_attempts_for_entrance_exam_url': reverse(
            'reset_student_attempts_for_entrance_exam',
            kwargs={'course_id': unicode(course_key)},
        ),
        'rescore_problem_url': reverse('rescore_problem', kwargs={'course_id': unicode(course_key)}),
        'rescore_entrance_exam_url': reverse('rescore_entrance_exam', kwargs={'course_id': unicode(course_key)}),
        'student_can_skip_entrance_exam_url': reverse(
            'mark_student_can_skip_entrance_exam',
            kwargs={'course_id': unicode(course_key)},
        ),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
        'list_entrace_exam_instructor_tasks_url': reverse('list_entrance_exam_instructor_tasks',
                                                          kwargs={'course_id': unicode(course_key)}),
        'spoc_gradebook_url': reverse('spoc_gradebook', kwargs={'course_id': unicode(course_key)}),
    }
    return section_data


def _section_extensions(course):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'extensions',
        'section_display_name': _('Extensions'),
        'units_with_due_dates': [(title_or_url(unit), unicode(unit.location))
                                 for unit in get_units_with_due_date(course)],
        'change_due_date_url': reverse('change_due_date', kwargs={'course_id': unicode(course.id)}),
        'reset_due_date_url': reverse('reset_due_date', kwargs={'course_id': unicode(course.id)}),
        'show_unit_extensions_url': reverse('show_unit_extensions', kwargs={'course_id': unicode(course.id)}),
        'show_student_extensions_url': reverse('show_student_extensions', kwargs={'course_id': unicode(course.id)}),
    }
    return section_data


def _section_data_download(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id

    show_proctored_report_button = (
        settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False) and
        course.enable_proctored_exams
    )

    section_data = {
        'section_key': 'data_download',
        'section_display_name': _('Data Download'),
        'access': access,
        'show_generate_proctored_exam_report_button': show_proctored_report_button,
        'get_problem_responses_url': reverse('get_problem_responses', kwargs={'course_id': unicode(course_key)}),
        'get_grading_config_url': reverse('get_grading_config', kwargs={'course_id': unicode(course_key)}),
        'get_students_features_url': reverse('get_students_features', kwargs={'course_id': unicode(course_key)}),
        'get_issued_certificates_url': reverse(
            'get_issued_certificates', kwargs={'course_id': unicode(course_key)}
        ),
        'get_students_who_may_enroll_url': reverse(
            'get_students_who_may_enroll', kwargs={'course_id': unicode(course_key)}
        ),
        'get_anon_ids_url': reverse('get_anon_ids', kwargs={'course_id': unicode(course_key)}),
        'list_proctored_results_url': reverse('get_proctored_exam_results', kwargs={'course_id': unicode(course_key)}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
        'list_report_downloads_url': reverse('list_report_downloads', kwargs={'course_id': unicode(course_key)}),
        'calculate_grades_csv_url': reverse('calculate_grades_csv', kwargs={'course_id': unicode(course_key)}),
        'problem_grade_report_url': reverse('problem_grade_report', kwargs={'course_id': unicode(course_key)}),
        'course_has_survey': True if course.course_survey_name else False,
        'course_survey_results_url': reverse('get_course_survey_results', kwargs={'course_id': unicode(course_key)}),
    }
    return section_data

def _section_grade_centre(course, access,class_code_list):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    assignment_names = get_assignment_names(course_key)

    section_data = {
        'section_key': 'data_download',
        'section_display_name': _('Grade Centre'),
        'access': access,
        'gradebook_url':reverse('teacher_gradebook_min', kwargs={'course_id': unicode(course_key)}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': unicode(course_key)}),
        'list_report_downloads_url': reverse('list_report_downloads', kwargs={'course_id': unicode(course_key)}),
        'calculate_grades_csv_url': reverse('calculate_grades_csv_class_code', kwargs={'course_id': unicode(course_key)}),
        'problem_grade_report_url': reverse('problem_grade_report', kwargs={'course_id': unicode(course_key)}),
        'submissions_report_url': reverse('submissions_report', kwargs={'course_id': unicode(course_key)}),
        'download_class_submissions_url': reverse('download_class_submissions', kwargs={'course_id': unicode(course_key)}),
        'class_code_list': class_code_list,
        'assignment_names': assignment_names,
    }
    return section_data

def _section_competition_submission(course,access,class_code_list):
    """ Provide data for the corresponding dashboard section """
    
    course_key = course.id
    section_data = {
        'section_key': 'competition_submission',
        'section_display_name': _('Competition'),
        'access': access,
        #'submit_entry_url': reverse('', kwargs={'course_id': unicode(course_key)}),
        'upload_file_url': 'upload_file',
        'class_code_list': class_code_list,
        'competition_submission_form': CompetitionSubmissionForm(),
        'video_upload_errors': "",
        'video_url_errors': "",
        'media_release_upload_errors': "",
        'src_upload_errors': "",
        'success': False,
        'error_msg': False,
    }
    return section_data

def null_applicable_aside_types(block):  # pylint: disable=unused-argument
    """
    get_aside method for monkey-patching into applicable_aside_types
    while rendering an HtmlDescriptor for email text editing. This returns
    an empty list.
    """
    return []


def _section_send_email(course, access):
    """ Provide data for the corresponding bulk email section """
    course_key = course.id

    # Monkey-patch applicable_aside_types to return no asides for the duration of this render
    with patch.object(course.runtime, 'applicable_aside_types', null_applicable_aside_types):
        # This HtmlDescriptor is only being used to generate a nice text editor.
        html_module = HtmlDescriptor(
            course.system,
            DictFieldData({'data': ''}),
            ScopeIds(None, None, None, course_key.make_usage_key('html', 'fake'))
        )
        fragment = course.system.render(html_module, 'studio_view')
    fragment = wrap_xblock(
        'LmsRuntime', html_module, 'studio_view', fragment, None,
        extra_data={"course-id": unicode(course_key)},
        usage_id_serializer=lambda usage_id: quote_slashes(unicode(usage_id)),
        # Generate a new request_token here at random, because this module isn't connected to any other
        # xblock rendering.
        request_token=uuid.uuid1().get_hex()
    )
    email_editor = fragment.content
    section_data = {
        'section_key': 'send_email',
        'section_display_name': _('Email'),
        'access': access,
        'send_email': reverse('send_email', kwargs={'course_id': unicode(course_key)}),
        'editor': email_editor,
        'list_instructor_tasks_url': reverse(
            'list_instructor_tasks', kwargs={'course_id': unicode(course_key)}
        ),
        'email_background_tasks_url': reverse(
            'list_background_email_tasks', kwargs={'course_id': unicode(course_key)}
        ),
        'email_content_history_url': reverse(
            'list_email_content', kwargs={'course_id': unicode(course_key)}
        ),
    }
    return section_data


def _get_dashboard_link(course_key):
    """ Construct a URL to the external analytics dashboard """
    analytics_dashboard_url = '{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, unicode(course_key))
    link = u"<a href=\"{0}\" target=\"_blank\">{1}</a>".format(analytics_dashboard_url,
                                                               settings.ANALYTICS_DASHBOARD_NAME)
    return link


def _section_analytics(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    analytics_dashboard_url = '{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, unicode(course_key))
    link_start = "<a href=\"{}\" target=\"_blank\">".format(analytics_dashboard_url)
    insights_message = _("For analytics about your course, go to {analytics_dashboard_name}.")

    insights_message = insights_message.format(
        analytics_dashboard_name=u'{0}{1}</a>'.format(link_start, settings.ANALYTICS_DASHBOARD_NAME)
    )
    section_data = {
        'section_key': 'instructor_analytics',
        'section_display_name': _('Analytics'),
        'access': access,
        'insights_message': insights_message,
    }

    return section_data


def _section_metrics(course, access):
    """Provide data for the corresponding dashboard section """
    course_key = course.id
    section_data = {
        'section_key': 'metrics',
        'section_display_name': _('Metrics'),
        'access': access,
        'course_id': unicode(course_key),
        'sub_section_display_name': get_section_display_name(course_key),
        'section_has_problem': get_array_section_has_problem(course_key),
        'get_students_opened_subsection_url': reverse('get_students_opened_subsection'),
        'get_students_problem_grades_url': reverse('get_students_problem_grades'),
        'post_metrics_data_csv_url': reverse('post_metrics_data_csv'),
    }
    return section_data

@xframe_options_exempt
@staff_member_required
def tawk_admin(request):
    context = {}
    return render_to_response('instructor/tawk_admin.html', context)

def get_user_school_summary(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden()

    identifier = request.GET.get("identifier")
    try:
        student = get_student_from_identifier(identifier)
        response = {"success": True,
                    "data" : _get_user_info(student)}
    except User.DoesNotExist:
        response = {"success": False,
                    "msg": "No user found"}
    return JsonResponse(response)

def _get_user_info(user):
    response = {}
    response["username"]= user.username
    response["email"]= user.email
    response["gender"]= user.profile.gender
    response["first_name"]= user.first_name
    #add first name, username, email, gender
    if is_teacher(user):
        #account type
        #show school
        response["last_name"]= user.last_name
        response["user_type"] = "teacher"
        response["school"] = user.teacherprofile.school.__unicode__()
        response["classes"] = []
        classes = get_my_classes(user)
        #show classes by classcode and how many students in each
        for c in classes:
            c_dict = {}
            c_dict["class_code"]= c.class_code
            c_dict["size"]= get_class_size(c,is_active=True)
            response["classes"].append(c_dict)
        
    #if user has studentprofile
    elif is_student(user):
        response["user_type"] = "student"
        response["grade"] = user.studentprofile.school_grade
        #account type
        classes = get_student_class_info(user)
        if not classes:
            classes = "Orphaned account. This student has no class"
        response["classes"] = classes
    return response   
