## docker build -t stunnel-image .
FROM alpine:latest
RUN set -x \
 && addgroup -S stunnel \
 && adduser -S -G stunnel stunnel \
 && apk add --update --no-cache \
        ca-certificates \
        libintl \
        openssl \
        stunnel

RUN mkdir -p /etc/stunnel \
 && chown -R stunnel:stunnel /etc/stunnel

USER stunnel
EXPOSE 443
CMD ["stunnel"]