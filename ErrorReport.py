from arcgis.gis import GIS
from arcgis import features
from datetime import datetime

# Login via ArcGIS Pro
gis = GIS("pro")
print('Login Successful')


# Dict of Error Reports to record
# Name of feature layer: (item id, map id)
#"Error Report": "88a946db49bd40829d57a645d02442f6",
er = {
    "FC Error Report": ("38919dbf7917404e80650a8891c60f2e", "a47455887dac4f7fa9fedbb79826fdbc"),
    "NHS Error Report": ("d2afd94945a84b9494f8603dd86b0c8f", "9a0f8f44a47549f4aad6541d45e64788")
    }

# Path for output html file
OutputPath = r'C:\Users\daniel.fourquet\Desktop\FC NHS Status'
OutputFileName = 'Error_Reports.html'

# Title for output HTML page
title = "Dan's AGOL Error Reports"


class ErrorReport:
    def __init__(self, featureLayer, label, mapID):
        self.name = label
        self.serviceItemId = featureLayer.properties.serviceItemId
        self.url = f'https://vdot.maps.arcgis.com/home/item.html?id={self.serviceItemId}'
        self.features = featureLayer.query().features
        self.lastUpdateTime = datetime.utcfromtimestamp(featureLayer.properties.editingInfo.lastEditDate / 1000).strftime("%x %X")
        self.mapID = mapID

        self.newErrorCount, self.inProgressCount, self.fixedCount, self.cannotFixCount = self.get_status_counts(self.features)

        self.card = self.create_card_html()
        self.modal = self.create_modal_html(self.features)
        

    
    def get_status_counts(self, features):
        newErrorCount = inProgressCount = fixedCount = cannotFixCount = 0

        for feature in features:
            s = feature.get_value("Status")
            if s == "New Error":
                newErrorCount += 1
            if s == "Fix in Progress":
                inProgressCount += 1
            if s == "Unable to Fix":
                fixedCount += 1
            if s == "Fix Complete":
                cannotFixCount += 1

        return newErrorCount, inProgressCount, fixedCount, cannotFixCount

    
    def create_card_html(self):
        html = htmlTemplates["card"]

        html = html.replace("[ERROR_REPORT_NAME]",self.name)
        html = html.replace("[NEW_ERROR_COUNT]",str(self.newErrorCount))
        html = html.replace("[IN_PROGRESS_COUNT]",str(self.inProgressCount))
        html = html.replace("[FIXED_COUNT]",str(self.fixedCount))
        html = html.replace("[CANNOT_FIX_COUNT]",str(self.cannotFixCount))
        html = html.replace("[date]",str(self.lastUpdateTime))
        html = html.replace("[URL]",self.url)
        html = html.replace("[SERVICE_ITEM_ID]", "id" + self.serviceItemId)  # "id" because html ids cannot start with a number

        return html


    def create_modal_html(self, features):
        modalHTML = htmlTemplates["modal"]
        modalHTML = modalHTML.replace("[SERVICE_ITEM_ID]", "id" + self.serviceItemId)  # "id" because html ids cannot start with a number
        modalHTML = modalHTML.replace("[MODAL_TITLE]", self.name)
        modalHTML = modalHTML.replace("[TABLE]", self.create_table_html(features))
        return modalHTML


    def create_table_html(self, features):
        if len(features) < 1:
            return "<h3>No records to display</h3>"

        tableHTML = '<table class="table table-hover"">'

        # Create table head
        ignoreFields = ['OBJECTID', 'GlobalID', 'CreationDate', 'Creator', 'EditDate', 'Editor']  # List of fields to skip
        fields = []  # List of fields to include

        headHTML = "<thead><tr>"
        headHTML += '<th scope="col"></th><th scope="col"></th>' # Spaces above map and AGOL buttons
        for field in features[0].fields:
            if field not in ignoreFields:
                fields.append(field)
                headHTML += f'<th scope="col">{field}</th>'
        headHTML += "</thead></tr>"

        # Create table body
        bodyHTML = "<tbody>"
        for feature in features:         
            # Get feature attributes and geometry   
            attr = feature.attributes
            geom = feature.geometry

            # Get feature location
            lat = str(geom['y'])
            lng = str(geom['x'])

            # Start row HTML
            bodyHTML += "<tr>"

            # Add View Map Button
            bodyHTML += "<td class='viewMap' data-lat='" + lat + "' data-lng='" + lng + "' data-mapID='" + self.mapID + "' data-comment='" + attr['ErrorComment'] + "'><div class='df-btn table-btn'>View Map</div></td>"

            # Add Open in AGOL Button
            bodyHTML += "<td class='openInAGOL' data-lat='" + lat + "' data-lng='" + lng + "' data-mapID='" + self.mapID + "'><div class='df-btn table-btn' >Open in AGOL</div></td>"

            # Add records
            for field in fields:
                bodyHTML += "<td>"
                bodyHTML += str(attr[field])
                bodyHTML += "</td>"
            
            bodyHTML += "</tr>"

        # Add head and body to table tag
        tableHTML += headHTML
        tableHTML += bodyHTML
        tableHTML += "</table>"

        return tableHTML
        





    
