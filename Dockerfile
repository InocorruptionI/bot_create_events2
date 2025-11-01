FROM ubuntu:latest
LABEL authors="konstantinkuzmin"

ENTRYPOINT ["top", "-b"]