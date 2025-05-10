const sql = require("mssql");

const config = {
  user: "sa", // hoặc tài khoản bạn dùng để đăng nhập SQL Server
  password: "123456", // thay bằng mật khẩu thực tế
  server: "TDV-LAPTOP\\DUYVU", // lưu ý dùng \\ để escape ký tự \
  database: "VeXemPhim",
  options: {
    encrypt: false, // nếu dùng Azure thì để true
    trustServerCertificate: true, // với local cần có dòng này
  },
};

const poolPromise = new sql.ConnectionPool(config)
  .connect()
  .then((pool) => {
    console.log("✅ Kết nối MSSQL thành công");
    return pool;
  })
  .catch((err) => console.error("❌ Lỗi kết nối MSSQL:", err));

module.exports = { sql, poolPromise };
