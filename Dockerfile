FROM ubuntu:20.04
MAINTAINER Eden Attenborough "gae19jtu@uea.ac.uk"
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update -y
RUN apt-get install -y python3-pip 
COPY . /app
RUN touch /.docker && touch /app/.docker
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["src/app.py", "--production"]
