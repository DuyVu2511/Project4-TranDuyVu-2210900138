import flask
import pyodbc
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)

def get_db_connection():
    conn_str = (
        "Driver={SQL Server};"
        "Server=TDV-LAPTOP\DUYVU;"  # Lưu ý dấu \\ cho escape trong chuỗi
        "Database=VeXemPhim;"
        "Trusted_Connection=yes;"
    )
    try:
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        print(f"Lỗi kết nối cơ sở dữ liệu: {str(e)}")
        raise

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

@app.route('/api/dangky', methods=['POST'])
def dang_ky():
    data = flask.request.get_json()
    ho_ten = data.get('hoTen')
    email = data.get('email')
    sdt = data.get('sdt')
    mat_khau = data.get('matKhau')
    ten_dang_nhap = email

    if not all([ho_ten, email, sdt, mat_khau]):
        return flask.jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'}), 400

    if '@' not in email or '.' not in email:
        return flask.jsonify({'success': False, 'message': 'Email không hợp lệ'}), 400

    if len(mat_khau) < 6:
        return flask.jsonify({'success': False, 'message': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM nguoi_dung WHERE email = ? OR ten_dang_nhap = ?", (email, ten_dang_nhap))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return flask.jsonify({'success': False, 'message': 'Email hoặc tên đăng nhập đã được sử dụng'}), 400

        cursor.execute("""
            INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, ho_ten, email, so_dien_thoai, la_quan_tri)
            OUTPUT INSERTED.nguoidung_id, INSERTED.ten_dang_nhap, INSERTED.ho_ten, INSERTED.la_quan_tri
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ten_dang_nhap, mat_khau, ho_ten, email, sdt, 0))

        user = cursor.fetchone()
        conn.commit()

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
        return flask.jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        return flask.jsonify({'success': False, 'message': f'Lỗi không xác định: {str(e)}'}), 500
@app.route('/api/dangnhap', methods=['POST'])
def dang_nhap():
    data = flask.request.get_json()
    ten_dang_nhap = data.get('tenDangNhap')
    mat_khau = data.get('matKhau')

    if not ten_dang_nhap or not mat_khau:
        return flask.jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nguoidung_id, ten_dang_nhap, mat_khau, ho_ten, la_quan_tri
            FROM nguoi_dung 
            WHERE ten_dang_nhap = ? OR email = ?
        """, (ten_dang_nhap, ten_dang_nhap))

        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return flask.jsonify({'success': False, 'message': 'Tên đăng nhập hoặc email không tồn tại'}), 401

        if user.mat_khau != mat_khau:
            cursor.close()
            conn.close()
            return flask.jsonify({'success': False, 'message': 'Mật khẩu không đúng'}), 401

        # Đưa la_quan_tri lên cấp cao nhất trong JSON trả về
        response = {
            'success': True,
            'message': 'Đăng nhập thành công',
            'la_quan_tri': bool(user.la_quan_tri),  # Chuyển về kiểu bool rõ ràng
            'user': {
                'id': user.nguoidung_id,
                'ten_dang_nhap': user.ten_dang_nhap,
                'ho_ten': user.ho_ten
            }
        }

        cursor.close()
        conn.close()
        return flask.jsonify(response), 200

    except pyodbc.Error as e:
        return flask.jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        return flask.jsonify({'success': False, 'message': f'Lỗi không xác định: {str(e)}'}), 500

@app.route('/api/phim/', methods=['GET'])
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

# Endpoint đặt vé
@app.route('/api/datve', methods=['POST'])
def dat_ve():
    data = flask.request.get_json()
    nguoi_dung_id = data.get('nguoiDungId')
    suat_chieu_id = data.get('suatChieuId')
    danh_sach_ghe = data.get('danhSachGhe')  # danh sách các ghe_id, ví dụ: [1, 2, 3]

    if not nguoi_dung_id or not suat_chieu_id or not danh_sach_ghe or not isinstance(danh_sach_ghe, list):
        return flask.jsonify({'success': False, 'message': 'Dữ liệu đặt vé không hợp lệ'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Kiểm tra từng ghế xem đã được đặt cho suất chiếu đó chưa
        ghe_chua_dat = []
        ghe_da_dat = []
        for ghe_id in danh_sach_ghe:
            cursor.execute("""
                SELECT * FROM ve_dat 
                WHERE suat_chieu_id = ? AND ghe_id = ?
            """, (suat_chieu_id, ghe_id))
            if cursor.fetchone():
                ghe_da_dat.append(ghe_id)
            else:
                ghe_chua_dat.append(ghe_id)

        if ghe_da_dat:
            cursor.close()
            conn.close()
            return flask.jsonify({
                'success': False,
                'message': f'Ghế đã được đặt: {ghe_da_dat}'
            }), 400

        # Nếu tất cả ghế đều chưa đặt, tiến hành đặt vé
        for ghe_id in ghe_chua_dat:
            cursor.execute("""
                INSERT INTO ve_dat (nguoi_dung_id, suat_chieu_id, ghe_id)
                VALUES (?, ?, ?)
            """, (nguoi_dung_id, suat_chieu_id, ghe_id))

        conn.commit()
        cursor.close()
        conn.close()

        return flask.jsonify({
            'success': True,
            'message': 'Đặt vé thành công',
            'danhSachGheDat': ghe_chua_dat
        }), 201

    except pyodbc.Error as e:
        return flask.jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        return flask.jsonify({'success': False, 'message': f'Lỗi không xác định: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000)