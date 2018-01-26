/**
 * The Charts feature logic.
 */
chartsFeature = {
    defaultChartOptions: {
        show_tooltips: false,
        x_accessor: 't',
        y_accessor: 'c',
        x_mouseover: '%b %e, %Y %H:%M%p ',
        area: false,
        min_y: 0,
        y_extended_ticks: true,
        x_extended_ticks: true,
        utc_time: true,
        full_width: true,
        top: 20,
        bottom: 35,
        left: 35,
        right: 25,
        buffer: 0
    },
    convertDates: function(data) {
        var to_date_object = d3.utcParse('%Y-%m-%dT%H:%M:%S');

        $.each(data, function(key, value) {
            value.t = to_date_object(value.t);
        });
    },
    /**
     * Initialize the Players charts on the Server details page.
     */
    initOnServerDetails: function() {
        this.convertDates(this.server_players_data);

        this.createChart({
            target: '#server-players-chart',
            color: '#A4CF17',
            data: this.server_players_data
        });
    },
    /**
     * Initialize the Players charts on the Home page.
     */
    initOnHome: function() {
        // Total and online players chart
        for (var i = 0; i < this.players_data.length; i++) {
            this.convertDates(this.players_data[i]);
        }

        this.createChart({
            target: '#players-chart',
            colors: ['#A4CF17', '#44b2f8'],
            legend: ['Total players', 'Online players'],
            legend_target: '#players-legend',
            aggregate_rollover: true,
            data: this.players_data
        });

        // Online and active servers
        for (var i = 0; i < this.servers_data.length; i++) {
            this.convertDates(this.servers_data[i]);
        }

        this.createChart({
            target: '#servers-chart',
            colors: ['#A4CF17', '#44b2f8'],
            legend: ['Online servers', 'Active servers'],
            legend_target: '#servers-chart-legend',
            aggregate_rollover: true,
            data: this.servers_data
        });
    },
    createChart: function(options) {
        MG.data_graphic($.extend({}, this.defaultChartOptions, options, true));
    }
};