
var map;
var probs;
var sts;
var heatmap;
var marker;
var interval = 0;
var intervalSize = 1;
var day = 0;
var near_ind = 0;

var rad = function(x) {
    return x * Math.PI / 180;
};

var getDistance = function(p1, p2) {
    var R = 6378137; // Earth’s mean radius in meter
    var dLat = rad(p2.lat() - p1.lat);
    var dLong = rad(p2.lng() - p1.lng);
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(rad(p1.lat)) * Math.cos(rad(p2.lat())) *
        Math.sin(dLong / 2) * Math.sin(dLong / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    var d = R * c;
    return d; // returns the distance in meter
};

function changeInterval(val_str) {
    interval = +val_str;
    updateHeatmap();
}

function changeIntervalSize(val_str) {
    intervalSize = +val_str;
    updateHeatmap();
}

function changeDay(val_str) {
    day = +val_str;
    updateHeatmap();
}

function updateHeatmap() {
    d3.json("/freqs/" + intervalSize + "/" + interval + "/"
            + day + "/" + near_ind,
        function (d) {
            freqs = d["freqs"]
            time = d["time"]
            $("#timeSpan").html(time);
            console.log(time);
            var hmData = new Array();
            for (var i = 0; i < sts.length; i++) {
                var loc = new google.maps.LatLng(
                        sts[i].lat, sts[i].lng);
                hmData.push({location: loc,
                    weight: 100000 * freqs[i]});
            }
            heatmap.setMap(null);
            heatmap = new google.maps.visualization.HeatmapLayer({
                data: hmData,
                radius: 25
            });
            heatmap.setMap(map);
        });
}

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: 40.77638, lng: -73.96957},
        zoom: 12,
        disableDoubleClickZoom: true,
        draggable: true
    });

    var marker = new google.maps.Marker({
        title: 'Pickup Station',
        map: map
    });


    heatmap = new google.maps.visualization.HeatmapLayer();

    d3.csv("stations", function (d) {
            return {lat: +d.lat, lng: +d.lng};
        }, function(data) {
            sts = data;
    });

    google.maps.event.addListener(map, 'click', function (ev) {
        var pt = ev.latLng;
        console.log(pt.lat());
        console.log(pt.lng());
        var near_dist = null;

        for (var i = 0; i < sts.length; i++) {
            dist = getDistance(sts[i], pt);
            if (near_dist == null || dist < near_dist) {
                near_dist = dist;
                near_ind = i;
            }
        }

        var markerPos = new google.maps.LatLng(
            sts[near_ind].lat, sts[near_ind].lng);

        marker.setPosition(markerPos);

        console.log(markerPos.lat);
        console.log(markerPos.lng);
        console.log(near_ind);
        updateHeatmap();
    });
}
