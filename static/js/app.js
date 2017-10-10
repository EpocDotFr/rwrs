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

/**
 * The Friends feature logic.
 */
friendsFeature = {
    /**
     * Initialize the Friends feature on the Home page.
     */
    initOnHome: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        var friends = this.getFriends();

        if (friends.length == 0) {
            return;
        }

        var self = this;
        var playing_friends = [];

        $.each(friends, function(friends_index, friend) {
            $.each(self.all_players, function(player_index, player) {
                if (friend == player) {
                    playing_friends.push(friend);
                }
            });
        });

        if (playing_friends.length == 0) {
            return;
        }

        var $total_playing_players = $('span.total-playing-friends');

        $total_playing_players.children('strong').text(playing_friends.length);
        $total_playing_players.removeClass('is-hidden');
    },
    /**
     * Initialize the Friends feature on the Servers list page.
     */
    initOnServersList: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        var friends = this.getFriends();

        if (friends.length == 0) {
            return;
        }

        var $servers_list = $('table.servers-list > tbody > tr');

        $.each(this.all_players_with_servers, function(server_ip_and_port, players) {
            var highlight = false;

            $.each(players, function(player_index, player) {
                $.each(friends, function(friends_index, friend) {
                    if (player == friend) {
                        highlight = true;

                        return false;
                    }
                });

                if (highlight) {
                    return false;
                }
            });

            if (highlight) {
                $servers_list.filter('[data-server-ip-and-port="' + server_ip_and_port + '"]').addClass('info');
            }
        });
    },
    /**
     * Initialize the Friends feature on the Server details page.
     */
    initOnServerDetails: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        // Enable the feature on the players list
        $('.actions-disabled').removeClass('actions-disabled').addClass('actions');

        var friends = this.getFriends();
        var self = this;

        var $players_list = $('table.players-list > tbody > tr');

        $players_list.each(function() {
            var $tr = $(this);
            var $add_friend_link = $tr.find('a.add-friend');
            var $remove_friend_link = $tr.find('a.remove-friend');

            $add_friend_link.on('click', function(e) {
                e.preventDefault();

                var $a = $(this);
                var $closest_tr = $a.closest('tr[data-username]');

                self.addFriend($closest_tr.data('username'));

                $a.addClass('is-hidden');
                $remove_friend_link.removeClass('is-hidden');
                $closest_tr.addClass('info');
            });

            $remove_friend_link.on('click', function(e) {
                e.preventDefault();

                var $a = $(this);
                var $closest_tr = $a.closest('tr[data-username]');

                self.removeFriend($closest_tr.data('username'));

                $a.addClass('is-hidden');
                $add_friend_link.removeClass('is-hidden');
                $closest_tr.removeClass('info');
            });
        });

        $.each(this.players, function(player_index, player) {
            var highlight = false;

            $.each(friends, function(friends_index, friend) {
                if (player == friend) {
                    highlight = true;

                    return false;
                }
            });

            var $player_tr = $players_list.filter('[data-username="' + player + '"]');

            if (highlight) {
                $player_tr.addClass('info');
                $player_tr.find('a.remove-friend').removeClass('is-hidden');
            } else {
                $player_tr.find('a.add-friend').removeClass('is-hidden');
            }
        });
    },
    /**
     * Initialize the Friends feature on the Player stats page.
     */
    initOnPlayerStats: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        // TODO
    },
    /**
     * Get all the user's friends.
     */
    getFriends: function() {
        return JSON.parse(localStorage.getItem('friends')) || [];
    },
    /**
     * Set the user's friends.
     */
    setFriends: function(friends) {
        localStorage.setItem('friends', JSON.stringify(friends));
    },
    /**
     * Add a new friend to the user's friends list.
     */
    addFriend: function(username) {
        var friends = this.getFriends();

        if ($.inArray(username, friends) !== -1) {
            return false;
        }

        friends.push(username);

        this.setFriends(friends);

        return true;
    },
    /**
     * Remove a friend from the user's friends list.
     */
    removeFriend: function(username) {
        var friends = this.getFriends();

        if ($.inArray(username, friends) === -1) {
            return false;
        }

        friends.splice(friends.indexOf(username), 1);

        this.setFriends(friends);

        return true;
    }
}
