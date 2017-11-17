#!/usr/bin/env bash

echo ""
echo "1. RUNNING CRAWLER >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
./takehome_crawler.py


echo ""
echo "2. RUNNING SCRAPER >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
./takehome_souschef.py


echo ""
echo "3. RUNNING LINECOOK CHEF >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
rm -rf content/*
mv CrawlerDemo_TakeHomeTest.zip content/
cd content
unzip -q CrawlerDemo_TakeHomeTest.zip
cd ..
./takehome_sushichef.py -v --reset --channeldir='./content/CrawlerDemo_TakeHomeTest' --token=".token"

