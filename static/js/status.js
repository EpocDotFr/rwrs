/**
 * The Online status feature logic.
 */
onlineStatusFeature = {
    /**
     * Initialize the feature.
     */
    init: function() {
        this.servers_lists = $('.servers-list');
        this.servers_lists.find('tbody:not(.has-outages)').addClass('is-hidden');

        this.initToggles();
    },
    /**
     * Initialize events to be able to toggle the servers list of each continents.
     */
    initToggles: function() {
        this.heads = this.servers_lists.find('thead th');

        this.heads.on('click', function(e) {
            var $th = $(this);
            var $icon = $th.find('.toggle-icon');
            var $closest_tbody = $th.closest('table').children('tbody');

            if ($closest_tbody.hasClass('is-hidden')) {
                $icon.removeClass('fa-plus-square');
                $icon.addClass('fa-minus-square');
                $closest_tbody.removeClass('is-hidden');
            } else {
                $icon.addClass('fa-plus-square');
                $icon.removeClass('fa-minus-square');
                $closest_tbody.addClass('is-hidden');
            }
        });
    }
}