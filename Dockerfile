FROM ubuntu

RUN apt-get update -y && \
    apt-get install -y python2.7

WORKDIR \

COPY . /

ENTRYPOINT [ "sh" ]

CMD [ "./runtests"]
