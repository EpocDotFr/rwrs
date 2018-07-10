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

        this.initInHeader();

        return true;
    },
    /**
     * Initialize the Friends feature in the header of all pages.
     */
    initInHeader: function() {
        var $total_playing_players = $('.total-playing-friends');
        var friends = this.getFriends();

        if (friends.length == 0) {
            $total_playing_players.addClass('is-hidden');

            return;
        }

        var playing_friends = 0;

        $.each(friends, function(friend_index, friend) {
            $.each(friendsFeature.all_players_with_servers_details, function(server_index, server) {
                if ($.inArray(friend, server.players.list) !== -1) {
                    playing_friends += 1;
                }
            });
        });

        if (playing_friends == 0) {
            $total_playing_players.addClass('is-hidden');

            return;
        }

        $total_playing_players.children('abbr').text(playing_friends);
        $total_playing_players.removeClass('is-hidden');
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
                contributors: friendsFeature.contributors,
                devs: friendsFeature.devs,
                rankedServersAdmins: friendsFeature.ranked_servers_admins,
                friend_to_add: '',
                playing_only: false
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

                        friendsFeature.initInHeader(); // Refresh the counter in the header

                        return true;
                    }

                    return false;
                },
                addFriend: function(username) {
                    if (friendsFeature.addFriend(username)) {
                        this.friends.push(username);
                        this.friends.sort();

                        friendsFeature.initInHeader(); // Refresh the counter in the header

                        return true;
                    }

                    return false;
                },
                submitAddFriendForm: function() {
                    if (!this.friend_to_add) {
                        alert('So you have a friend with no name?');

                        return;
                    }

                    if (this.addFriend(this.friend_to_add.toUpperCase())) {
                        this.friend_to_add = '';
                    } else {
                        alert('Friend wasn\'t added. Hey may be already in your friends list.');
                    }
                },
                inArray: function(value, array) {
                    return $.inArray(value, array) !== -1;
                }
            },
            computed: {
                friendsEnriched: function() {
                    var enriched_friends = [];
                    var self = this;

                    $.each(this.friends, function(friend_index, friend) {
                        var enriched_friend = {
                            username: friend
                        };

                        $.each(friendsFeature.all_players_with_servers_details, function(server_index, server) {
                            if ($.inArray(friend, server.players.list) !== -1) {
                                enriched_friend.playing_on_server = server;

                                return false;
                            }
                        });

                        if (!self.playing_only || (self.playing_only && 'playing_on_server' in enriched_friend)) {
                            enriched_friends.push(enriched_friend);
                        }
                    });

                    return enriched_friends;
                }
            }
        });
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

        $.each(this.all_players_with_servers_details, function(server_index, server) {
            var highlight = false;

            $.each(friends, function(friends_index, friend) {
                if ($.inArray(friend, server.players.list) !== -1) {
                    highlight = true;

                    return false;
                }
            });

            if (highlight) {
                $servers_list.filter('[data-server-ip-and-port="' + server.ip_and_port + '"]').addClass('info');
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
        $('.friends-feature').removeClass('is-hidden');

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

                friendsFeature.initInHeader(); // Refresh the counter in the header
            });

            $remove_friend_link.on('click', function(e) {
                e.preventDefault();

                var $a = $(this);
                var $closest_tr = $a.closest('tr[data-username]');

                friendsFeature.removeFriend($closest_tr.data('username'));

                $a.addClass('is-hidden');
                $add_friend_link.removeClass('is-hidden');
                $closest_tr.removeClass('info');

                friendsFeature.initInHeader(); // Refresh the counter in the header
            });
        });

        $.each(this.all_players_with_servers_details, function(server_index, server) {
            if (server.ip_and_port == friendsFeature.server_ip_and_port) {
                $.each(server.players.list, function(player_index, player) {
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

                return false;
            }
        });
    },
    /**
     * Initialize the Friends feature on the Players list page.
     */
    initOnPlayersList: function() {
        if (!this.init()) {
            return;
        }

        var friends = this.getFriends();

        var $players_list = $('.players-list > tbody > tr');

        $players_list.each(function() {
            var $tr = $(this);
            var username = $tr.data('username');
            var $add_friend_link = $tr.find('.add-friend');
            var $remove_friend_link = $tr.find('.remove-friend');

            $add_friend_link.on('click', function(e) {
                e.preventDefault();

                var $a = $(this);
                var $closest_tr = $a.closest('tr[data-username]');

                friendsFeature.addFriend($closest_tr.data('username'));

                $a.addClass('is-hidden');
                $remove_friend_link.removeClass('is-hidden');

                if (!$closest_tr.hasClass('notice')) { // Player isn't already highlighted in the leaderboard
                    $closest_tr.addClass('info');
                }

                friendsFeature.initInHeader(); // Refresh the counter in the header
            });

            $remove_friend_link.on('click', function(e) {
                e.preventDefault();

                var $a = $(this);
                var $closest_tr = $a.closest('tr[data-username]');

                friendsFeature.removeFriend($closest_tr.data('username'));

                $a.addClass('is-hidden');
                $add_friend_link.removeClass('is-hidden');
                $closest_tr.removeClass('info');

                friendsFeature.initInHeader(); // Refresh the counter in the header
            });

            if ($.inArray(username, friends) !== -1) {
                if (!$tr.hasClass('notice')) { // Player isn't already highlighted in the leaderboard
                    $tr.addClass('info');
                }

                $remove_friend_link.removeClass('is-hidden');
            } else {
                $add_friend_link.removeClass('is-hidden');
            }
        });
    },
    /**
     * Initialize the Friends feature on the Player details page.
     */
    initOnPlayerDetails: function() {
        if (!this.init()) {
            return;
        }

        var friends = this.getFriends();

        var $add_friend_link = $('.add-friend');
        var $remove_friend_link = $('.remove-friend');

        $add_friend_link.on('click', function(e) {
            e.preventDefault();

            var username = $(this).data('username');

            friendsFeature.addFriend(username);

            $(this).addClass('is-hidden');
            $remove_friend_link.removeClass('is-hidden');

            friendsFeature.initInHeader(); // Refresh the counter in the header
        });

        $remove_friend_link.on('click', function(e) {
            e.preventDefault();

            var username = $(this).data('username');

            friendsFeature.removeFriend(username);

            $(this).addClass('is-hidden');
            $add_friend_link.removeClass('is-hidden');

            friendsFeature.initInHeader(); // Refresh the counter in the header
        });

        if ($.inArray($remove_friend_link.data('username'), friends) !== -1) {
            $remove_friend_link.removeClass('is-hidden');
        }

        if ($.inArray($add_friend_link.data('username'), friends) === -1) {
            $add_friend_link.removeClass('is-hidden');
        }
    },
    /**
     * Initialize the Friends feature on the Players comparison page.
     */
    initOnPlayersComparison: function() {
        if (!this.init()) {
            return;
        }

        var friends = this.getFriends();

        var $add_friend_links = $('.add-friend');
        var $remove_friend_links = $('.remove-friend');

        $add_friend_links.on('click', function(e) {
            e.preventDefault();

            var username = $(this).data('username');

            friendsFeature.addFriend(username);

            $(this).addClass('is-hidden');
            $(this).siblings('.remove-friend[data-username="' + username + '"]').removeClass('is-hidden');

            friendsFeature.initInHeader(); // Refresh the counter in the header
        });

        $remove_friend_links.on('click', function(e) {
            e.preventDefault();

            var username = $(this).data('username');

            friendsFeature.removeFriend(username);

            $(this).addClass('is-hidden');
            $(this).siblings('.add-friend[data-username="' + username + '"]').removeClass('is-hidden');

            friendsFeature.initInHeader(); // Refresh the counter in the header
        });

        $remove_friend_links.each(function() {
            if ($.inArray($(this).data('username'), friends) !== -1) {
                $(this).removeClass('is-hidden');
            }
        });

        $add_friend_links.each(function() {
            if ($.inArray($(this).data('username'), friends) === -1) {
                $(this).removeClass('is-hidden');
            }
        });
    },
    /**
     * Get all the user's friends.
     */
    getFriends: function() {
        var friends = JSON.parse(localStorage.getItem('friends'));

        if (!friends) {
            return [];
        }

        // Force usernames to be string as they are stored either as int or string by the JSON parser
        $.each(friends, function(key, friend) {
            friends[key] = friend + '';
        });

        return friends;
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
};