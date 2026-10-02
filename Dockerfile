FROM python:3.11-slim

RUN apt-get update && apt-get install -y git curl unzip && rm -rf /var/lib/apt/lists/*

# I-install ang Luau
RUN curl -L https://github.com/luau-lang/luau/releases/latest/download/luau-ubuntu.zip -o luau.zip \
    && unzip luau.zip -d /usr/local/bin \
    && rm luau.zip

# I-clone ang deobfuscator
RUN git clone https://github.com/KryptIT/luraph-v15-v14.x-deobfuscator.git /app/deob

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "bot.py"]
