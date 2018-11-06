/**
 * The Popovers feature logic.
 */
popoversFeature = {
    initialContent: '<i class="fas fa-spinner fa-pulse"></i> Loading...',

    /**
     * Initialize the Players charts on the Server details page.
     */
    initOnServerDetails: function() {
        var $players_name_links = $('.players-list a[data-popover-url]');

        var feature = this;

        $players_name_links.each(function() {
            var link = this;

            tippy(link, {
                content: feature.initialContent,
                arrow: true,
                theme: 'rwrs',
                delay: [500, 50],
                duration: [200, 200],
                performance: true,
                onShow: function(tip) {
                    $.ajax({
                        type: 'GET',
                        url: $(link).data('popover-url'),
                        dataType: 'html',
                        cache: false,
                        success: function(response, status, xhr) {
                            if (tip.state.isVisible) {
                                tip.setContent(response);
                            }
                        },
                        error: function(xhr, errorType, error) {
                            tip.setContent('Error fetching popover content: ' + error);
                        }
                    });
                },
                onHidden: function(tip) {
                    tip.setContent(feature.initialContent);
                }
            });
        });
    }
};