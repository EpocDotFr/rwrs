/**
 * The Charts feature logic.
 */
chartsFeature = {
    defaultChartOptions: {
        chart_type: 'line',
        show_tooltips: false,
        x_accessor: 't',
        y_accessor: 'v',
        x_mouseover: '%b %e, %Y %H:%M%p ',
        area: false,
        y_extended_ticks: true,
        x_extended_ticks: true,
        utc_time: true,
        full_width: true,
        top: 15,
        bottom: 35,
        left: 40,
        right: 10,
        buffer: 0,
        interpolate: d3.curveMonotoneX
    },
    missingDataChartOptions: {
        chart_type: 'missing-data',
        full_width: true,
        top: 15,
        bottom: 35,
        left: 40,
        right: 10,
        buffer: 0
    },
    /**
     * Initialize the charts on the Player's Evolution page.
     */
    initOnPlayerEvolution: function() {
        // K/D ratio
        if (this.player_evolution_data.ratio.length == 0) {
            // If there's no data to display, create a "missing data" chart
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
                data: this.player_evolution_data.ratio,
                markers: this.getPromotionMarkers(this.player_evolution_data.ratio)
            });
        }

        // Score
        if (this.player_evolution_data.score.length == 0) {
            // If there's no data to display, create a "missing data" chart
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
                data: this.player_evolution_data.score,
                markers: this.getPromotionMarkers(this.player_evolution_data.score)
            });
        }

        // Leaderboard position (by XP)
        if (this.player_evolution_data.position.length == 0) {
            // If there's no data to display, create a "missing data" chart
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
                data: this.player_evolution_data.position,
                markers: this.getPromotionMarkers(this.player_evolution_data.position)
            });
        }
    },
    /**
     * Initialize the Players charts on the Server details page.
     */
    initOnServerDetails: function() {
        if (this.server_players_data.length == 0) {
            // If there's no data to display, create a "missing data" chart
            this.createMissingDataChart({
                target: '#server-players-chart'
            });
        } else {
            this.convertDates(this.server_players_data);

            this.createChart({
                target: '#server-players-chart',
                color: '#A4CF17',
                min_y: 0,
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
            // If there's no data to display, create a "missing data" chart
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
                min_y: 0,
                data: this.players_data
            });
        }

        // Online and active servers
        if (this.servers_data.length == 0 || (this.servers_data[0].length == 0 && this.servers_data[1].length == 0)) {
            // If there's no data to display, create a "missing data" chart
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
                min_y: 0,
                data: this.servers_data
            });
        }
    },
    /**
     * Initialize a chart with the given options.
     */
    createChart: function(options) {
        var optionsToUse = {};

        Object.assign(optionsToUse, this.defaultChartOptions, options);

        MG.data_graphic(optionsToUse);
    },
    /**
     * Initialize a "missing data" chart with the given options.
     */
    createMissingDataChart: function(options) {
        var optionsToUse = {};

        Object.assign(optionsToUse, this.missingDataChartOptions, options);

        this.createChart(optionsToUse);
    },
    /**
     * Converts dates in a list of objects.
     */
    convertDates: function(data, format) {
        var format = typeof format !== 'undefined' ? format : '%Y-%m-%dT%H:%M:%S';
        var to_date_object = d3.utcParse(format);

        data.forEach(function(item) {
            item.t = to_date_object(item.t);
        });
    },
    /**
     * Get the markers which will represent when the player has been promoted.
     */
    getPromotionMarkers: function(data) {
        return data.map(function(item) {
            if (!item.ptr) {
                return null;
            }

            return {
                't': item.t,
                'label': item.ptr
            };
        });
    }
};