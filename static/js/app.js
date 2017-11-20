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

        this.initInHeader();

        return true;
    },
    /**
     * Initialize the Friends feature in the header of all pages.
     */
    initInHeader: function() {
        var friends = this.getFriends();

        if (friends.length == 0) {
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
            return;
        }

        var $total_playing_players = $('.total-playing-friends');

        $total_playing_players.children('strong').text(playing_friends);
        $total_playing_players.children('.friend-label').text(playing_friends > 1 ? 'friends' : 'friend');
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

        // Nothing special to do
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

            friendsFeature.initInHeader(); // Refresh the counter in the header
        });

        $remove_friend_link.on('click', function(e) {
            e.preventDefault();

            friendsFeature.removeFriend(friendsFeature.player);

            $(this).addClass('is-hidden');
            $add_friend_link.removeClass('is-hidden');

            friendsFeature.initInHeader(); // Refresh the counter in the header
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

/**
 * The Players charts feature logic.
 */
playersChartsFeature = {
    defaultChartOptions: {
        show_tooltips: false,
        x_accessor: 't',
        y_accessor: 'c',
        area: false,
        y_extended_ticks: true,
        x_extended_ticks: true,
        top: 20,
        bottom: 35,
        left: 30,
        right: 15,
        buffer: 0
    },
    dateFormat: '%Y-%m-%dT%H:%M:%S',
    /**
     * Initialize the Players charts on the Server details page.
     */
    initOnServerDetails: function() {
        this.createChart({
            target: '#server-players-chart',
            width: 360,
            color: '#A4CF17',
            data: MG.convert.date(this.server_players_data, 't', this.dateFormat)
        });
    },
    /**
     * Initialize the Players charts on the Home page.
     */
    initOnHome: function() {
        // Online players chart
        this.createChart({
            target: '#online-players-chart',
            width: 500,
            color: '#A4CF17',
            legend: ['Online players'],
            legend_target: '#online-players-legend',
            data: MG.convert.date(this.online_players_data, 't', this.dateFormat)
        });

        // Online and active servers
        for (var i = 0; i < this.servers_data.length; i++) {
            this.servers_data[i] = MG.convert.date(this.servers_data[i], 't', this.dateFormat);
        }

        this.createChart({
            target: '#servers-chart',
            width: 500,
            colors: ['#A4CF17', '#44b2f8'],
            legend: ['Online servers', 'Active servers'],
            legend_target: '#servers-chart-legend',
            data: this.servers_data
        });
    },
    createChart: function(options) {
        MG.data_graphic($.extend({}, this.defaultChartOptions, options, true));
    }
};