/**
 * The Personal Access Token regeneration feature logic.
 */
regeneratePat = {
    /**
     * Initialize the feature.
     */
    init: function() {
        var self = this;

        this.$regenerate_pat_button = document.querySelector('button.regenerate-pat');
        this.$pat_input = document.querySelector('input.pat');

        this.$regenerate_pat_button.addEventListener('click', function() {
            if (!confirm('This will disallow all applications that are using the current token. Confirm?')) {
                return false;
            }

            this.disabled = true;

            self.regeneratePat();
        });
    },
    /**
     * Actually regenerate the Personal Access Token.
     */
    regeneratePat: function() {
        var self = this;

        fetch(this.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }).then(function(response) {
            if (response.ok) {
                return response.json();
            } else {
                return Promise.reject(response);
            }
        }).then(function(response) {
            if (response.status != 'success') {
                alert(response.data.message);
            } else {
                self.$pat_input.value = response.data.new_pat;
            }

            self.$regenerate_pat_button.disabled = false;
        }).catch(function(error) {
            alert(error);

            self.$regenerate_pat_button.disabled = false;
       });
    }
};