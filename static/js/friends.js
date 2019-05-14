/**
 * The Friends feature logic.
 */
friendsFeature = {
    /**
     * Initialize the Friends feature on the My friends page.
     */
    initOnMyFriends: function() {
        // TODO Migration system
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