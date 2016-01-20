"""
Exceptions related to the handling of profile images
"""

from django.utils.translation import ugettext as _

class ImageValidationError(Exception):
    """
    Exception to use when the system rejects a user-supplied source image.
    """
    @property
    def user_message(self):
        """
        Translate the developer-facing exception message for API clients.
        """
        # pylint: disable=translation-of-non-string
        return _(self.message)
