"""
    Helpers for accessing comprehensive theming related variables.
"""
from microsite_configuration import microsite
from microsite_configuration import page_title_breadcrumbs
from django.conf import settings


def get_page_title_breadcrumbs(*args):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return page_title_breadcrumbs(*args)


def get_value(val_name, default=None, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.get_value(val_name, default=default, **kwargs)


def get_template_path(relative_path, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.get_template_path(relative_path, **kwargs)


def get_themed_template_path(relative_path, default_path, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.

    It returns path of the themed template (i.e. relative_path) if theming is enabled AND microsite is disabled
     otherwise it will return path of the microsite's or lms template.

    :param relative_path: relative path of themed template
    :param default_path: relative path of the microsite's or lms template to use if
        theming is disabled or microsite is enabled
    """
    is_theme_enabled = settings.FEATURES.get("USE_CUSTOM_THEME", False)
    is_microsite = microsite.is_request_in_microsite()
    if is_theme_enabled and not is_microsite:
        return relative_path
    return microsite.get_template_path(default_path, **kwargs)
