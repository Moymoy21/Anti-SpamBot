FROM python:3.11-slim

RUN apt-get update && apt-get install -y git curl unzip wget file && rm -rf /var/lib/apt/lists/*

# I-install ang Luau WITH DIAGNOSTICS
RUN curl -L -o luau.zip https://github.com/luau-lang/luau/releases/download/0.607/luau-ubuntu.zip && \
    echo "=== FILE INFO ===" && \
    ls -la luau.zip && \
    file luau.zip && \
    echo "=== ZIP CONTENTS ===" && \
    unzip -l luau.zip && \
    echo "=== EXTRACTING ===" && \
    unzip -o luau.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/luau* && \
    echo "=== FINAL CHECK ===" && \
    ls -la /usr/local/bin/ && \
    rm luau.zip

# I-clone ang KryptIT deobfuscator
RUN git clone https://github.com/KryptIT/luraph-v15-v14.x-deobfuscator.git /app/deob

# I-symlink ang Luau binaries sa loob ng deobfuscator
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
