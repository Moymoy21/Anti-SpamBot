FROM python:3.11-slim

RUN apt-get update && apt-get install -y git curl unzip && rm -rf /var/lib/apt/lists/*

# I-install ang Luau (kasama na ang luau-ast, luau-analyze, atbp.)
RUN curl -L https://github.com/luau-lang/luau/releases/latest/download/luau-ubuntu.zip -o luau.zip \
    && unzip luau.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/* \
    && rm luau.zip

# I-clone ang KryptIT deobfuscator
RUN git clone https://github.com/KryptIT/luraph-v15-v14.x-deobfuscator.git /app/deob

# ITO ANG BAGONG DAGDAG: Gumawa ng bin folder at i-symlink ang Luau binaries
RUN mkdir -p /app/deob/Deobfuscator/deobf/bin && \
    ln -sf /usr/local/bin/luau /app/deob/Deobfuscator/deobf/bin/luau && \
    ln -sf /usr/local/bin/luau-ast /app/deob/Deobfuscator/deobf/bin/luau-ast && \
    ln -sf /usr/local/bin/luau-analyze /app/deob/Deobfuscator/deobf/bin/luau-analyze && \
    ln -sf /usr/local/bin/luau-compile /app/deob/Deobfuscator/deobf/bin/luau-compile

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "bot.py"]
