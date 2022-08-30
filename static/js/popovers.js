/**
 * The Popovers feature logic.
 */
popoversFeature = {
    initialContent: '<div class="pas"><i class="fas fa-spinner fa-pulse"></i> Loading...</div>',
    defaultPopoverOptions: {
        arrow: true,
        delay: [700, 50],
        duration: [200, 200],
        performance: true
    },
    /**
     * Initialize the Ajax "player" popover on the Server details page.
     */
    initOnServerDetails: function() {
        this.initPlayerPopover(document.querySelectorAll('.players-list a[data-popover-url]'));
    },
    /**
     * Initialize the Ajax "player" popover on the Servers list page.
     */
    initOnServersList: function() {
        this.initPlayerPopover(document.querySelectorAll('.servers-list a[data-popover-url]'));
    },
    /**
     * Initialize the Ajax "player" popover on the User profile page.
     */
    initOnUserProfile: function() {
        this.initPlayerPopover(document.querySelectorAll('.rwr-accounts-list a[data-popover-url]'));
    },
    /**
     * Initialize the Ajax "player" popover on the My Friends page.
     */
    initOnMyFriends: function() {
        this.initPlayerPopover(document.querySelectorAll('.friends-list a[data-popover-url]'));
    },
    /**
     * Initialize an Ajax "player" popover on a set of elements.
     */
    initPlayerPopover: function(elements) {
        return this.initPopover(
            elements,
            {
                theme: 'rwrs-player',
            }
        );
    },
    /**
     * Initialize an Ajax popover on a set of elements.
     */
    initPopover: function(elements, options) {
        var self = this;

        var optionsToUse = {};

        Object.assign(optionsToUse, self.defaultPopoverOptions, options);

        optionsToUse.content = self.initialContent;

        optionsToUse.onShow = function(tip) {
            fetch(tip.reference.dataset.popoverUrl, {
                method: 'GET'
            }).then(function(response) {
                if (response.ok) {
                    return response.text();
                } else {
                    return Promise.reject(response);
                }
            }).then(function(response) {
                if (tip.state.isVisible) {
                    tip.setContent(response);
                }
            }).catch(function(error) {
                tip.setContent('Error fetching popover content.');
            });
        };

        optionsToUse.onHidden = function(tip) {
            tip.setContent(self.initialContent);
        };

        return tippy(elements, optionsToUse);
    }
};