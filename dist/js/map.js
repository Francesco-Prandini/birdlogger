
      var map;
      var latitude;
      var longitude;
	
      function initMap() {
        map = new google.maps.Map(document.getElementById('map'), {
          zoom: 7,
	  minZoom: 7,
          //center: new google.maps.LatLng(45.00,11.00),
          mapTypeId: 'terrain'
        });
	
	var allowedBounds = new google.maps.LatLngBounds(
	  new google.maps.LatLng(43.5, 8.0), 
	  new google.maps.LatLng(46.0, 15)
	);
	var lastValidCenter = map.getCenter();

        var postShowWindow = new google.maps.InfoWindow({maxWidth: 300});
	postShowWindow.addListener('closeclick', function(event){map.set('scrollwheel', true);});
        var postSubmitWindow = new google.maps.InfoWindow({maxWidth: 200});
        postSubmitWindow.addListener('closeclick', function(event){map.set('scrollwheel', true);});
	
	//var geolocation = {};
	
	getLocation();
	
	map.data.loadGeoJson('data.json');
	
	map.data.addListener('click', function(event){	  
	    map.set('scrollwheel', false);
	    point=event.feature.getGeometry().get();
	    postShowWindow.setPosition(point);
	    postShowWindow.setContent(httpGet('post?postId='+event.feature.getProperty("postId")));
	    postShowWindow.open(map);    
	    //window.open('post?postId='+event.feature.getProperty("id"))
	    
	});
	
	map.addListener( 'click', function(event) {
	    map.set('scrollwheel', false);
	    //placeMarker(event.latLng, map);
	    postSubmitWindow.setPosition(event.latLng)
	    if(typeof latitude==='undefined' || typeof longitude==='undefined'){
		postSubmitWindow.setContent(httpGet('post_upload?lat='+event.latLng.lat()+'&lng='+event.latLng.lng()));
		postSubmitWindow.open(map);
	    }else{
		postSubmitWindow.setContent(httpGet('post_upload?lat='+latitude+'&lng='+longitude));
		postSubmitWindow.open(map);
	    }
	    //postSubmitWindow.open(map);
	    //window.open('image_upload')
	});
	

	var lastValidCenter = map.getCenter();

	google.maps.event.addListener(map, 'center_changed', function() {
	  if (allowedBounds.contains(map.getCenter())) {
	    lastValidCenter = map.getCenter();
	    return; 
	}
	map.setCenter(lastValidCenter);
	});
	
	var ctaLayer = new google.maps.KmlLayer({
          url: 'http://www.emiliaromagnaturismo.it/it/come-arrivare/mappa-confini-regione.kml/at_download/file',
          map: map
        });

	
      }
      
      function placeMarker(latlng, map){
	var marker = new google.maps.Marker({
	    position: latlng,
	    map: map
	});
      }
      function httpGet(url){
	var xmlHttp = new XMLHttpRequest();
	xmlHttp.open( "GET", url, false ); // false for synchronous request
	xmlHttp.send();
	return xmlHttp.responseText;

      }
      function sendCoord(postion){
	  postSubmitWindow.setContent(httpGet('post_upload?lat='+position.coords.latitude+'&lng='+position.coords.longitude));
	  postSubmitWindow.open(map);
      }
      function error(err) {
	console.warn(`ERROR(${err.code}): ${err.message}`);
	};
	function getLocation() {
    // If the user allow us to get the location from the browser
	    if(navigator.geolocation){
		navigator.geolocation.getCurrentPosition(function(position){
		    latitude = position.coords.latitude;
		    longitude = position.coords.longitude;
		});
	    }
}
    
    
  

