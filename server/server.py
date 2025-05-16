import flask
import pyodbc
from flask_cors import CORS

# Kết nối tới SQL Server
conn_str = (
    "Driver={SQL Server};"
    "Server=TDV-LAPTOP\\DUYVU;"  # Cập nhật theo tên server của bạn
    "Database=VeXemPhim;"
    "Trusted_Connection=yes;"
)
con = pyodbc.connect(conn_str)

app = flask.Flask(__name__)
CORS(app)

# Hàm dùng chung để lấy toàn bộ dữ liệu từ 1 bảng
def fetch_all(table_name):
    cursor = con.cursor()
    sql = f"SELECT * FROM {table_name}"
    cursor.execute(sql)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Các route API
@app.route('/nguoidung/getall', methods=['GET'])
def get_all_nguoi_dung():
    return flask.jsonify(fetch_all('nguoi_dung'))

@app.route('/phim/getall', methods=['GET'])
def get_all_phim():
    return flask.jsonify(fetch_all('phim'))

@app.route('/phongchieu/getall', methods=['GET'])
def get_all_phong_chieu():
    return flask.jsonify(fetch_all('phong_chieu'))

@app.route('/ghe/getall', methods=['GET'])
def get_all_ghe():
    return flask.jsonify(fetch_all('ghe'))

@app.route('/suatchieu/getall', methods=['GET'])
def get_all_suat_chieu():
    return flask.jsonify(fetch_all('suat_chieu'))

@app.route('/vedat/getall', methods=['GET'])
def get_all_ve_dat():
    return flask.jsonify(fetch_all('ve_dat'))

if __name__ == '__main__':
    app.run(debug=True)
