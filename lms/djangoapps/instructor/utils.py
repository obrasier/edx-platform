"""
Helpers for instructor app.
"""
import json
import pytz
import datetime

from xmodule.modulestore.django import modulestore

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module
from student.models import ClassSet, StudentProfile, CompetitionSubmission

class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        self.session = {}
        self.user = None
        return

    def get_host(self):
        """Return a default host."""
        return 'edx.mit.edu'

    def is_secure(self):
        """Always insecure."""
        return False


def get_module_for_student(student, usage_key, request=None, course=None):
    """Return the module for the (student, location) using a DummyRequest."""
    if request is None:
        request = DummyRequest()
        request.user = student

    descriptor = modulestore().get_item(usage_key, depth=0)
    field_data_cache = FieldDataCache([descriptor], usage_key.course_key, student)
    return get_module(student, request, usage_key, field_data_cache, course=course)

def get_users_by_class_code(class_code):
    class_set = get_class_set_by_class_code(class_code)
    # then find studentProfiles related to classSet
    # then find Users related to studentProfiles
    #if use map function. Then need a function that can retrieve its user from profile. 
    user_list = get_users_by_class_set(class_set)
    return user_list


def get_class_set_by_class_code(code):
    try:
        result=ClassSet.objects.get(class_code=code)
    except ClassSet.DoesNotExist:
        result = None
    return result

def get_users_by_class_set(class_set):
    student_list = StudentProfile.objects.filter(classSet= class_set)
    user_list = map(get_user_by_studentprofile,student_list)
    return user_list

def get_user_by_studentprofile(student_profile):
    user = student_profile.user
    return user

def get_class_codes_of_teacher(teacher_user, course_key):
    
    #course = get_course_with_access(
    #    user, 'teacher', course_id, depth=None
    #)
    class_set_list = ClassSet.objects.filter(teacher=teacher_user,course_id=course_key)
    def extract_class_info(class_set):
        return {
            'class_code': class_set.class_code,
            'short_name': class_set.short_name,
            'class_name': class_set.class_name,
        }
    return map(extract_class_info,class_set_list)

def get_competition_submissions(class_code):
    submissions = CompetitionSubmission.objects.filter(class_set__class_code=class_code).order_by('-attempt_number')
    if submissions.count()>0:
        return submissions[0]
    else:
        return None
    
def get_last_submission_summary(class_code):
    sub = get_competition_submissions(class_code)
    if sub:
        count = 0
        video = json.loads(sub.video_entry)
        media = json.loads(sub.media_release)
        src = json.loads(sub.src_code_entry)

        if video.get('video_file_name',None):
            count+=1
        if media.get('media_file_names',None):
            count+=len(media['media_file_names'])
        if src.get('src_file_names',None):
            count+=len(media['src_file_names'])

        return {
                'class_code':class_code,
                'attempt': sub.attempt_number,
                'received': sub.submitted_at.astimezone(pytz.timezone('Australia/Sydney')).strftime("%Y-%m-%d %H:%M %Z"),
                'files': count,
                'url': video.get('url',None),
        }
    else:
        return None
