from submissions import api as sub_api
import re
from instructor_task.tasks_helper import _order_problems
from instructor.views.api import _order_problems as order_submissions
from student.models import ClassSet, CourseEnrollment,anonymous_id_for_user
from django.contrib.auth.models import User
from collections import OrderedDict
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from itertools import chain

from opaque_keys.edx.locations import SlashSeparatedCourseKey

course_id=SlashSeparatedCourseKey.from_deprecated_string('course-v1:edX+DemoX+Demo_Course')


class_code = "TTEA1589"
enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
class_set = ClassSet.objects.get(class_code=class_code)
class_students = enrolled_students.filter(studentprofile__classSet=class_set)


header_row = OrderedDict([('id', 'Student ID'), ('email', 'Email'), ('username', 'Username'),('first_name','First Name'),('last_name','Last Name')])

#s_list = [{"username":s.username,"first_name":s.first_name,"last_name":s.last_name,"email":s.email ,"anon_id": anonymous_id_for_user(s,course_id,save=False)} for s in students]

#try:
course_structure = CourseStructure.objects.get(course_id=course_id)
blocks = course_structure.ordered_blocks
problems = order_submissions(blocks)
problems2 = _order_problems(blocks)
#except CourseStructure.DoesNotExist:
#    return task_progress.update_task_state(
#        extra_meta={'step': 'Generating course structure. Please refresh and try again.'}
#    )

# Just generate the static fields for now.
#print ("problems.values():")
#print problems.values()
#print ("problems2.values():")
#print problems2.values()

header = list(header_row.values())

for p in problems:
    header.append(re.sub(" Questions","",problems[p]["chapter"])+": "+unicode(problems[p]["section_number"])+"_"+problems[p]["section_name"]+" - "+problems[p]["problem_name"])
rows = [header]

error_rows = [list(header_row.values()) + ['error_msg']]
current_step = {'step': 'Calculating Grades'}

#for student, gradeset, err_msg in iterate_grades_for(course_id, enrolled_students, keep_raw_scores=True):
#    student_fields = [getattr(student, field_name) for field_name in header_row]
#    task_progress.attempted += 1

for student in class_students:
    for p in problems:
        student_fields = [getattr(student, field_name) for field_name in header_row]
        student_dict = {
            'student_id': anonymous_id_for_user(student,course_id,save=False),
            'item_id': p,
            'course_id': course_id, 
            'item_type':'sga', 
        }
        sub = sub_api.get_submissions(student_dict)
        if sub:
            student_fields = student_fields + ['true']
        else:
            student_fields = student_fields + ['false']
    print student_fields
    rows.append(student_fields)
