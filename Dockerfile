FROM python:3.9

COPY . /app
WORKDIR /app

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

ENTRYPOINT [ "python", "main.py" ]