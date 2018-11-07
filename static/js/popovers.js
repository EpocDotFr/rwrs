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
        this.initPlayerPopover($('.players-list a[data-popover-url]').get());
    },
    initPlayerPopover: function(elements) {
        return this.initPopover(
            elements,
            {
                theme: 'rwrs-player',
            }
        );
    },
    initPopover: function(elements, options) {
        var self = this;

        var options = $.extend({}, self.defaultPopoverOptions, options, true);

        options.content = self.initialContent;

        options.onShow = function(tip) {
            $.ajax({
                type: 'GET',
                url: $(tip.reference).data('popover-url'),
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

        return tippy(elements, options);
    }
};