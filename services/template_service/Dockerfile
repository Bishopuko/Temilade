FROM php:8.1-cli

WORKDIR /app

# 1️ Install dependencies and sockets extension
RUN apt-get update && \
    apt-get install -y libzip-dev unzip && \
    docker-php-ext-install sockets && \
    rm -rf /var/lib/apt/lists/*

# 2️ Copy composer files
COPY composer.json composer.lock* ./

# 3️ Install Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# 4️ Install PHP dependencies (use ignore platform req as safety fallback)
RUN composer install --no-dev --optimize-autoloader --ignore-platform-req=ext-sockets

# 5️ Copy application source
COPY . .

EXPOSE 8081

CMD ["php", "-S", "0.0.0.0:8081", "-t", "public"]
