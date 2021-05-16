let pathname_url_active = window.location.pathname.split("/")[2];
function activaCurrentUrlElement(){            
    let element = document.getElementById(pathname_url_active);
    if (element != null) element.classList.add("activeElementUrl");     
}
activaCurrentUrlElement();