FROM python:3.11-slim

RUN apt-get update && apt-get install -y git curl unzip wget && rm -rf /var/lib/apt/lists/*

# I-install ang Luau (gumamit ng specific version para sure)
RUN wget https://github.com/luau-lang/luau/releases/download/0.607/luau-ubuntu.zip -O luau.zip \
    && unzip -j luau.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/luau* \
    && rm luau.zip \
    && ls -la /usr/local/bin/

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
