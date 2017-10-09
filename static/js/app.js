/**
 * Check if localStorage is supported in the current browser.
 */
function isLocalStorageSupported() {
    try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        return true;
    } catch(e) {
        return false;
    }
}

friendsFeature = {
    initOnHome: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        var total_playing_players = this.totalPlayingFriends();

        if (total_playing_players > 0) {
            $total_playing_players = $('.total-playing-friends');

            $total_playing_players.children('strong').text(friendsCount);
            $total_playing_players.removeClass('is-hidden');
        }
    },
    initOnPlayerStats: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        // TODO
    },
    initOnServerDetails: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        // TODO
    },
    initOnServersList: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        // TODO
    },
    totalPlayingFriends: function() {
        var friends = this.getFriends();

        return 2; // TODO this.all_players
    },
    getFriends: function() {
        return JSON.parse(localStorage.getItem('friends')) || [];
    },
    setFriends: function(friends) {
        localStorage.setItem('friends', JSON.stringify(friends));
    },
    addFriend: function(username) {
        var friends = this.getFriends();

        if ((username in friends)) {
            return false;
        }

        friends.append(username);

        this.setFriends(friends);

        return true;
    },
    removeFriend: function(username) {
        var friends = this.getFriends();

        if (!(username in friends)) {
            return false;
        }

        friends.splice(friends.indexOf(username), 1);

        this.setFriends(friends);

        return true;
    },
    totalFriends: function() {
        return this.getFriends().length;
    },
    hasFriends: function() {
        return this.totalFriends() > 0;
    }
}
