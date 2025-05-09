/**
 * The RWR Accounts Clear credentials feature logic.
 */
rwrAccountsClear = {
    /**
     * Initialize the feature.
     */
    init: function() {
        var self = this;

        this.$clear_rwr_account_credentials_buttons = document.querySelectorAll('a.clear-rwr-account-credentials');

        this.$clear_rwr_account_credentials_buttons.forEach(function(el) {
            el.addEventListener('click', function(e) {
                e.preventDefault();

                if (!confirm('Confirm clearing this account\'s credentials?\n\nIf you do not understand what you are doing, or if someone did not asked you to click on that button, do not proceed.')) {
                    e.preventDefault();

                    return false;
                }

                self.clear(this);
            });
        });
    },
    /**
     * Actually clear RWR account credentials.
     */
   clear: function(button) {
        button.disabled = true;

        fetch(`${this.endpoint}${button.dataset.accountId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }).then(function(response) {
            return response.json();
        }).then(function(response) {
            if (response.status != 'success') {
                alert(response.data.message);
            } else {
                alert('Credentials have been cleared successfully for this account.');
            }

            button.disabled = false;
        }).catch(function(error) {
            alert(error);

            button.disabled = false;
        });
    }
};