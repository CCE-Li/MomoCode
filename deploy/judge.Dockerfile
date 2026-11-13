FROM alpine:3.20

RUN apk add --no-cache g++ libstdc++ \
    && adduser -D -u 10001 judge

USER judge
WORKDIR /workspace
