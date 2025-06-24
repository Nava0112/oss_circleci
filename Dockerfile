FROM python:3.11

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV ORACLE_HOME=/opt/oracle/instantclient

# Install OS-level dependencies
RUN apt-get update && \
    apt-get install -y libaio1 unzip curl && \
    mkdir -p /opt/oracle && \
    curl -L -o instantclient.zip https://download.oracle.com/otn_software/linux/instantclient/2380000/instantclient-basic-linux.x64-23.8.0.25.04.zip && \
    unzip instantclient.zip -d /opt/oracle && \
    rm instantclient.zip && \
    ln -s /opt/oracle/instantclient_23_8 /opt/oracle/instantclient && \
    ln -sf /opt/oracle/instantclient/libclntsh.so.23.1 /opt/oracle/instantclient/libclntsh.so && \
    ln -sf /opt/oracle/instantclient/libocci.so.23.1 /opt/oracle/instantclient/libocci.so   

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install pytest
RUN apt-get update && apt-get install -y gcc python3-dev build-essential

# Copy app code
COPY . /app
WORKDIR /app

EXPOSE 5000

CMD ["python", "oss.py"]
