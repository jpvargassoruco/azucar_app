FROM nginx:1.25-alpine

# Copy static frontend assets into standard serving directory
COPY . /usr/share/nginx/html

# Replace default Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
