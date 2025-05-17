import flask
import pyodbc
from flask_cors import CORS

# Khởi tạo ứng dụng Flask
app = flask.Flask(__name__)
CORS(app)  # Cho phép yêu cầu cross-origin

# Hàm tạo kết nối cơ sở dữ liệu
def get_db_connection():
    conn_str = (
        "Driver={SQL Server};"
        "Server=TDV-LAPTOP\\DUYVU;"  # Thay đổi tên server nếu cần
        "Database=VeXemPhim;"
        "Trusted_Connection=yes;"
    )
    try:
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        print(f"Lỗi kết nối cơ sở dữ liệu: {str(e)}")
        raise

# Hàm lấy tất cả dữ liệu từ một bảng
def fetch_all(table_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = f"SELECT * FROM {table_name}"
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return rows
    except pyodbc.Error as e:
        print(f"Lỗi khi lấy dữ liệu: {str(e)}")
        return []

# Endpoint đăng ký người dùng
@app.route('/api/dangky', methods=['POST'])
def dang_ky():
    data = flask.request.get_json()
    ho_ten = data.get('hoTen')
    email = data.get('email')
    sdt = data.get('sdt')
    mat_khau = data.get('matKhau')
    ten_dang_nhap = email  # Sử dụng email làm tên đăng nhập

    # Kiểm tra các trường bắt buộc
    if not all([ho_ten, email, sdt, mat_khau]):
        return flask.jsonify({
            'success': False,
            'message': 'Vui lòng nhập đầy đủ thông tin'
        }), 400

    # Kiểm tra định dạng email
    if '@' not in email or '.' not in email:
        return flask.jsonify({
            'success': False,
            'message': 'Email không hợp lệ'
        }), 400

    # Kiểm tra độ dài mật khẩu
    if len(mat_khau) < 6:
        return flask.jsonify({
            'success': False,
            'message': 'Mật khẩu phải có ít nhất 6 ký tự'
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Kiểm tra email hoặc tên đăng nhập đã tồn tại
        cursor.execute(
            "SELECT * FROM nguoi_dung WHERE email = ? OR ten_dang_nhap = ?",
            (email, ten_dang_nhap)
        )
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return flask.jsonify({
                'success': False,
                'message': 'Email hoặc tên đăng nhập đã được sử dụng'
            }), 400

        # Thêm người dùng mới vào cơ sở dữ liệu
        cursor.execute(
            """
            INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, ho_ten, email, so_dien_thoai, la_quan_tri)
            OUTPUT INSERTED.nguoidung_id, INSERTED.ten_dang_nhap, INSERTED.ho_ten, INSERTED.la_quan_tri
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ten_dang_nhap, mat_khau, ho_ten, email, sdt, 0)
        )
        
        user = cursor.fetchone()
        conn.commit()
        
        # Trả về thông tin người dùng vừa đăng ký
        response = {
            'success': True,
            'message': 'Đăng ký thành công',
            'user': {
                'id': user.nguoidung_id,
                'ten_dang_nhap': user.ten_dang_nhap,
                'ho_ten': user.ho_ten,
                'la_quan_tri': user.la_quan_tri
            }
        }
        
        cursor.close()
        conn.close()
        return flask.jsonify(response), 201

    except pyodbc.Error as e:
        return flask.jsonify({
            'success': False,
            'message': f'Lỗi cơ sở dữ liệu: {str(e)}'
        }), 500
    except Exception as e:
        return flask.jsonify({
            'success': False,
            'message': f'Lỗi không xác định: {str(e)}'
        }), 500

# Endpoint đăng nhập
@app.route('/api/dangnhap', methods=['POST'])
def dang_nhap():
    data = flask.request.get_json()
    ten_dang_nhap = data.get('tenDangNhap')
    mat_khau = data.get('matKhau')

    # Kiểm tra các trường bắt buộc
    if not ten_dang_nhap or not mat_khau:
        return flask.jsonify({
            'success': False,
            'message': 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu'
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tìm người dùng theo tên đăng nhập hoặc email
        cursor.execute(
            """
            SELECT nguoidung_id, ten_dang_nhap, mat_khau, ho_ten, la_quan_tri
            FROM nguoi_dung 
            WHERE ten_dang_nhap = ? OR email = ?
            """,
            (ten_dang_nhap, ten_dang_nhap)
        )
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return flask.jsonify({
                'success': False,
                'message': 'Tên đăng nhập hoặc email không tồn tại'
            }), 401

        # Kiểm tra mật khẩu
        if user.mat_khau != mat_khau:
            cursor.close()
            conn.close()
            return flask.jsonify({
                'success': False,
                'message': 'Mật khẩu không đúng'
            }), 401

        # Trả về thông tin người dùng
        response = {
            'success': True,
            'message': 'Đăng nhập thành công',
            'user': {
                'id': user.nguoidung_id,
                'ten_dang_nhap': user.ten_dang_nhap,
                'ho_ten': user.ho_ten,
                'la_quan_tri': user.la_quan_tri
            }
        }

        cursor.close()
        conn.close()
        return flask.jsonify(response), 200

    except pyodbc.Error as e:
        return flask.jsonify({
            'success': False,
            'message': f'Lỗi cơ sở dữ liệu: {str(e)}'
        }), 500
    except Exception as e:
        return flask.jsonify({
            'success': False,
            'message': f'Lỗi không xác định: {str(e)}'
        }), 500

# Các endpoint khác
@app.route('/api/phim', methods=['GET'])
def get_all_phim():
    phim_data = fetch_all('phim')
    for phim in phim_data:
        phim['id'] = phim.pop('phim_id')
        phim['ten'] = phim.pop('ten_phim')
        phim['moTa'] = phim.pop('mo_ta')
        phim['thoiLuong'] = phim.pop('thoi_luong')
        phim['tacGia'] = phim.pop('tac_gia')
    return flask.jsonify(phim_data)

@app.route('/api/nguoidung', methods=['GET'])
def get_all_nguoi_dung():
    return flask.jsonify(fetch_all('nguoi_dung'))

@app.route('/api/phongchieu', methods=['GET'])
def get_all_phong_chieu():
    return flask.jsonify(fetch_all('phong_chieu'))

@app.route('/api/ghe', methods=['GET'])
def get_all_ghe():
    return flask.jsonify(fetch_all('ghe'))

@app.route('/api/suatchieu', methods=['GET'])
def get_all_suat_chieu():
    return flask.jsonify(fetch_all('suat_chieu'))

@app.route('/api/vedat', methods=['GET'])
def get_all_ve_dat():
    return flask.jsonify(fetch_all('ve_dat'))

# Chạy ứng dụng
if __name__ == '__main__':
    app.run(debug=True, port=3000)