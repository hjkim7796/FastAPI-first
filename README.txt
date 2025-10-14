[Linux의 경우]
🌈모듈파일 수정
$> vi requirements.txt
...
pywin32 모듈을 삭제후 저장
...

🌈virtual 환경 구성
반드시 python 3.12 이상 사용
$> /usr/bin/python3.12 -m venv .venv
$> source .venv/bin/activate

🌈python 버젼 확인
((.venv) ) $> python --version
Python 3.12.11
((.venv) ) $> pip --version
pip 23.2.1 from /.../.venv/lib64/python3.12/site-packages/pip (python 3.12)

🌈module 설치
((.venv) ) $> pip install -r requirements.txt

🌈DB 설정 - mysql설치 필수
db name: <your db>
db username: <db username>
db password: <db password>
그후,
database.py 파일 열고 
...
DATABASE_URL = "mysql+pymysql://<username>:<password>@localhost:3306/<your db>"
수정후 저정

🌈실행
((.venv) ) $> uvicorn main:app --host 127.0.0.1 --port 8000

만약 nginx와 함께 실행할 경우 --root-path /ai 추가후, nginx에서 /ai 구성
((.venv) ) $> uvicorn main:app --host 127.0.0.1 --port 8000 --root-path /ai


만약 web으로 접속후 아래와 같이 에러가 발생하면,
1. claude_agent_sdk._errors.CLINotFoundError: Claude Code not found. Install with:
  npm install -g @anthropic-ai/claude-code

    ((.venv) ) $> sudo npm install -g @anthropic-ai/claude-code
2. api key error 가 발생하면
    .env파일을 열고 ANTHROPIC_API_KEY 값을 입력

