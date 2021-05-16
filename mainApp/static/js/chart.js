let mstData;
/*
    Hàm lấy dữ liệu từ API để trả dữ liệu Json vào mydata rồi gọi hàm render của từng template
    pathAPI lấy ở script trong template để lấy url api
*/
function fetchJson(pathAPI, getValueFilter){
    let url_api = 'http://'+ window.location.host + pathAPI  + getValueFilter;
    document.getElementById('messagesGetChart').style.display = 'none';
    fetch(url_api)
    .then(function(response) {
        if(!response.ok) throw new Error("HTTP error, status = " + response.status);
        let myjson_data = response.json();
        
        return myjson_data;
    })
    .then(function(mydata){
        mstData = mydata;
        // Render ra đồ thi 
        renderChart(mydata);
        // Render ra bảng thông tin bổ xung của đồ thi
        renderTable(mydata);
    })
    .catch(function(error) {
        console.log("error");
        document.getElementById('messagesGetChart').style.display = '';
        document.getElementById('table-statistical').style.display = 'none';
    })
}

// Nối các String để thành url của API các filter
function changeUnitToCallAPI(objectGet, id){
    let pathAPI = '/adminuet/base-list/' ;
    let url_api = 'http://'+ window.location.host + pathAPI  + objectGet + id;
    return url_api;
}
$(window).on('load', function() {
    $('#exampleModal').modal('show');
});