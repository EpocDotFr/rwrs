/**
 * The Personal Access Token regeneration feature logic.
 */
regeneratePat = {
    /**
     * Initialize the feature.
     */
    init: function() {
        var self = this;

        this.$regenerate_pat_button = $('button.regenerate-pat');
        this.$pat_input = $('input.pat');

        this.$regenerate_pat_button.on('click', function() {
            if (!confirm('This will disallow all applications that are using the current token. Confirm?')) {
                return false;
            }

            $(this).prop('disabled', true);

            self.regeneratePat();
        });
    },
    /**
     * Actually regenerate the Personal Access Token.
     */
    regeneratePat: function() {
        var self = this;

        $.ajax({
            type: 'POST',
            url: self.endpoint,
            contentType: 'application/json',
            success: function(response, status, xhr) {
                if (response.status != 'success') {
                    alert(response.data.message);
                } else {
                    self.$pat_input.val(response.data.new_pat);
                }
            },
            error: function(xhr, errorType, error) {
                try {
                    var response = JSON.parse(xhr.responseText);
                    message = response.data.message;
                } catch (e) {
                    message = error;
                }

                alert(message);
            },
            complete: function() {
                self.$regenerate_pat_button.prop('disabled', false);
            }
        });
    }
};