/**
 * The Map feature logic.
 */
mapFeature = {
    defaultZoom: 1,
    overlays: {},

    playerSpawnMarker: L.Icon.extend({
        options: {
            iconUrl: '/images/map_viewer/player_spawn.png',
            iconSize: [10, 10],
            iconAnchor: [0, 0],
            popupAnchor: [5, 5]
        }
    }),

    /**
     * Initialize the feature on the Map details page.
     */
    initOnMapDetails: function() {
        this.map = new L.map('map', {
            crs: L.CRS.Simple,
            attributionControl: false,
            zoomControl: false,
            minZoom: this.minZoom,
            maxZoom: this.maxZoom,
            zoom: this.defaultZoom
        });

        this.bounds = new L.LatLngBounds(
            this.map.unproject([0, 2048], this.map.getMaxZoom()),
            this.map.unproject([2048, 0], this.map.getMaxZoom())
        );

        this.mapLayer = new L.tileLayer(this.tilesUrl, {
            minZoom: this.minZoom,
            maxZoom: this.maxZoom,
            tileSize: this.tileSize,
            bounds: this.bounds,
            errorTileUrl: this.tileNotFoundUrl
        }).addTo(this.map);

        // FIXME Scale is wrong
        this.scaleControl = new L.control.scale({
            position: 'bottomleft'
        }).addTo(this.map);

        this.zoomControl = new L.control.zoom({
            position: 'bottomright'
        }).addTo(this.map);

        this.loadPlayersSpawns();

        this.layersControl = new L.control.layers(
            null,
            this.overlays,
            {
                position: 'topright'
            }
        ).addTo(this.map);

        this.map.setMaxBounds(this.bounds);
        this.map.setView(this.bounds.getCenter());
    },
    loadPlayersSpawns: function() {
        var players_spawns = new L.layerGroup();

        var self = this;

        $.each(this.objects.players_spawns, function(index, player_spawn) {
            players_spawns.addLayer(new L.marker(
                self.map.unproject(
                    [player_spawn.x, player_spawn.y],
                    self.map.getMaxZoom()
                ),
                {
                    icon: new self.playerSpawnMarker
                }
            ));
        });

        self.overlays['Players spawns'] = players_spawns;
    }
};