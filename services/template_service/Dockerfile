FROM php:8.3-cli


WORKDIR /app

# 1️ Install dependencies and sockets extension
RUN apt-get update && \
    apt-get install -y libzip-dev unzip libpq-dev && \
    docker-php-ext-install sockets pdo pdo_pgsql && \
    rm -rf /var/lib/apt/lists/*

# 2️ Copy composer files from lumen
COPY lumen/composer.json lumen/composer.lock* ./

# 3️ Install Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# 4️ Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader --ignore-platform-req=ext-sockets
RUN docker-php-ext-install pdo pdo_pgsql

# 5️ Copy application source from lumen
COPY lumen/ .

EXPOSE 8081

CMD ["php", "-S", "0.0.0.0:8081", "-t", "public"]
