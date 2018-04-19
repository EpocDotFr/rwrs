/**
 * The Map feature logic.
 */
mapFeature = {
    defaultZoom: 1,

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

        this.map.setMaxBounds(this.bounds);
        this.map.setView(this.bounds.getCenter());

        this.mapLayer = L.tileLayer(this.tilesUrl, {
            minZoom: this.minZoom,
            maxZoom: this.maxZoom,
            tileSize: this.tileSize,
            bounds: this.bounds,
            errorTileUrl: this.tileNotFoundUrl
        }).addTo(this.map);

        L.control.scale({
            position: 'bottomleft'
        }).addTo(this.map);

        L.control.zoom({
            position: 'bottomright'
        }).addTo(this.map);
    }
}