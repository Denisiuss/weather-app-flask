# Build Stage
FROM python:3.9-alpine as build

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /weather_app

COPY requirements.txt .

RUN apk add --no-cache build-base \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del build-base

# Runtime Stage
FROM python:3.9-alpine as runtime

# Create a non-root user
RUN addgroup -S weather_group && adduser -S weather_user -G weather_group

WORKDIR /weather_app

# Copy application files
COPY --from=build /usr/local/lib/python3.9 /usr/local/lib/python3.9
COPY --from=build /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY . .

# Change ownership of the application directory to the non-root user
RUN chown -R weather_user /weather_app

USER weather_user

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
