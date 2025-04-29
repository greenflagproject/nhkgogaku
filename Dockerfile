FROM python:3.13.3

RUN apt-get update
RUN apt-get install -y locales \
	&& echo "ja_JP UTF-8" > /etc/locale.gen \
	&& locale-gen
	# && echo "export LANG=ja_JP.UTF-8" >> ~/.bashrc

RUN curl -O https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar -xJf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*/ffprobe /usr/local/bin/ && \
    rm -rf ffmpeg-*

ENV LAMBDA_TASK_ROOT=/var/task
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY nhkgogaku.py ${LAMBDA_TASK_ROOT}
# COPY ./lib/linuxarm64/* /usr/local/bin/

ENV LANG=ja_JP.UTF-8

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
ENTRYPOINT ["python3"]
CMD [ "nhkgogaku.py" ]
