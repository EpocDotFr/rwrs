/**
 * The Popovers feature logic.
 */
popoversFeature = {
    initialContent: '<i class="fas fa-spinner fa-pulse"></i> Loading...',
    defaultPopoverOptions: {
        arrow: true,
        delay: [500, 50],
        duration: [200, 200],
        performance: true
    },
    /**
     * Initialize the Players charts on the Server details page.
     */
    initOnServerDetails: function() {
        var self = this;

        $('.players-list a[data-popover-url]').each(function() {
            self.initPlayerPopover(this);
        });
    },
    initPlayerPopover: function(element) {
        return this.initPopover(
            element,
            {
                theme: 'rwrs-player',
            }
        );
    },
    initPopover: function(element, options) {
        var options = $.extend({}, this.defaultPopoverOptions, options, true);
        var url = $(element).data('popover-url');

        options.content = this.initialContent;

        var self = this;

        options.onShow = function(tip) {
            $.ajax({
                type: 'GET',
                url: url,
                dataType: 'html',
                cache: false,
                success: function(response, status, xhr) {
                    if (tip.state.isVisible) {
                        tip.setContent(response);
                    }
                },
                error: function(xhr, errorType, error) {
                    tip.setContent('Error fetching popover content.');
                }
            });
        };

        options.onHidden = function(tip) {
            tip.setContent(self.initialContent);
        };

        return tippy(element, options);
    }
};