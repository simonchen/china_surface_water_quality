from flask import Flask, request, render_template_string
import requests
import json

app = Flask(__name__)

def fetch_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    url = "https://szzdjc.cnemc.cn:8070/GJZ/Ajax/Publish.ashx?AreaID=&RiverID=&MNName=&PageIndex=-1&PageSize=60&action=getRealDatas"
    retries = 3
    ret_json = {"error": "Failed to fetch data"}
    while retries > 0:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            json = response.json()
            if type(json) is dict:
                ret_json = json
                break
        retries -= 1

    return ret_json

def generate_html(data):
    if "error" in data:
        return f"<p>{data['error']}</p>"

    thead = data['thead']
    tbody = data['tbody']

    p_list = []

    html_table = "<table border='0' cellspacing='0' cellpadding='0'>"
    html_table += "<thead><tr>"
    for header in thead:
        html_table += f"<th title='点我排序' style='cursor:hand;' onclick='sortTable({thead.index(header)})'>{header}</th>"
    html_table += "</tr></thead>"

    html_table += "<tbody>"
    for row in tbody:
        html_table += "<tr>"
        idx = 0
        for item in row:
            if item is None: item = ''
            if (idx == 0) and item not in p_list:
                p_list.append(item)
            html_table += f"<td>{item}</td>"
            idx += 1
        html_table += "</tr>"
    html_table += "</tbody>"
    html_table += "</table>"

    html_p = '<select onchange="filter()"><option value="" selected>全部</option>'
    for p in p_list:
        html_p += f'<option value="{p}">{p}</option>'
    html_p += "</select>"

    html_c = '<input id="dispHead" type="checkbox" onclick="dispHead()"></input><label for="dispHead">仅显示排序列</label><br><br>'

    html_css = """
<style type="text/css">
table {
    border: 1px solid #000;
}
th {
    border-bottom: 1px solid #000;
    border-right: 1px solid #000;
    padding: 5px;
}
td {
    border-right: 1px solid #000;
    border-bottom: 1px solid #000;
    padding: 5px;
}
</style>
"""
    return html_css + html_p + html_c + html_table

