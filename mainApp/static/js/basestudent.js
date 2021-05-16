let pathname_url = window.location.pathname; 
let pathname_url_active = pathname_url.split("/")[1];
function activaCurrentUrlElement(){            
    let element = document.getElementById(pathname_url_active);
    if (element != null) element.classList.add("activeElementUrl");     
}
activaCurrentUrlElement();