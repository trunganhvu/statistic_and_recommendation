//Hàm khởi tạo và chạy để  lấy và in ra dữ liệu(json + phân trang)
function main(offset, limit){
    setNumberSelectFromUrl(limit);
    fetchJson(offset, parseInt(limit));
}
//Hàm này lấy {{limit}} từ url để set cho form select để  hiển thị.
function setNumberSelectFromUrl(limit){
    let arraySelection = [];
    let limitExpected = limit;
    let number = document.getElementById("numberofrow");
    for (let i = 0; i < number.length; i++){
        arraySelection.push(number.options[i].value);
    }
    number.options[arraySelection.indexOf(limitExpected.toString())].selected = true;
    return limitExpected;
}
//Lắng nghe thay đổi, click của form select và load lại trang số 1 theo limit = value của selected.
function redictUrlClickOption(){
    window.open('http://'+ window.location.host + pathAdmin + pathForPage + 1 + '/limit' + getNumberOfRowInSelections(), '_parent' );
}
//Hàm fetchJson nhận dữ liệu từ API trả về và gọi đến hàm renderTable() và renderPagination()
function fetchJson(offset, limit){
    let checkLimit = getNumberOfRowInSelections();
    url_api = 'http://'+ window.location.host + pathAdmin + pathApiGetList + offset + '/' + limit;
    fetch(url_api)
    .then(function(response) {
        if(!response.ok) throw new Error("HTTP error, status = " + response.status);
        let myjson_data = response.json();
        document.getElementById("table-body").innerHTML = "";
        return myjson_data;
    })
    .then(function(mydata){
        if (Object.keys(mydata.data).length == 0){
            renderNotificationNoData()
        }
        else {
            renderTable(mydata);
            let page = mydata.numberOfPage;
            document.getElementById("pagination").innerHTML = '';
            renderPagination(page, currentPage, pathForPage);
        }  
    })
    .catch(function(error) {
        console.log("error");
    })
}
//Hàm renderPagination() nhận đầu vào là số lượng page và biến {{page}} - toàn cuc
//render ra các thành phân trang dạng html và có đánh dấu trang hiện thời. 
function renderPagination(pageNumber, currentPage, pathForPage){
    let row = '';
    for (let index = 1; index <= pageNumber; index++){
        let valueSelection2 = getNumberOfRowInSelections()
        url_page = pathAdmin + pathForPage + index +'/limit' + valueSelection2;
        if (index == currentPage){
            row += '<li class="page-item"><a href=\"'+ url_page+ '\" class="page-link activebutton" id="page1">' + index + '</a></li>';
        }
        else if (index==1 || index==2 || index==currentPage -1 || index==currentPage+1 || index== pageNumber || index == pageNumber - 1){
            row += '<li class="page-item"><a href=\"'+ url_page+ '\" class="page-link" id="page1">' + index + '</a></li>';
        }
        else if (index == 3 || index == pageNumber -2) {
            row += '<li class="page-item"><a href=\"'+ url_page+ '\" class="page-link" id="page1">' + '...' + '</a></li>';
        }
    }
    document.getElementById("pagination").innerHTML += row;
}
//Hàm lấy giá trị số lượng dòng mà người dùng muôn xem ở 1 trang table
function getNumberOfRowInSelections(){
    let numberOfRow1 = document.getElementById("numberofrow");
    let valueSelection1 = numberOfRow1.options[numberOfRow1.selectedIndex].value;
    return valueSelection1;
}
function renderNotificationNoData(){
    let textreturn = '<p style="color:#dc3545">Hiện tại danh mục này chưa có dữ liệu</p>';
    document.getElementById("pagination").innerHTML = textreturn;
}
var entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
};

function escapeHtml(string) {
    return String(string).replace(/[&<>"'`=\/]/g, function (s) {
        return entityMap[s];
    });
}
function encodeHTML(str){
    return str.replace(/([\u00A0-\u9999<>&])(.|$)/g, function(full, char, next) {
    if(char !== '&' || next !== '#'){
        if(/[\u00A0-\u9999<>&]/.test(next))
        next = '&#' + next.charCodeAt(0) + ';';
        return '&#' + char.charCodeAt(0) + ';' + next;
    }

    return full;
    });
}
function sortTableByColumn(table, column, asc = true) {
    const dirModifier = asc ? 1 : -1;
    const tBody = table.tBodies[0];
    const rows = Array.from(tBody.querySelectorAll("tr"));
    // Sort each row
    const sortedRows = rows.sort((a, b) => {
        const aColText = a.querySelector(`td:nth-child(${ column + 1 })`).textContent.trim();
        const bColText = b.querySelector(`td:nth-child(${ column + 1 })`).textContent.trim();

        return aColText > bColText ? (1 * dirModifier) : (-1 * dirModifier);
    });
    // Remove all existing TRs from the table
    while (tBody.firstChild) {
        tBody.removeChild(tBody.firstChild);
    }
    // Re-add the newly sorted rows
    tBody.append(...sortedRows);
    // Remember how the column is currently sorted
    table.querySelectorAll("th").forEach(th => th.classList.remove("th-sort-asc", "th-sort-desc"));
    table.querySelector(`th:nth-child(${ column + 1})`).classList.toggle("th-sort-asc", asc);
    table.querySelector(`th:nth-child(${ column + 1})`).classList.toggle("th-sort-desc", !asc);
}

document.querySelectorAll(".table th").forEach(headerCell => {
    headerCell.addEventListener("click", () => {
        const tableElement = headerCell.parentElement.parentElement.parentElement;
        const headerIndex = Array.prototype.indexOf.call(headerCell.parentElement.children, headerCell);
        const currentIsAscending = headerCell.classList.contains("th-sort-asc");
        sortTableByColumn(tableElement, headerIndex, !currentIsAscending);
    });
});
function searchForUnit(){
    // Hàm sắp xếp theo thứ tự giá trị của bảng theo thuộc tính
    let input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("myInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("myTable");
    tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++){
        td = tr[i].getElementsByTagName("td")[1];
        if (td) {
            txtValue = td.textContent || td.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) tr[i].style.display = "";
            else tr[i].style.display = "none";
        }   
    }
}