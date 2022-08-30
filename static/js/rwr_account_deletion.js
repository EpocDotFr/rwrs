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

        this.$rwr_account_deletion_form = document.querySelector('form#rwr-account-deletion-form');
        this.$rwr_account_deletion_form_submit = document.querySelector('button#rwr-account-deletion-form-submit');

        this.$rwr_account_deletion_form.addEventListener('submit', function(e) {
            if (submitting) {
                e.preventDefault();
            } else {
                self.$rwr_account_deletion_form_submit.disabled = true;

                submitting = true;
            }
        });
    }
};