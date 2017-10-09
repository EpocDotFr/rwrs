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

        $total_playing_players = $('.total-playing-friends');

        $total_playing_players.children('strong').text(playing_friends.length);
        $total_playing_players.removeClass('is-hidden');
    },
    initOnServersList: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        var friends = this.getFriends();

        if (friends.length == 0) {
            return;
        }

        $servers_list = $('.servers-list');

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
                $servers_list.find('tbody > tr[data-server-ip-and-port="' + server_ip_and_port + '"]').addClass('info');
            }
        });
    },
    initOnServerDetails: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        var friends = this.getFriends();

        if (friends.length == 0) {
            return;
        }

        $players_list = $('.players-list');

        $.each(this.players, function(player_index, player) {
            var highlight = false;

            $.each(friends, function(friends_index, friend) {
                if (player == friend) {
                    highlight = true;

                    return false;
                }
            });

            if (highlight) {
                $players_list.find('tbody > tr[data-username="' + player + '"]').addClass('info');
            }
        });
    },
    initOnPlayerStats: function() {
        if (!isLocalStorageSupported()) {
            return;
        }

        // TODO
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
    }
}
