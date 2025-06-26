# 安裝後端

## 建立 venv 虛擬環境

- 到官網下載 Python 3.12 版本
- 建立 python 3.12 虛擬環境

  ```
  py -3.12 -m venv traffic_env
  ```

## 啟動環境

- 到 traffic_env\Scripts 目錄下，執行 activate

  ```
  .\traffic_env\Scripts\activate
  ```

- 確定進入虛擬環境 (traffic_env)

  ```
  (traffic_env) D:\01.Project\traffic\traffic_project\backend\traffic_env\traffic>
  ```

- 升級 pip

  ```
  python -m pip install --upgrade pip
  ```

## 安裝套件

- 回到 traffic_env\traffic\ 目錄底下
- 執行以下指令安裝套件

  ```
  pip install -r requirements.txt
  ```

## 備份套件

- 回到 traffic_env\traffic\ 目錄底下

  ```
  pip freeze > requirements.txt
  ```

- 產生 requirements.txt 套件清單，該檔案會與 manage.py 同目錄

## 保留專案

- 保留 traffic 專案整個目錄即可

## 離開虛擬環境

- 到 traffic_env\Scripts 目錄下，執行 deactivate

  ```
  .\traffic_env\Scripts\deactivate
  ```

---

# 套件列表

- django
- djangorestframework
- django-cors-headers
- django-environ
- djangorestframework-simplejwt
- django-filter
- django-extensions
- django-debug-toolbar
- mysqlclient
- numpy
- pandas
- joblib
- stensorflow
- scikit-learn
