FROM python:3.12

EXPOSE 8000

ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

COPY requirements.txt /requirements.txt

RUN /root/.cargo/bin/uv pip install --system --no-cache -r requirements.txt

WORKDIR /app
COPY ./ /app

CMD ["python3", "api.py"]