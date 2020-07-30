FROM nginx

# Make /var/cache/nginx/ writable by non-root users
RUN chgrp nginx /var/cache/nginx/
RUN chmod g+w /var/cache/nginx/

EXPOSE 8081

# Write the PID file to a location where regular users have write access. Not Standards compliant.
RUN sed -i.bak -e 's%^pid /var/run/nginx.pid;%pid /var/tmp/nginx.pid;%' /etc/nginx/nginx.conf

COPY ./nginx.conf /etc/nginx/conf.d/default.conf 