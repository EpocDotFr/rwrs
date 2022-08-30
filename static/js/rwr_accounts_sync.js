/**
 * The RWR Accounts Sync feature logic.
 */
rwrAccountsSync = {
    /**
     * Initialize the feature.
     */
    init: function() {
        var self = this;

        this.$sync_rwr_accounts_buttons = document.querySelectorAll('button.sync-rwr-accounts');

        this.$sync_rwr_accounts_buttons.forEach(function(el) {
            el.addEventListener('click', function() {
                self.sync(this);
            });
        });
    },
    /**
     * Actually sync RWR accounts.
     */
   sync: function(button) {
        button.disabled = true;

        var database = button.dataset.database;

        $.ajax({
            type: 'POST',
            url: this.endpoints[database],
            contentType: 'application/json',
            success: function(response, status, xhr) {
                if (response.status != 'success') {
                    alert(response.data.message);
                } else {
                    window.location.href = window.location.href;
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
                button.disabled = false;
            }
        });
    }
};