FROM python:3.11-slim

# I-install ang lahat ng kailangan (kasama na ang build tools)
RUN apt-get update && apt-get install -y \
    git curl unzip wget file \
    build-essential cmake g++ make \
    && rm -rf /var/lib/apt/lists/*

# I-BUILD ANG LUAU MULA SA SOURCE
RUN git clone --depth 1 https://github.com/luau-lang/luau.git /tmp/luau && \
    cd /tmp/luau && \
    cmake -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build --target Luau.Repl.CLI -j$(nproc) && \
    cmake --build build --target Luau.Analyze -j$(nproc) && \
    cp build/Luau.Repl.CLI /usr/local/bin/luau && \
    cp build/Luau.Analyze /usr/local/bin/luau-analyze && \
    cp build/Luau.Repl.CLI /usr/local/bin/luau-ast && \
    cp build/Luau.Repl.CLI /usr/local/bin/luau-compile && \
    chmod +x /usr/local/bin/luau* && \
    echo "=== LUAU BUILT SUCCESSFULLY ===" && \
    ls -la /usr/local/bin/ && \
    rm -rf /tmp/luau

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