def build_html():
    """ Builds html page from main template.
        The html for individual reports is created in the ErrorReport class.
     """

    def build_error_report_cards():
        """ Error reports are displayed in html cards.
            For each feature service in er, this function collects
            the report card and returns them as a single string """

        html = ""

        for key in er.keys():
            report = er[key]
            card = report.card
            html += card

        return html


    def build_modals():
        """ Build the modals that will display the records
            for each error report """

        html = ""

        for key in er.keys():
            report = er[key]
            modal = report.modal
            html += modal

        return html

        
    # Load base template
    html = htmlTemplates["main"]

    # Insert title
    html = html.replace("[Title]", title)

    # Error reports are stored in card columns
    # They are inserted into the template here
    html = html.replace("[ERROR_REPORTS]", build_error_report_cards())
    html = html.replace("[LAST_UPDATE]", str(datetime.now().strftime("%x %X")))
    html = html.replace("[MODALS]", build_modals())

    return html


def main():

    # Replace item id's in er (error report) dict with ErrorReport objects
    # er dictionary format: {Name of feature layer: (item id, map id)}
    for key in er.keys():
        # Get layer from dictionary
        layerCollection = gis.content.get(er[key][0])
        featureLayer = layerCollection.layers[0]

        # Get mapid from dictionary
        mapID = er[key][1]

        # Create errorReport object
        errorReport = ErrorReport(featureLayer, key, mapID)

        # Store errorReport object in er dictionary, replacing input tuple
        er[key] = errorReport

    # Generate html from error report collection
    html = build_html()

    with open(f'{OutputPath}\\{OutputFileName}', 'w') as file:
        file.write(html)


