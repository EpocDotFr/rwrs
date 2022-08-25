/**
 * The RWR Account Deletion feature logic.
 */
rwrAccountDeletion = {
    /**
     * Initialize the feature.
     */
    init: function() {
        var self = this;
        var submitting = false;

        this.$rwr_account_deletion_form = $('form#rwr-account-deletion-form');
        this.$rwr_account_deletion_form_submit = $('button#rwr-account-deletion-form-submit');

        this.$rwr_account_deletion_form.on('submit', function(e) {
            if (submitting) {
                e.preventDefault();
            }

            self.$rwr_account_deletion_form_submit.prop('disabled', true);

            submitting = true;
        });
    }
};