@app.route('/')
def index():
    data = fetch_data()
    html_table = generate_html(data)
    script = """
    <script>
    var _prev_n = -1;

    function dispHead(){
        var is_checked = document.querySelector("input").checked;
        if (_prev_n < 0) return;

        var sel = document.querySelector("select");
        var p = sel.value;
        var table, rows;
        table = document.querySelector("table");
        rows = table.rows;
        var rowCount = rows.length;
        for (i = 0; i < rowCount; i++) {
            var tds = rows[i].getElementsByTagName("td");
            if (!tds.length) tds = rows[i].getElementsByTagName("th");
            for (j = 4; j < tds.length; j++){
                if (is_checked && j != _prev_n){
                    tds[j].style.display = 'none';
                }else{
                    tds[j].style.display = '';
                    tds[j].style.width = is_checked ? '50%' : '';
                }
            }
        }
    }

    function filter(){
        if (_prev_n < 0) return;
        sortTable(_prev_n, true);
    /***
        var sel = document.querySelector("select");
        var p = sel.value;
        var table, rows;
        table = document.querySelector("table");
        rows = table.rows;
        var rowCount = rows.length;
        for (i = 1; i < rowCount; i++) {
            var cur_p = rows[i].getElementsByTagName("td")[0].innerText;
            rows[i].style.display = (p == '' || cur_p == p) ? '' : 'none';
        }
    ***/
    }

    function sortTable(n, keep_current_sort) {
        keep_current_sort = keep_current_sort || false;
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        table = document.querySelector("table");
        rows = table.rows;
        var rowCount = rows.length;
        var arr = [];

        var cur_th = rows[0].getElementsByTagName("th")[n];
        var method = cur_th.getAttribute('method') || 'asc';
        if (!keep_current_sort){
            method = (method == 'asc') ? 'desc' : 'asc';
        }
        cur_th.setAttribute('method', method);

        // 将表内容存储在内存数组变量中
        for (i = 1; i < rowCount; i++) {
            //if (_prev_n >= 0){
            //    rows[i].getElementsByTagName("td")[_prev_n].style.backgroundColor = '';
            //    rows[i].getElementsByTagName("td")[_prev_n].innerHTML = rows[i].getElementsByTagName("td")[_prev_n].innerHTML.replace(/<span class\="pct"[^<>]+><\/span>/ig, '');
            //}
            //rows[i].getElementsByTagName("td")[n].style.backgroundColor = '#eee';
            arr.push([rows[i], rows[i].getElementsByTagName("td")[n].innerText.toLowerCase()]);
        }

        // 使用快速排序算法对数组进行排序
        //quickSort(arr, 0, arr.length - 1);
        var MAX_NUMBER_STR = '999999';
        arr = arr.sort(function(it1, it2){
            if (it1[1] == '--') it1[1] = (method == 'asc') ? MAX_NUMBER_STR : '-1';
            if (it2[1] == '--') it2[1] = (method == 'asc') ? MAX_NUMBER_STR : '-1';
            var v1 = parseFloat(it1[1],10), v2 = parseFloat(it2[1],10);
            if (Number.isNaN(v1)) v1 = it1[1];
            if (Number.isNaN(v2)) v2 = it2[1];
            if (v1 > v2) return method == 'asc' ? 1 : -1;
            if (v1 < v2) return method == 'asc' ? -1 : 1;
            return 0;
        });

        // Finding max. number of current sorting column (maybe filtered by City)
        var sel = document.querySelector("select");
        var p = sel.value;
        var arr_num = [];
        arr.forEach(function(item){
            if (item[1] == MAX_NUMBER_STR) return;
            if (p.length > 0 && p != item[0].getElementsByTagName("td")[0].innerText) return;
            arr_num.push(item[1]);
        });
        var max_num = 0;
        if (arr_num.length > 0){
            max_num = parseFloat((method == 'asc') ? arr_num[arr_num.length-1] : arr_num[0], 10);
        }

        /***
        arr.forEach(function(item){
            var num = parseFloat(item[1],10);
            if (Number.isNaN(num) || Number.isNaN(max_num)) return;
            if (item[0].getElementsByTagName("td")[n].innerHTML.indexOf('class="pct"') >= 0) return;
            var pct = (num / max_num * 100).toFixed(2);
            if (pct < 1) pct = 1;
            item[0].getElementsByTagName("td")[n].innerHTML = '<span class="pct" style="display:inline-block;position:relative;height:12px;overflow:hidden;background-image:linear-gradient(to right, red, yellow ' + pct + '%, green);width:100%;"></span>' + item[0].getElementsByTagName("td")[n].innerHTML;
        });
        ***/

        // 按排序好的数组变量重新构建表内容
        var fragment = document.createDocumentFragment();
        fragment.appendChild(rows[0].cloneNode(true));
        for (i = 1; i < rowCount; i++) {
            var cloneRow = rows[i].cloneNode(true);
            cloneRow.innerHTML = arr[i-1][0].innerHTML;

            // setting background and percentage
            if (_prev_n >= 0){
                cloneRow.getElementsByTagName("td")[_prev_n].style.backgroundColor = '';
                cloneRow.getElementsByTagName("td")[_prev_n].innerHTML = cloneRow.getElementsByTagName("td")[_prev_n].innerHTML.replace(/<span class\="pct"[^<>]+><\/span>/ig, '');
            }
            cloneRow.getElementsByTagName("td")[n].style.backgroundColor = '#eee';
            var num = parseFloat(cloneRow.getElementsByTagName("td")[n].innerText,10);
            if (!Number.isNaN(num) && !Number.isNaN(max_num))
            {
                var pct = (num / max_num * 100).toFixed(2);
                if (pct < 1) pct = 1;
                cloneRow.getElementsByTagName("td")[n].innerHTML = '<span class="pct" style="display:inline-block;position:relative;height:12px;overflow:hidden;background-image:linear-gradient(to right, red, yellow ' + pct + '%, green);width:100%;"></span>' + cloneRow.getElementsByTagName("td")[n].innerHTML;
            }

            // filter by city
            cloneRow.style.display = (p == '' || cloneRow.getElementsByTagName("td")[0].innerText == p) ? '' : 'none';

            fragment.appendChild(cloneRow);
        }

        // 删除当前表内容
        table.innerHTML = "";

        // Adding fragment
        table.appendChild(fragment);

        // activate filter
        //filter();

        // disp heads
        dispHead();

        _prev_n = n;
    }

    function quickSort(arr, left, right) {
        if (left < right) {
            var pivotIndex = Math.floor((left + right) / 2);
            var pivotValue = arr[pivotIndex][1];
            var tempLeft = left;
            var tempRight = right;

            while (tempLeft <= tempRight) {
                while (arr[tempLeft][1] < pivotValue) {
                    tempLeft++;
                }
                while (arr[tempRight][1] > pivotValue) {
                    tempRight--;
                }
                if (tempLeft <= tempRight) {
                    var temp = arr[tempLeft];
                    arr[tempLeft] = arr[tempRight];
                    arr[tempRight] = temp;
                    tempLeft++;
                    tempRight--;
                }
            }

            quickSort(arr, left, tempRight);
            quickSort(arr, tempLeft, right);
        }
    }

    sortTable(0); // init
    </script>
    """
    return f"{html_table}{script}"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9898)
