/**
 * The Friends feature logic.
 */
friendsFeature = {
    /**
     * Initialize the Friends feature on the My friends page.
     */
    initOnMyFriends: function() {
        // TODO
    },
    /**
     * Initialize the Friends feature on the Server details page.
     */
    initOnServerDetails: function() {
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
    },
    /**
     * Initialize the Friends feature on the Players list page.
     */
    initOnPlayersList: function() {
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
        var friends = this.getFriends();

        var $add_friend_link = $('.add-friend');
        var $remove_friend_link = $('.remove-friend');

        $add_friend_link.on('click', function(e) {
            e.preventDefault();

            var $username = $(this).data('username');

            friendsFeature.addFriend($username);

            $(this).addClass('is-hidden');
            $remove_friend_link.removeClass('is-hidden');
        });

        $remove_friend_link.on('click', function(e) {
            e.preventDefault();

            var $username = $(this).data('username');

            friendsFeature.removeFriend($username);

            $(this).addClass('is-hidden');
            $add_friend_link.removeClass('is-hidden');
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
        var friends = this.getFriends();

        var $add_friend_links = $('.add-friend');
        var $remove_friend_links = $('.remove-friend');

        $add_friend_links.on('click', function(e) {
            e.preventDefault();

            var $username = $(this).data('username');

            friendsFeature.addFriend($username);

            $(this).addClass('is-hidden');
            $(this).siblings('.remove-friend[data-username="' + $username + '"]').removeClass('is-hidden');
        });

        $remove_friend_links.on('click', function(e) {
            e.preventDefault();

            var $username = $(this).data('username');

            friendsFeature.removeFriend($username);

            $(this).addClass('is-hidden');
            $(this).siblings('.add-friend[data-username="' + $username + '"]').removeClass('is-hidden');
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