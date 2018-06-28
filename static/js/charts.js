/**
 * The Charts feature logic.
 */
chartsFeature = {
    defaultChartOptions: {
        show_tooltips: false,
        x_accessor: 't',
        y_accessor: 'v',
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
    missingDataChartOptions: {
        chart_type: 'missing-data',
        top: 0,
        bottom: 10,
        left: 10,
        right: 15
    },
    convertDates: function(data, format) {
        var format = typeof format !== 'undefined' ? format : '%Y-%m-%dT%H:%M:%S';
        var to_date_object = d3.utcParse(format);

        $.each(data, function(key, value) {
            value.t = to_date_object(value.t);
        });
    },
    /**
     * Initialize the charts on the Player's Evolution page.
     */
    initOnPlayerEvolution: function() {
        // K/D ratio
        if (this.player_evolution_data.ratio.length == 0) {
            // If there's no data ti display, create a "missing data" chart
            this.createMissingDataChart({
                target: '#ratio-chart'
            });
        } else {
            this.convertDates(this.player_evolution_data.ratio, '%Y-%m-%d');

            this.createChart({
                target: '#ratio-chart',
                color: '#A4CF17',
                x_mouseover: '%b %e, %Y ',
                min_y_from_data: true,
                data: this.player_evolution_data.ratio
            });
        }

        // Score
        if (this.player_evolution_data.score.length == 0) {
            // If there's no data ti display, create a "missing data" chart
            this.createMissingDataChart({
                target: '#score-chart'
            });
        } else {
            this.convertDates(this.player_evolution_data.score, '%Y-%m-%d');

            this.createChart({
                target: '#score-chart',
                color: '#A4CF17',
                x_mouseover: '%b %e, %Y ',
                min_y_from_data: true,
                data: this.player_evolution_data.score
            });
        }

        // Leaderboard position (by XP)
        if (this.player_evolution_data.position.length == 0) {
            // If there's no data ti display, create a "missing data" chart
            this.createMissingDataChart({
                target: '#position-chart'
            });
        } else {
            this.convertDates(this.player_evolution_data.position, '%Y-%m-%d');

            this.createChart({
                target: '#position-chart',
                color: '#A4CF17',
                x_mouseover: '%b %e, %Y ',
                min_y_from_data: true,
                data: this.player_evolution_data.position
            });
        }
    },
    /**
     * Initialize the Players charts on the Server details page.
     */
    initOnServerDetails: function() {
        if (this.server_players_data.length == 0) {
            // If there's no data ti display, create a "missing data" chart
            this.createMissingDataChart({
                target: '#server-players-chart'
            });
        } else {
            this.convertDates(this.server_players_data);

            this.createChart({
                target: '#server-players-chart',
                color: '#A4CF17',
                data: this.server_players_data
            });
        }
    },
    /**
     * Initialize the Players charts on the Home page.
     */
    initOnHome: function() {
        // Total and online players chart
        if (this.players_data.length == 0 || (this.players_data[0].length == 0 && this.players_data[1].length == 0)) {
            // If there's no data ti display, create a "missing data" chart
            this.createMissingDataChart({
                target: '#players-chart'
            });
        } else {
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
        }

        // Online and active servers
        if (this.servers_data.length == 0 || (this.servers_data[0].length == 0 && this.servers_data[1].length == 0)) {
            // If there's no data ti display, create a "missing data" chart
            this.createMissingDataChart({
                target: '#servers-chart'
            });
        } else {
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
        }
    },
    createChart: function(options) {
        MG.data_graphic($.extend({}, this.defaultChartOptions, options, true));
    },
    createMissingDataChart: function(options) {
        this.createChart($.extend({}, this.missingDataChartOptions, options, true));
    }
};