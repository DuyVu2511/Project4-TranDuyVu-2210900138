import flask
import pyodbc
from flask_cors import CORS

app = flask.Flask(__name__)
CORS(app)
def get_db_connection():
    conn_str = (
        "Driver={SQL Server};"
        "Server=TDV-LAPTOP\DUYVU;"
        "Database=VeXemPhim;"
        "Trusted_Connection=yes;"
    )
    try:
        return pyodbc.connect(conn_str)
    except pyodbc.Error as e:
        print(f"Lỗi kết nối cơ sở dữ liệu: {str(e)}")
        raise

# -------------------- HÀM DÙNG CHUNG: LẤY DỮ LIỆU --------------------
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

# dang ký người dùng
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

    except Exception as e:
        return flask.jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

# dawdng nhập người dùng
@app.route('/api/dangnhap', methods=['POST'])
def dang_nhap():
    data = flask.request.get_json()
    ten_dang_nhap = data.get('tenDangNhap')
    mat_khau = data.get('matKhau')

    if not ten_dang_nhap or not mat_khau:
        return flask.jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'}), 400

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
            return flask.jsonify({'success': False, 'message': 'Tài khoản không tồn tại'}), 401
        if user.mat_khau != mat_khau:
            return flask.jsonify({'success': False, 'message': 'Mật khẩu không đúng'}), 401

        response = {
            'success': True,
            'message': 'Đăng nhập thành công',
            'la_quan_tri': bool(user.la_quan_tri),
            'user': {
                'id': user.nguoidung_id,
                'ten_dang_nhap': user.ten_dang_nhap,
                'ho_ten': user.ho_ten
            }
        }

        cursor.close()
        conn.close()
        return flask.jsonify(response), 200

    except Exception as e:
        return flask.jsonify({'success': False, 'message': str(e)}), 500

# crud người dùngdùng
@app.route('/api/nguoidung', methods=['GET'])
def get_all_nguoi_dung():
    return flask.jsonify(fetch_all('nguoi_dung'))
# thêm người dùngdùng
@app.route('/api/nguoidung', methods=['POST'])
def them_nguoi_dung():
    data = flask.request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nguoi_dung (ten_dang_nhap, mat_khau, ho_ten, email, so_dien_thoai, la_quan_tri)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data['ten_dang_nhap'],
            data['mat_khau'],
            data.get('ho_ten'),
            data.get('email'),
            data.get('so_dien_thoai'),
            int(data.get('la_quan_tri', False))
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return flask.jsonify({'success': True, 'message': 'Thêm người dùng thành công'}), 201
    except Exception as e:
        return flask.jsonify({'success': False, 'message': str(e)}), 500
#sua nguoi dung
@app.route('/api/nguoidung/<int:nguoidung_id>', methods=['PUT'])
def sua_nguoi_dung(nguoidung_id):
    data = flask.request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE nguoi_dung
            SET ten_dang_nhap = ?, mat_khau = ?, ho_ten = ?, email = ?, so_dien_thoai = ?, la_quan_tri = ?
            WHERE nguoidung_id = ?
        """, (
            data['ten_dang_nhap'],
            data['mat_khau'],
            data.get('ho_ten'),
            data.get('email'),
            data.get('so_dien_thoai'),
            int(data.get('la_quan_tri', False)),
            nguoidung_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return flask.jsonify({'success': True, 'message': 'Cập nhật người dùng thành công'}), 200
    except Exception as e:
        return flask.jsonify({'success': False, 'message': str(e)}), 500
#xoa nguoi dung
@app.route('/api/nguoidung/<int:nguoidung_id>', methods=['DELETE'])
def xoa_nguoi_dung(nguoidung_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM nguoi_dung WHERE nguoidung_id = ?", (nguoidung_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return flask.jsonify({'success': True, 'message': 'Xóa người dùng thành công'}), 200
    except Exception as e:
        return flask.jsonify({'success': False, 'message': str(e)}), 500

# danh sach phim 
@app.route('/api/phim', methods=['GET'])
def get_all_phim():
    phim_data = fetch_all('phim')
    for phim in phim_data:
        phim['id'] = phim.pop('phim_id')
        phim['ten'] = phim.pop('ten_phim')
        phim['moTa'] = phim.pop('mo_ta')
        phim['thoiLuong'] = phim.pop('thoi_luong')
        phim['tacGia'] = phim.pop('tac_gia')
        phim['trailer'] = phim.pop('trailer')
    return flask.jsonify(phim_data)

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

@app.route('/api/vedat/nguoidung/<int:nguoi_dung_id>', methods=['GET'])
def get_ve_dat_by_nguoi_dung(nguoi_dung_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Chỉ lấy các cột cần thiết
        sql = """
            SELECT nguoi_dung_id, suat_chieu_id, ghe_id, thoi_gian_dat, trang_thai
            FROM ve_dat
            WHERE nguoi_dung_id = ?
        """
        cursor.execute(sql, (nguoi_dung_id,))

        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        if not rows:
            return flask.jsonify({
                'success': True,
                'message': 'Không tìm thấy vé đặt nào cho người dùng này',
                'data': []
            }), 200

        return flask.jsonify({
            'success': True,
            'message': 'Lấy danh sách vé đặt thành công',
            'data': rows
        }), 200

    except pyodbc.Error as e:
        print(f"Lỗi khi lấy dữ liệu vé đặt: {str(e)}")
        return flask.jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500

# them phim
@app.route('/api/phim', methods=['POST'])
def them_phim():
    data = flask.request.get_json()
    ten_phim = data.get('ten')
    tac_gia = data.get('tacGia')
    mo_ta = data.get('moTa')
    thoi_luong = data.get('thoiLuong')
    anh = data.get('anh')
    trailer = data.get('trailer')

    if not ten_phim:
        return flask.jsonify({'success': False, 'message': 'Tên phim không được để trống'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO phim (ten_phim, mo_ta, thoi_luong, tac_gia, anh, trailer)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ten_phim, mo_ta, thoi_luong, tac_gia, anh, trailer))
        conn.commit()
        cursor.close()
        conn.close()
        return flask.jsonify({'success': True, 'message': 'Thêm phim thành công'}), 201
    except Exception as e:
        print("Lỗi thêm phim:", e)
        return flask.jsonify({'success': False, 'message': str(e)}), 500


# sua phim
@app.route('/api/phim/<int:phim_id>', methods=['PUT'])
def sua_phim(phim_id):
    data = flask.request.get_json()
    ten_phim = data.get('ten')
    mo_ta = data.get('moTa')
    thoi_luong = data.get('thoiLuong')
    tac_gia = data.get('tacGia')
    anh = data.get('anh')
    trailer = data.get('trailer')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE phim
            SET ten_phim = ?, mo_ta = ?, thoi_luong = ?, tac_gia = ?, anh = ?, trailer = ?
            WHERE phim_id = ?
        """, (ten_phim, mo_ta, thoi_luong, tac_gia, anh, trailer, phim_id))
        conn.commit()
        cursor.close()
        conn.close()
        return flask.jsonify({'success': True, 'message': 'Cập nhật phim thành công'}), 200
    except Exception as e:
        return flask.jsonify({'success': False, 'message': str(e)}), 500


#xoa phim
@app.route('/api/phim/<int:phim_id>', methods=['DELETE'])
def xoa_phim(phim_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM phim WHERE phim_id = ?", (phim_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return flask.jsonify({'success': True, 'message': 'Xóa phim thành công'}), 200
    except Exception as e:
        return flask.jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000)