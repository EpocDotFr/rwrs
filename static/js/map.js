/**
 * The Map feature logic.
 */
mapFeature = {
    defaultZoom: 1,
    overlays: {},

    /**
     * Initialize the feature on the Map details page.
     */
    initOnMapDetails: function() {
        this.map = L.map('map', {
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

        this.mapLayer = L.tileLayer(this.tilesUrl, {
            minZoom: this.minZoom,
            maxZoom: this.maxZoom,
            tileSize: this.tileSize,
            bounds: this.bounds,
            errorTileUrl: this.tileNotFoundUrl
        }).addTo(this.map);

        // FIXME Scale is wrong
        this.scaleControl = L.control.scale({
            position: 'bottomleft'
        }).addTo(this.map);

        this.zoomControl = L.control.zoom({
            position: 'bottomright'
        }).addTo(this.map);

        // TODO Temporary according to this screenshot https://d1u5p3l4wpay3k.cloudfront.net/runningwithrifles_gamepedia/b/bd/Mapview.jpg?version=41b530749819057bafe70109299d99d6
        this.overlays['<i class="fa fa-map"></i> Test'] = L.layerGroup([
            L.marker(this.map.unproject([1024, 1024], this.map.getMaxZoom())).bindPopup('Test')
        ]);

        this.layersControl = L.control.layers(
            null,
            this.overlays,
            {
                position: 'topright'
            }
        ).addTo(this.map);

        this.map.setMaxBounds(this.bounds);
        this.map.setView(this.bounds.getCenter());
    }
}