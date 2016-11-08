#from instructor.views.api import _get_assignmen_names
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.djangoapps.content.course_structures.models import CourseStructure

blocks = CourseStructure.objects.get(course_id=SlashSeparatedCourseKey.from_deprecated_string('course-v1:edX+DemoX+Demo_Course')).ordered_blocks
assignments = []

for block in blocks:
    if blocks[block]['block_type']=='sequential':
        block_format = blocks[block]['format']
        if unicode(block_format) not in assignments and not unicode(block_format)=="None":
            assignments.extend([unicode(block_format)])
