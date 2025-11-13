FROM php:8.3-cli

WORKDIR /app

# Install dependencies and PHP extensions
RUN apt-get update && \
    apt-get install -y \
        libzip-dev \
        unzip \
        libpq-dev \
        git \
        curl \
    && docker-php-ext-install \
        sockets \
        pdo \
        pdo_pgsql \
    && rm -rf /var/lib/apt/lists/*

# Install Composer globally
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Copy composer files first for layer caching
COPY lumen/composer.json lumen/composer.lock* ./

# Install PHP dependencies (ignore ext-sockets since it’s built-in now)
RUN pecl install redis && docker-php-ext-enable redis
RUN composer install --no-dev --optimize-autoloader

# Copy application source
COPY lumen/ .

# Expose the app port
EXPOSE 8081

# Start Lumen using PHP’s built-in server
CMD ["php", "-S", "0.0.0.0:8081", "-t", "public"]
