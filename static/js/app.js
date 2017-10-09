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

            $total_playing_players.children('strong').text(total_playing_players);
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
    getPlayingFriends: function() {
        var friends = this.getFriends();
        var self = this;
        var playing_friends = [];

        $.each(friends, function(friends_index, friend) {
            $.each(self.all_players, function(player_index, player) {
                if (friend == player) {
                    playing_friends.push(friend);
                }
            });
        });

        return playing_friends;
    },
    totalPlayingFriends: function() {
        return this.getPlayingFriends().length;
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
