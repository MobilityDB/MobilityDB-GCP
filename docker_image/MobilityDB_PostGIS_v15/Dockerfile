#This Dockerfile use mobilityDB develop version
FROM postgis/postgis:15-3.3
# Configuration Parameters
LABEL maintainer="MobilityDB Project - https://github.com/MobilityDB/MobilityDB"
ENV MOBILITYDB_VERSION 1.0
ENV POSTGRES_DB=mobilitydb
ENV POSTGRES_USER=docker 
ENV POSTGRES_PASSWORD=docker

ENV PGROUTING_GIT_HASH 113aa3b60f60db20ecc00e28b2ef4ae7d5e76219

# Fix the Release file expired problem
RUN echo "Acquire::Check-Valid-Until \"false\";\nAcquire::Check-Date \"false\";" | cat > /etc/apt/apt.conf.d/10no--check-valid-until


# Install Prerequisites MobilityDB
RUN apt-get update \
 && apt-get install -y \
    build-essential \
    cmake \
    git \
    libproj-dev \    
    g++ \
    wget \
    autoconf \
    autotools-dev \
    libgeos-dev \
    libpq-dev \
    libproj-dev \
    libjson-c-dev \
    protobuf-c-compiler \
    xsltproc \
    libgsl-dev \
    libgslcblas0 \    
    postgresql-server-dev-${PG_MAJOR} \
  && rm -rf /var/lib/apt/lists/* 

# Install MobilityDB
RUN git clone https://github.com/MobilityDB/MobilityDB.git -b develop /usr/local/src/MobilityDB
RUN mkdir /usr/local/src/MobilityDB/build
RUN cd /usr/local/src/MobilityDB/build && \
    cmake .. && \
    make -j$(nproc) && \
    make install


# Install Prerequisites PgRouting
RUN apt update \
 && apt install -y \
        libboost-atomic1.74.0 \
        libboost-chrono1.74.0 \
        libboost-graph1.74.0 \
        libboost-date-time1.74.0 \
        libboost-program-options1.74.0 \
        libboost-system1.74.0 \
        libboost-thread1.74.0 \
 && apt install -y \
        libboost-graph-dev \
        libpq-dev \
 && mkdir -p /usr/src/pgrouting \
 && cd /usr/src/pgrouting \
 && git init \
 && git remote add origin https://github.com/pgRouting/pgrouting.git \
 && git fetch --depth 1 origin :${PGROUTING_GIT_HASH} \
 && git reset --hard FETCH_HEAD \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make \
 && make install \
 && cd / \
 && rm -rf /usr/src/pgrouting 


RUN rm /docker-entrypoint-initdb.d/10_postgis.sh
COPY ./initdb-mobilitydb.sh /docker-entrypoint-initdb.d/mobilitydb.sh
#RUN chmod +x /docker-entrypoint-initdb.d/mobilitydb.sh