"""
Models.
"""
from django.utils.translation import ugettext_lazy as _

from django.db.models import TextField

from config_models.models import ConfigurationModel


class XBlockDisableConfig(ConfigurationModel):
    """
    Configuration for disabling XBlocks.
    """

    class Meta(ConfigurationModel.Meta):
        app_label = 'xblock_django'

    disabled_blocks = TextField(
        default='', blank=True,
        help_text=_('Space-separated list of XBlocks which should not render.')
    )

    @classmethod
    def is_block_type_disabled(cls, block_type):
        """ Return True if block_type is disabled. """

        config = cls.current()
        if not config.enabled:
            return False

        return block_type in config.disabled_blocks.split()

    @classmethod
    def disabled_block_types(cls):
        """ Return list of disabled xblock types. """

        config = cls.current()
        if not config.enabled:
            return ()

        return config.disabled_blocks.split()


class XBlockDeprecatedAdvancedComponentConfig(ConfigurationModel):
    """
    Configuration for deprecated XBlocks that should not be created in Studio.
    """

    class Meta(ConfigurationModel.Meta):
        app_label = 'xblock_django'

    disabled_blocks = TextField(
        default='', blank=True,
        help_text=_(
            "Adding components in this list will disable the creation of new problem for "
            "those components in Studio. Existing problems will work fine and one can edit"
            "them in Studio."
        )
    )

    @classmethod
    def disabled_block_types(cls):
        """ Return list of deprecated xblock types. """

        config = cls.current()
        if not config.enabled:
            return ()

        return config.disabled_blocks.split()

    @classmethod
    def __unicode__(cls):
        config = cls.current()
        return u"Deprectaed xblock types are {deprectated_xblocks}".format(deprectaed_xblocks=config.disabled_blocks)
