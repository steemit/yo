  // Initialize Firebase
  var config = {
      apiKey: "AIzaSyCqF8QYlFUEZ1i6Pd-lKc4PLMQbUZQzHOg",
      authDomain: "androidgcm-testing.firebaseapp.com",
      databaseURL: "https://androidgcm-testing.firebaseio.com",
      projectId: "androidgcm-testing",
      storageBucket: "androidgcm-testing.appspot.com",
      messagingSenderId: "949229151994"
					    };
  firebase.initializeApp(config);

// these functions are shamelessly ripped from google's tutorials - i'm a backend guy, not a UI guy
function registerServiceWorker() {
	  return navigator.serviceWorker.register('/gcm/js/service_worker.js')
		    .then(function(registration) {
			        console.log('Service worker successfully registered.');
				    return registration;
				      })
	    .catch(function(err) {
		        console.error('Unable to register service worker.', err);
			  });
}

function askPermission() {
	  return new Promise(function(resolve, reject) {
		      const permissionResult = Notification.requestPermission(function(result) {
			            resolve(result);
        });
          if (permissionResult) {
	        permissionResult.then(resolve, reject);
	    }
			    })
	    .then(function(permissionResult) {
		        if (permissionResult !== 'granted') {
				      throw new Error('We weren\'t granted permission.');
				          }
			  });
}

function urlBase64ToUint8Array(base64String) {
	  const padding = '='.repeat((4 - base64String.length % 4) % 4);
	  const base64 = (base64String + padding)
	    .replace(/\-/g, '+')
	    .replace(/_/g, '/')
	  ;
	  const rawData = window.atob(base64);
	  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

function subscribeUserToPush(service_reg) {
	  return service_reg.then(function(registration) {
		const subscribeOptions = {
		      userVisibleOnly: true,
		      applicationServerKey: urlBase64ToUint8Array('%%SERVER_KEY%%')
	        };
                return registration.pushManager.subscribe(subscribeOptions);
         }).then(function(pushSubscription) {
                console.log('Received PushSubscription: ', JSON.stringify(pushSubscription));
                $.ajax({
	                 type:"POST",
	                 url:"/gcm/add_sub",
	                 data:JSON.stringify(pushSubscription),
	                 dataType:"json",
			 
	                 success:function(response) {
	                     console.log("Transmitted subscription to server, got back response: ", JSON.stringify(response));
	                }
                });

		 return pushSubscription;
         });
}

function subscribeUser() {
         var $service_reg = registerServiceWorker();
	 askPermission();
	 var sub = subscribeUserToPush($service_reg);
	 console.log(sub);
        $.ajax({
               type:"POST",
	       url:"/gcm/add_sub",
	       data:sub,
	       dataType:"json",
	       success:function(response) {
                   console.log("Transmitted subscription to server, got back response: ", JSON.stringify(response));
	       }
	});
}
