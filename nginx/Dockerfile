FROM nginx

# RUN mkdir -p /home/HH
# RUN useradd HH
# ENV HOME=/home/HH
# ENV APP_HOME=/home/HH/web
# RUN mkdir $APP_HOME
# WORKDIR $APP_HOME
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d