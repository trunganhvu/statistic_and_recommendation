function searchTwoField(){
    // Hàm sắp xếp theo thứ tự giá trị của bảng theo thuộc tính
    let input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("myInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("myTable");
    tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++){
        td = tr[i].getElementsByTagName("td")[1];
        td2 = tr[i].getElementsByTagName("td")[2];
        
        if (td && td2) {
            txtValue = td.textContent || td.innerText;
            txtValue2 = td2.textContent || td2.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1 || txtValue2.toUpperCase().indexOf(filter) > -1) tr[i].style.display = "";
            else tr[i].style.display = "none";
        }   
    }
}

function searchThreeField(){
    // Hàm sắp xếp theo thứ tự giá trị của bảng theo thuộc tính
    let input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("myInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("myTable");
    tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++){
        td = tr[i].getElementsByTagName("td")[1];
        td2 = tr[i].getElementsByTagName("td")[2];
        td3 = tr[i].getElementsByTagName("td")[3];
        if (td && td2 && td3) {
            txtValue = td.textContent || td.innerText;
            txtValue2 = td2.textContent || td2.innerText;
            txtValue3 = td3.textContent || td3.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1 
                || txtValue2.toUpperCase().indexOf(filter) > -1
                || txtValue3.toUpperCase().indexOf(filter) > -1){
                    tr[i].style.display = "";
                } 
                
            else{
                tr[i].style.display = "none";
            } 
        }   
    }
}