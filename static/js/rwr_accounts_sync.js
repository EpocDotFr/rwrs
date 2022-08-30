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

        fetch(this.endpoints[database], {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }).then(function (response) {
            if (response.ok) {
                return response.json();
            } else {
                return Promise.reject(response);
            }
        }).then(function (response) {
            if (response.status != 'success') {
                button.disabled = false;

                alert(response.data.message);
            } else {
                window.location.href = window.location.href;
            }
        }).catch(function (error) {
            button.disabled = false;

            alert(error);
        });
    }
};