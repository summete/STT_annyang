from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import requests
import os  # 환경 변수를 사용하기 위해 import
import logging  # 로깅 모듈 추가

app = Flask(__name__)
CORS(app)

# 데이터베이스 파일 생성 및 연결
conn = sqlite3.connect('translations.db', check_same_thread=False)
c = conn.cursor()

# 테이블 생성 (이미 존재하는 경우 생략)
c.execute('''
    CREATE TABLE IF NOT EXISTS translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_text TEXT,
        translated_text TEXT
    )
''')
conn.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text')

        if not text:
            raise ValueError("No text provided")

        # 네이버 파파고 API 요청
        url = 'https://openapi.naver.com/v1/papago/n2mt'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Naver-Client-Id': os.environ.get('NAVER_CLIENT_ID'),  # 환경 변수에서 ID 가져옴
            'X-Naver-Client-Secret': os.environ.get('NAVER_CLIENT_SECRET'),  # 환경 변수에서 Secret 가져옴
        }
        body = 'source=ko&target=en&text=' + text
        response = requests.post(url, headers=headers, data=body)

        if response.status_code != 200:
            raise Exception("Translation API request failed")

        translated_text = response.json().get('message', {}).get('result', {}).get('translatedText', "")
        return jsonify(status="success", translated_text=translated_text)

    except ValueError as e:
        return jsonify(status="failure", error=str(e)), 400
    except Exception as e:
        return jsonify(status="failure", error=str(e)), 500

@app.route('/save-results', methods=['POST'])
def save_results():
    try:
        data = request.json
        original_text = data.get('originalText')
        translated_text = data.get('translatedText')

        if not original_text or not translated_text:
            raise ValueError("Invalid data")

        # 데이터베이스에 저장
        c.execute('INSERT INTO translations (original_text, translated_text) VALUES (?, ?)', 
                  (original_text, translated_text))
        conn.commit()

        return jsonify(status="success", original_text=original_text, translated_text=translated_text)

    except ValueError as e:
        return jsonify(status="failure", error=str(e)), 400
    except Exception as e:
        return jsonify(status="failure", error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
