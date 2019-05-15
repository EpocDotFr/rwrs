/**
 * The Friends Import feature logic.
 */
friendsImportFeature = {
    /**
     * Initialize the Friends Import feature.
     */
    init: function() {
        if (!this.isLocalStorageSupported()) {
            return;
        }

        var friends = this.getFriends();

        if (friends.length == 0) {
            return;
        }

        this.importFriends(friends);
    },
    /**
     * Determine if the localStorage API is supported by the web browser.
     */
    isLocalStorageSupported: function() {
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');

            return true;
        } catch(e) {
            return false;
        }
    },
    /**
     * Get the friends list stored in the web browser.
     */
    getFriends: function() {
        var friends = localStorage.getItem('friends');

        if (!friends) {
            return [];
        }

        friends = JSON.parse(friends);

        if (friends.length == 0) {
            localStorage.removeItem('friends');

            return [];
        }

        return friends;
    },
    /**
     * Import the given friends list into the current user account.
     */
    importFriends: function(friends) {
        $.ajax({
            type: 'POST',
            url: this.endpoint,
            contentType: 'application/json',
            data: JSON.stringify(friends),
            success: function(response, status, xhr) {
                if (response.status != 'success') {
                    alert(response.data.message);
                } else {
                    localStorage.removeItem('friends');

                    window.location.href = window.location.pathname;
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
            }
        });
    }
};