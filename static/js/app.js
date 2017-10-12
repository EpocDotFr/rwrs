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
     * Global initialization of the feature (on all pages).
     */
    init: function() {
        if (!isLocalStorageSupported()) {
            return false;
        }

        $('.manage-friends-link').removeClass('is-hidden');

        return true;
    },
    /**
     * Initialize the Friends feature on the My friends page.
     */
    initOnMyFriends: function() {
        if (!this.init()) {
            return;
        }

        Vue.config.productionTip = false;

        var vue_delimiters = ['${', '}']; // Because Jinja2 already uses double brackets

        this.app = new Vue({
            delimiters: vue_delimiters,
            el: '#app',
            data: {
                friends: [],
                my_username: friendsFeature.my_username,
                friend_to_add: ''
            },
            mounted: function() {
                this.$nextTick(function() {
                    friendsFeature.app.friends = friendsFeature.getFriends();
                });
            },
            methods: {
                removeFriend: function(username) {
                    if (friendsFeature.removeFriend(username)) {
                        this.friends.splice(this.friends.indexOf(username), 1);

                        return true;
                    }

                    return false;
                },
                addFriend: function(username) {
                    if (friendsFeature.addFriend(username)) {
                        this.friends.push(username);
                        this.friends.sort();

                        return true;
                    }

                    return false;
                },
                submitAddFriendForm: function() {
                    if (this.addFriend(this.friend_to_add.toUpperCase())) {
                        this.friend_to_add = '';
                    } else {
                        alert('Friend wasn\'t added. Hey may be already in your friends list.');
                    }
                }
            },
            computed: {
                friendsEnriched: function() {
                    var enriched_friends = [];

                    $.each(this.friends, function(friend_index, friend) {
                        var enriched_friend = {
                            username: friend
                        };

                        $.each(friendsFeature.all_players_with_servers_details, function(server_index, server) {
                            if ($.inArray(friend, server.players.list) !== -1) {
                                enriched_friend.playing_on_server = server;
                            }
                        });

                        enriched_friends.push(enriched_friend)
                    });

                    return enriched_friends;
                }
            }
        });
    },
    /**
     * Initialize the Friends feature on the Home page.
     */
    initOnHome: function() {
        if (!this.init()) {
            return;
        }

        var friends = this.getFriends();

        if (friends.length == 0) {
            return;
        }

        var playing_friends = [];

        $.each(friends, function(friend_index, friend) {
            if ($.inArray(friend, friendsFeature.all_players) !== -1) {
                playing_friends.push(friend);
            }
        });

        if (playing_friends.length == 0) {
            return;
        }

        var $total_playing_players = $('.total-playing-friends');

        $total_playing_players.children('strong').text(playing_friends.length);
        $total_playing_players.removeClass('is-hidden');
    },
    /**
     * Initialize the Friends feature on the Servers list page.
     */
    initOnServersList: function() {
        if (!this.init()) {
            return;
        }

        var friends = this.getFriends();

        if (friends.length == 0) {
            return;
        }

        var $servers_list = $('.servers-list > tbody > tr');

        $.each(this.all_players_with_servers, function(server_ip_and_port, players) {
            var highlight = false;

            $.each(friends, function(friends_index, friend) {
                if ($.inArray(friend, players) !== -1) {
                    highlight = true;

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
        if (!this.init()) {
            return;
        }

        // Enable the feature on the players list
        $('.actions-disabled').removeClass('actions-disabled').addClass('actions');

        var friends = this.getFriends();

        var $players_list = $('.players-list > tbody > tr');

        $players_list.each(function() {
            var $tr = $(this);
            var $add_friend_link = $tr.find('.add-friend');
            var $remove_friend_link = $tr.find('.remove-friend');

            $add_friend_link.on('click', function(e) {
                e.preventDefault();

                var $a = $(this);
                var $closest_tr = $a.closest('tr[data-username]');

                friendsFeature.addFriend($closest_tr.data('username'));

                $a.addClass('is-hidden');
                $remove_friend_link.removeClass('is-hidden');
                $closest_tr.addClass('info');
            });

            $remove_friend_link.on('click', function(e) {
                e.preventDefault();

                var $a = $(this);
                var $closest_tr = $a.closest('tr[data-username]');

                friendsFeature.removeFriend($closest_tr.data('username'));

                $a.addClass('is-hidden');
                $add_friend_link.removeClass('is-hidden');
                $closest_tr.removeClass('info');
            });
        });

        $.each(this.players, function(player_index, player) {
            var highlight = false;

            if ($.inArray(player, friends) !== -1) {
                highlight = true;
            }

            var $player_tr = $players_list.filter('[data-username="' + player + '"]');

            if (highlight) {
                $player_tr.addClass('info');
                $player_tr.find('.remove-friend').removeClass('is-hidden');
            } else {
                $player_tr.find('.add-friend').removeClass('is-hidden');
            }
        });
    },
    /**
     * Initialize the Friends feature on the Player stats page.
     */
    initOnPlayerStats: function() {
        if (!this.init()) {
            return;
        }

        var friends = this.getFriends();

        var $add_friend_link = $('.add-friend');
        var $remove_friend_link = $('.remove-friend');

        $add_friend_link.on('click', function(e) {
            e.preventDefault();

            friendsFeature.addFriend(friendsFeature.player);

            $(this).addClass('is-hidden');
            $remove_friend_link.removeClass('is-hidden');
        });

        $remove_friend_link.on('click', function(e) {
            e.preventDefault();

            friendsFeature.removeFriend(friendsFeature.player);

            $(this).addClass('is-hidden');
            $add_friend_link.removeClass('is-hidden');
        });

        if ($.inArray(this.player, friends) !== -1) {
            $remove_friend_link.removeClass('is-hidden');
        } else {
            $add_friend_link.removeClass('is-hidden');
        }
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
        localStorage.setItem('friends', JSON.stringify(friends.sort()));
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
