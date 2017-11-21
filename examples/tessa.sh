#!/usr/bin/env bash

echo ""
echo "1. RUNNING TESSA Swahili >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
./tessa_cralwer.py  --lang=sw

echo ""
echo "2. RUNNING TESSA Arabic >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
./tessa_cralwer.py  --lang=ar

echo ""
echo "3. RUNNING TESSA Francais >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
./tessa_cralwer.py  --lang=fr

echo ""
echo "4. RUNNING TESSA English >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
./tessa_cralwer.py  --lang=en

