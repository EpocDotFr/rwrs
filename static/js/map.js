/**
 * The Map feature logic.
 */
mapFeature = {
    defaultZoom: 1,

    playerSpawnMarker: L.Icon.extend({
        options: {
            iconUrl: '/images/map_viewer/player_spawn.png',
            iconSize: [10, 10],
            iconAnchor: [5, 5],
            popupAnchor: [0, 0]
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

        var overlays = {};

        // TODO Temporary according to this screenshot https://d1u5p3l4wpay3k.cloudfront.net/runningwithrifles_gamepedia/b/bd/Mapview.jpg?version=41b530749819057bafe70109299d99d6
        overlays['<i class="fa fa-map"></i> Test'] = new L.layerGroup([
            new L.marker(this.map.unproject([1024, 1024], this.map.getMaxZoom()), {icon: new this.playerSpawnMarker}).bindPopup('Test')
        ]);

        this.layersControl = new L.control.layers(
            null,
            overlays,
            {
                position: 'topright'
            }
        ).addTo(this.map);

        this.map.setMaxBounds(this.bounds);
        this.map.setView(this.bounds.getCenter());
    }
};