htmlTemplates = {
    "main": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <title>Bootstrap 4 Minimal Template</title>

    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">

    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>

    <link rel="stylesheet" href="style.css">

    
</head>

<body>
    <div class="jumbotron jumbotron-fluid">
        <div class="container">
            <h1 class="display-3">[Title]</h1>
            <hr>
            <p>Last updated [LAST_UPDATE]</p>
        </div>
    </div>

    <div class="container">
        <div class="card-columns">
            [ERROR_REPORTS]
        </div>
    </div>

    <div class="jumbotron jumbotron-fluid footer">
        <div class="container">

        </div>
    </div>
    <!-- Modals that hold error report records -->
    [MODALS]
    
    <!-- Map Modal -->
    <div class="modal" id="mapModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="MapLabel">Error Report Location</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                </div>
                <div class="modal-body">
                    <div id="map"></div>
                </div>
                <div class="modal-footer">
                    <div id="btnGoHereInAGOL" class="df-btn btnGoHereInAGOL" data-dismiss="modal" data-mapID="test">Go Here in AGOL</div>
                    <div class="df-btn" data-dismiss="modal">Close</div>
                </div>
            </div>
        </div>
    </div>

    
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>

    <script>
        $(document).ready(function() {
            // Set up map
            var map = L.map("map").setView([37.5, -77.4], 10);
            
            // Basemap
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);
            
            // Error report location
            var marker = L.circleMarker([0,0], {radius:10, fillColor: 'red', fillOpacity:  0.5}).addTo(map);
        
            

            function show_map(lat, lng, mapid, comment) {
                // Show map modal
                $('#mapModal').modal('show');
                
                // Move comment marker
                let coords = L.latLng(lat, lng);
                marker.setLatLng(coords);
                
                if (comment) {
                    marker.bindPopup(comment);
                }
                
                // Set map view
                map.setView(coords, 13);
                
                // Set Go to AGOL button
                $("#btnGoHereInAGOL").attr('data-mapID', mapid);
                                    
                                    // Fix issue with map size within modal
            setTimeout(function() {
                map.invalidateSize();
            }, 500);
            }
            
            
            // Event Listeners
            $("#btnGoHereInAGOL").on("click", function() {
                let mapID = $('#btnGoHereInAGOL').attr('data-mapID');
                let coords = map.getCenter();
                let lat = coords.lat;
                let lng = coords.lng;
                let level = map.getZoom();
                let url = 'https://www.arcgis.com/home/webmap/viewer.html?webmap=' + mapID + '&center=' + lng + ',' + lat + '&level=' + level;
                window.open(url);
            });
            
            $('.viewMap').on('click', function() {
                // Convert coordinates
                let t = $(this);
                let lat = t.attr('data-lat');
                let lng = t.attr('data-lng');
                point = new L.Point(lng, lat);
                coords = L.Projection.SphericalMercator.unproject(point);
                
                lat = coords.lat;
                lng = coords.lng;
                
                console.log('Lat: ' + lat + '   Lng: ' + lng);
                
                let mapID = t.attr('data-mapID');
                let comment = t.attr('data-comment');
                show_map(lat, lng, mapID, comment);
            })

            $('.openInAGOL').on('click', function() {
                // Convert coordinates
                let t = $(this);
                let lat = t.attr('data-lat');
                let lng = t.attr('data-lng');
                point = new L.Point(lng, lat);
                coords = L.Projection.SphericalMercator.unproject(point);
                
                lat = coords.lat;
                lng = coords.lng;
                
                console.log('Lat: ' + lat + '   Lng: ' + lng);
                
                let mapID = t.attr('data-mapID');
                let url = 'https://www.arcgis.com/home/webmap/viewer.html?webmap=' + mapID + '&center=' + lng + ',' + lat + '&level=13';
                window.open(url);
            })
        })
    </script>
</body>
</html>""",
    "card": """<div class="card">
                <div class="card-body">
                    <h4 class="card-title">[ERROR_REPORT_NAME]</h4>
                    <ul>
                        <li class="card-text">There are <span class="error newErrorCount">[NEW_ERROR_COUNT]</span> new errors.</li>
                        <li class="card-text"><span class="error inProgressCount">[IN_PROGRESS_COUNT]</span> errors are being fixed now.</li>
                        <li class="card-text"><span class="error fixedCount">[FIXED_COUNT]</span> errors have been fixed.</li>
                        <li class="card-text"><span class="error cannotFixCount">[CANNOT_FIX_COUNT]</span> errors can not be fixed.</li>
                        <p class="card-text"><small class="text-muted">Last updated [date]</small></p>
                    </ul>
                    <a href="" class="df-btn er-btn btn" data-toggle="modal" data-target="#[SERVICE_ITEM_ID]">View Records</a>
                    <a href="[URL]" target="_blank" class="df-btn er-btn">View in AGOL</a>
                </div>
            </div>""",
    "modal": """<div class="modal fade" id="[SERVICE_ITEM_ID]" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-xl modal-dialog-scrollable" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="exampleModalLabel">[MODAL_TITLE]</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                </div>
                <div class="modal-body">
                    [TABLE]
                </div>
                <div class="modal-footer">
                    <div class="df-btn" data-dismiss="modal">Close</div>
                </div>
            </div>
        </div>
    </div>"""
}


if __name__ == '__main__':
    main()