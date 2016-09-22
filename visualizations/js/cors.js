
var map;
var probs;
var sts;
var marker;
var interval = 0;
var intervalSize = 1;
var day = 0;
var near_ind = 0;

var p0_marker;
var d0_marker;
var p1_marker;
var d1_marker;
var markers;
var partners;
var oris;
var dsts;
var line_0;
var line_1;

self = this;

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

function getPin(color) {
    var pinImage = new google.maps.MarkerImage(
        "http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|" + color,
        new google.maps.Size(21, 34),
        new google.maps.Point(0,0),
        new google.maps.Point(10, 34));
    return pinImage;
}

function getNearest(pt)
{
    var near_dist = null;
    var ind = 0;

    for (var i = 0; i < sts.length; i++) {
        dist = getDistance(sts[i], pt);
        if (near_dist == null || dist < near_dist) {
            near_dist = dist;
            ind = i;
        }
    }

    return ind;
}

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: 40.77638, lng: -73.96957},
        zoom: 12,
        disableDoubleClickZoom: true,
        draggable: true,
    });

    var marker = new google.maps.Marker({
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            strokeColor: "blue",
            scale: 6
        },
        title: 'Pickup Station',
        map: map
    });

    d3.csv("stations", function (d) {
            return {lat: +d.lat, lng: +d.lng};
        }, function(data) {
            sts = data;
            var redPin = getPin("FE7569");
            var bluePin = getPin("ADD8E6");

            var inits = [47, 35, 42, 21];

            // for (var i = 0; i < inits[i]; i++)
            // {
            //     if (i % 2 == 0) {
            //         inits[i]
            //     }
            // }

            p0_marker = new google.maps.Marker({
                icon: bluePin,
                position: sts[inits[0]],
                map: map,
                draggable: true,
                title:"Drag me!"
            });

            d0_marker = new google.maps.Marker({
                icon: redPin,
                position: sts[inits[1]],
                map: map,
                draggable: true,
                title:"Drag me!"
            });

            p1_marker = new google.maps.Marker({
                icon: bluePin,
                position: sts[inits[2]],
                map: map,
                draggable: true,
                title:"Drag me!"
            });

            d1_marker = new google.maps.Marker({
                icon: redPin,
                position: sts[inits[3]],
                map: map,
                draggable: true,
                title:"Drag me!"
            });

            var t0 = [sts[inits[0]], sts[inits[1]]];
            var t1 = [sts[inits[2]], sts[inits[3]]];

            line_0 = new google.maps.Polyline({
                path: t0,
                geodesic: true,
                strokeColor: '#FF0000',
                strokeOpacity: 1.0,
                strokeWeight: 2,
                map: map
            });

            line_1 = new google.maps.Polyline({
                path: t1,
                geodesic: true,
                strokeColor: '#458B00',
                strokeOpacity: 1.0,
                strokeWeight: 2,
                map: map
            });

            markers = [p0_marker, d0_marker, p1_marker, d1_marker];
            partners = [d0_marker, p0_marker, d1_marker, p1_marker];
            oris = [p0_marker, p1_marker];
            dsts = [d0_marker, d1_marker];
            lines = [line_0, line_1];

            function updatePlot() {
                var inds = new Array();

                for (var i = 0; i < 4; i++) {
                    inds.push(getNearest(markers[i].position));
                }

                var cor_url = "/correlation_graph/" + inds.join("/");
                var bar_url = "/bar_graph/" + inds.join("/");

                $.get(cor_url, function(data) {
                    $("#cor").html(data);
                });

                $.get(bar_url, function(data) {
                    $("#bar").html(data);
                });

            }

            function makeDragCallback(i) {
                var partner = partners[i];
                var line = lines[Math.floor(i / 2)];

                return function(ev) {
                    var path = [ev.latLng, partner.position];
                    line.setPath(path);
                }
            }

            for (var i = 0; i < 4; i++) {
                markers[i].addListener("drag", makeDragCallback(i));
                markers[i].addListener("dragend", updatePlot);
            }
            // $(document).ajaxStart(function() {
            //     $("#graph").addClass("loading");
            // });
            // $(document).ajaxStop(function() {
            //     $("#graph").removeClass("loading");
            // });

    });
}
