/**
 * The Player claim feature logic.
 */
playerClaimFeature = {
    /**
     * Initialize the feature.
     */
    init: function() {
        this.$time_remaining_container = $('.time-remaining');

        this.initCountDown();
    },
    /**
     * Initialize the countdown.
     */
    initCountDown: function() {
        var self = this;

        this.countdown = countdown(
            this.milliseconds_remaining,
            function(ts) {
                self.$time_remaining_container.text(ts);
            },
            countdown.MINUTES | countdown.SECONDS
        );
    }
};