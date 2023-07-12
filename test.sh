#!/bin/bash

sanity=$(curl "http://localhost:8000/ping" -s)
echo "sanity check: ${sanity}"
if [ "$sanity" != "Pong" ]
then
  echo "sanity check failed"
  exit 1
fi