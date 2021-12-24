FROM python:3

WORKDIR /app

COPY requirements.txt /app
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
	--no-cache-dir -U \
	-r requirements.txt

COPY . /app

ENTRYPOINT [ "python", "main.py" ]
