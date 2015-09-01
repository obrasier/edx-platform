""" API v1 views. """
import logging

from django.http import Http404
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated

from commerce.api.v1.models import Course
from commerce.api.v1.permissions import ApiKeyOrModelPermission
from commerce.api.v1.serializers import CourseSerializer
from course_modes.models import CourseMode

log = logging.getLogger(__name__)


class CourseListView(ListAPIView):
    """ List courses and modes. """
    authentication_classes = (OAuth2Authentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseSerializer

    def get_queryset(self):
        return Course.iterator()


class CourseRetrieveUpdateView(RetrieveUpdateAPIView, CreateModelMixin):
    """ Retrieve, update, or create courses/modes. """
    lookup_field = 'course_id'
    lookup_url_kwarg = 'course_id'
    model = CourseMode
    authentication_classes = (OAuth2Authentication, SessionAuthentication,)
    permission_classes = (ApiKeyOrModelPermission,)
    serializer_class = CourseSerializer

    # TODO -- explain this more
    queryset = CourseMode.objects.all()

    def get_object(self, queryset=None):
        course_id = self.kwargs.get(self.lookup_url_kwarg)
        course = Course.get(course_id)

        if course:
            return course

        raise Http404

    def update(self, request, *args, **kwargs):
        # First, try to update the existing instance
        try:
            return super(CourseRetrieveUpdateView, self).update(request, *args, **kwargs)
        except Http404:
            # If no instance exists yet, create it.
            # This is backwards-compatible with Django Rest Framework v2.
            return super(CourseRetrieveUpdateView, self).create(request, *args, **kwargs)

    def pre_save(self, obj):
        # There is nothing to pre-save. The default behavior changes the Course.id attribute from
        # a CourseKey to a string, which is not desired.
        pass
