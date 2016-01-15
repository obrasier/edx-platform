var edx = edx || {},
    Language = (function($) {
        'use strict';
        var lang_edx = {

            init: function() {
                lang_edx.listenForLanguagePreferenceChange();
            },

            /**
             * Listener on changing language from selector.
             * Send an ajax request to save user language preferences.
             */
            listenForLanguagePreferenceChange: function() {
                $("#settings-language-value").change(function(event) {
                    event.preventDefault();
                    // ajax request to save user language preferences.
                    $.ajax({
                        type: 'PATCH',
                        data: JSON.stringify({'pref-lang': this.value}),
                        url: $('#preference-api-url').val(),
                        dataType: 'json',
                        contentType: "application/merge-patch+json",
                        beforeSend: function (xhr) {
                            xhr.setRequestHeader("X-CSRFToken", $('#csrf_token').val());
                        },
                        success: function () {
                            // User language preference has been set successfully
                            // Now submit the form in success callback.
                            $("#settings-form").submit();
                        },
                        error: function () {
                            document.location.reload();
                        }
                    });
                });
            }

        };
        return {
            init: lang_edx.init
        };

    })(jQuery);

    edx.language = Language;
    edx.language.init();
