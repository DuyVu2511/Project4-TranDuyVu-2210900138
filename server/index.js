const express = require("express");
const cors = require("cors");
const app = express();

app.use(cors());
app.use(express.json());

// Import route
const nguoiDungRouter = require("./routes/nguoidung");
app.use("/api/nguoidung", nguoiDungRouter);

// Khởi động server
const PORT = 3001;
app.listen(PORT, () => {
  console.log(`🚀 Server backend chạy tại http://localhost:${PORT}`);
});
