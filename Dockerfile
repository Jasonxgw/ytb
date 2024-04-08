FROM registry.cn-hangzhou.aliyuncs.com/data-ecs/inverst:v0.1
RUN sed -i s@/deb.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list \
    && sed -i s@/security.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list \
    && sed -i s@stable/updates@stable-security@g /etc/apt/sources.list
RUN sed -i s@/deb.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN sed -i s@/security.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN apt-get update && apt-get install -y python3 python3-pip curl unzip libgconf-2-4 build-essential wget
RUN pip install --upgrade pip
ENV TZ Asia/Shanghai
#RUN apt-get update
#RUN apt-get install -y ffmpeg --fix-missing
#RUN apt-get install -y  vim
#RUN apt-get install -y --no-install-recommends unrar
#RUN apt-get install -y --no-install-recommends tzdata  && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ADD . .
ENV PYTHONPATH "${PYTHONPATH}:/app"
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 下载edge deb
#RUN wget https://packages.microsoft.com/repos/edge/pool/main/m/microsoft-edge-stable/microsoft-edge-stable_123.0.2420.81-1_amd64.deb
#RUN dpkg -i microsoft-edge-stable_123.0.2420.81-1_amd64.deb
CMD /usr/local/bin/python main.py