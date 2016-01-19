"""
Image file manipulation functions related to profile images.
"""
from cStringIO import StringIO
from collections import namedtuple
from contextlib import closing

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _
import piexif
from PIL import Image

from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_storage


ImageType = namedtuple('ImageType', ('extensions', 'mimetypes', 'magic'))

IMAGE_TYPES = {
    'jpeg': ImageType(
        extensions=['.jpeg', '.jpg'],
        mimetypes=['image/jpeg', 'image/pjpeg'],
        magic=['ffd8'],
    ),
    'png': ImageType(
        extensions=[".png"],
        mimetypes=['image/png'],
        magic=["89504e470d0a1a0a"],
    ),
    'gif': ImageType(
        extensions=[".gif"],
        mimetypes=['image/gif'],
        magic=["474946383961", "474946383761"],
    ),
}


def user_friendly_size(size):
    """
    Convert size in bytes to user friendly size.

    Arguments:
        size (int): size in bytes

    Returns:
        user friendly size
    """
    units = [_('bytes'), _('KB'), _('MB')]
    i = 0
    while size >= 1024:
        size /= 1024
        i += 1
    return u'{} {}'.format(size, units[i])


def get_valid_file_types():
    """
    Return comma separated string of valid file types.
    """
    return ', '.join([', '.join(IMAGE_TYPES[ft].extensions) for ft in IMAGE_TYPES.keys()])


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


def validate_uploaded_image(uploaded_file):
    """
    Raises ImageValidationError if the server should refuse to use this
    uploaded file as the source image for a user's profile image.  Otherwise,
    returns nothing.
    """

    # validation code by @pmitros,
    # adapted from https://github.com/pmitros/ProfileXBlock
    # see also: http://en.wikipedia.org/wiki/Magic_number_%28programming%29

    if uploaded_file.size > settings.PROFILE_IMAGE_MAX_BYTES:
        file_upload_too_large = _(
            u'The file must be smaller than {image_max_size} in size.'
        ).format(
            image_max_size=user_friendly_size(settings.PROFILE_IMAGE_MAX_BYTES)
        )
        raise ImageValidationError(file_upload_too_large)
    elif uploaded_file.size < settings.PROFILE_IMAGE_MIN_BYTES:
        file_upload_too_small = _(
            u'The file must be at least {image_min_size} in size.'
        ).format(
            image_min_size=user_friendly_size(settings.PROFILE_IMAGE_MIN_BYTES)
        )
        raise ImageValidationError(file_upload_too_small)

    # check the file extension looks acceptable
    filename = unicode(uploaded_file.name).lower()
    filetype = [ft for ft in IMAGE_TYPES if any(filename.endswith(ext) for ext in IMAGE_TYPES[ft].extensions)]
    if not filetype:
        file_upload_bad_type = _(
            u'The file must be one of the following types: {valid_file_types}.'
        ).format(valid_file_types=get_valid_file_types())
        raise ImageValidationError(file_upload_bad_type)
    filetype = filetype[0]

    # check mimetype matches expected file type
    if uploaded_file.content_type not in IMAGE_TYPES[filetype].mimetypes:
        file_upload_bad_mimetype = _(
            u'The Content-Type header for this file does not match '
            u'the file data. The file may be corrupted.'
        )
        raise ImageValidationError(file_upload_bad_mimetype)

    # check magic number matches expected file type
    headers = IMAGE_TYPES[filetype].magic
    if uploaded_file.read(len(headers[0]) / 2).encode('hex') not in headers:
        file_upload_bad_ext = _(
            u'The file name extension for this file does not match '
            u'the file data. The file may be corrupted.'
        )
        raise ImageValidationError(file_upload_bad_ext)
    # avoid unexpected errors from subsequent modules expecting the fp to be at 0
    uploaded_file.seek(0)


def _crop_image_to_square(image):
    """
    Given a PIL.Image object, return a copy cropped to a square around the
    center point with each side set to the size of the smaller dimension.
    """
    width, height = image.size
    if width != height:
        side = width if width < height else height
        image = image.crop(((width - side) / 2, (height - side) / 2, (width + side) / 2, (height + side) / 2))
    return image


def _set_color_mode_to_rgb(image_obj):
    if image_obj.mode != 'RGB':
        return image_obj.convert('RGB')
    else:
        return image_obj


def _scale_image(image, size):
    """
    Given a PIL.Image object, get a resized copy using `size` (square)
    """
    return image.resize((size, size), Image.ANTIALIAS)


def _create_image_file(image_obj):
    """
    Given a PIL.Image object, get a resized copy using `size` (square) and
    return a file-like object containing the data saved as a JPEG.

    Note that the file object returned is a django ContentFile which holds
    data in memory (not on disk).
    """
    string_io = StringIO()
    image_obj.save(string_io, format='JPEG')
    image_file = ContentFile(string_io.getvalue())
    return image_file


def _get_exif_orientation(image):
    """Return the orientation value for the given Image object"""
    if 'exif' in image.info:
        return image.info['exif']['0th'].get(piexif.ImageIFD.Orientation)



def create_profile_images(image_file, profile_image_names):
    """
    Generates a set of image files based on image_file and
    stores them according to the sizes and filenames specified
    in `profile_image_names`.
    """
    image_obj = Image.open(image_file)

    image_obj = _set_color_mode_to_rgb(image_obj)
    image_obj = _crop_image_to_square(image_obj)

    storage = get_profile_image_storage()
    for size, name in profile_image_names.items():
        scaled = _scale_image(image_obj, size)
        with closing(_create_image_file(scaled)) as scaled_image_file:
            storage.save(name, scaled_image_file)


def remove_profile_images(profile_image_names):
    """
    Physically remove the image files specified in `profile_image_names`
    """
    storage = get_profile_image_storage()
    for name in profile_image_names.values():
        storage.delete(name)
