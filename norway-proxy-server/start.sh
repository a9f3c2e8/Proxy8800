#!/bin/sh

# Запускаем API сервер в фоне
python api_server.py &

# Запускаем MTProto сервер на переднем плане
python mtproto_server.py
