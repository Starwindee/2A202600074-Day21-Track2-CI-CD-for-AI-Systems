# Báo Cáo Ngắn - Lab CI/CD cho AI Systems

## 1) Cấu hình mô hình đã chọn và lý do

- Mô hình đã chọn: `RandomForestClassifier`
- Tham số trong `params.yaml`:
  - `n_estimators: 250`
  - `max_depth: 20`
  - `min_samples_split: 2`

Lý do chọn:

- Đây là cấu hình cho kết quả tốt và ổn định trong các lần thử nghiệm ở Bước 1.
- Cấu hình đơn giản, dễ tái lập, phù hợp để đưa vào pipeline CI/CD của lab.

## 2) Tóm tắt kết quả

- Bước 1: Đã chạy nhiều lần train và theo dõi trên MLflow.
- Bước 2: Pipeline CI/CD chạy theo thứ tự `Test -> Train -> Eval -> Deploy`.
- Bước 3: Sau khi cập nhật dữ liệu mới và đẩy DVC pointer, pipeline tự động chạy lại.

## 3) Khó khăn gặp phải và cách xử lý

1. Fail ở bước Eval (accuracy < 0.70)

- Vấn đề: Ở dữ liệu ban đầu, job `Eval` bị chặn do `accuracy` chưa đạt ngưỡng `0.70`.
- Cách xử lý:
  - Chạy `python add_new_data.py` để bổ sung dữ liệu huấn luyện.
  - Chạy `dvc add data/train_phase1.csv` để cập nhật pointer dữ liệu.
  - `dvc push` trước, sau đó `git push` để kích hoạt pipeline.
- Kết quả: với dữ liệu mới, accuracy tăng và vượt ngưỡng (`~0.74`), pipeline qua được Eval và tiếp tục Deploy.

2. Không thể tạo service account key (Org Policy)

- Vấn đề: Project bị policy chặn tạo key (`iam.disableServiceAccountKeyCreation`), không thể dùng cách xác thực JSON key truyền thống.
- Cách xử lý: Chuyển sang xác thực không dùng key bằng Workload Identity Federation (WIF) cho GitHub Actions.

3. Lỗi `dvc pull` trong CI

- Vấn đề: Có thời điểm pipeline vẫn chạy workflow cũ hoặc cấu hình xác thực chưa đồng nhất khiến `dvc pull` lỗi khi truy cập GCS.
- Cách xử lý:
  - Làm sạch workflow (bỏ các dòng `credentialpath`/`sa-key.json` cũ).
  - Chuẩn hóa xác thực WIF và kiểm tra lại secrets.
  - Cập nhật lại dữ liệu DVC pointer + cache trên bucket.

4. Deploy fail do SSH

- Vấn đề: Secret SSH ban đầu cấu hình chưa đúng (nhầm public/private key, user/key chưa khớp).
- Cách xử lý:
  - Tạo key deploy riêng.
  - Đưa public key vào `authorized_keys` trên VM.
  - Cập nhật chính xác `VM_HOST`, `VM_USER`, `VM_SSH_KEY` trong GitHub Secrets.

5. Service trên VM không khởi động ổn định

- Vấn đề:
  - Thiếu package Python (`fastapi`, `uvicorn`, ...).
  - Thiếu quyền đọc model từ GCS (`storage.objects.get` bị 403).
  - Service trỏ sai đường dẫn file `serve.py` hoặc môi trường Python.
- Cách xử lý:
  - Tạo virtual environment riêng trên VM và cài dependencies.
  - Sửa file systemd service (`ExecStart`) về đúng đường dẫn.
  - Cấp quyền `Storage Object Viewer` cho compute service account của VM trên bucket.
  - Restart service và kiểm tra lại endpoint `/health`.

## 4) Ghi chú nộp bài

Các bằng chứng đã/nên đính kèm trong thư mục screenshot:

- MLflow UI có ít nhất 3 runs.
- GitHub Actions với các jobs xanh (Bước 2 và Bước 3).
- Kết quả `curl /health` và `curl /predict` trên VM.
- Cloud Storage thể hiện dữ liệu DVC và model `models/latest/model.pkl`.
