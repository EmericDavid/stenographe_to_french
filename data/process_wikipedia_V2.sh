#!/bin/bash
cd /home/nas-wks01/users/uapv2502538/wikipedia

mkdir -p logs
mkdir -p data/wikipedia_dump
mkdir -p data/wikipedia_output

URLS=(
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles1.xml-p1p306134.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles2.xml-p306135p1050822.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p1050823p2550822.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles3.xml-p2550823p2977214.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles4.xml-p2977215p4477214.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles4.xml-p4477215p5202073.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p5202074p6702073.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p6702074p8202073.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles5.xml-p8202074p9074283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p9074284p10574283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p10574284p12074283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p12074284p13574283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p13574284p15074283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p15074284p16574283.bz2"
    "https://mirror.accum.se/mirror/wikimedia.org/dumps/frwiki/20250301/frwiki-20250301-pages-articles6.xml-p16574284p16733183.bz2"
)

for i in "${!URLS[@]}"; do
    URL=${URLS[$i]}

    echo "Processing URL: $URL"

    sbatch process_single_url.sh $URL
    sleep 1
done