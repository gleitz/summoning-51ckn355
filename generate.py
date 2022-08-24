#!/usr/bin/env python

#################################################################
#
# summoning-51ckn355 - AI generated cards and sets for Cockatrice
# written by Benjamin Gleitzman (gleitz@mit.edu)
#
#################################################################

import argparse
import json
import time
from urllib.parse import quote

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from slugify import slugify

CARD_INFO_GENERATION_URL = 'https://backend-dot-valued-sight-253418.ew.r.appspot.com/api/v1/card'
CARD_ART_GENERATION_URL = 'https://backend-dot-valued-sight-253418.ew.r.appspot.com/api/v1/art'
CARD_DISPLAY_URL = 'https://adventuresofyou.online/urza'

# pylint: disable=anomalous-backslash-in-string
DOWNLOAD_BOOKMARKLET = '''(function() {
  if(window.html2canvas)
    return run();
  var script = document.createElement('script');
  script.onload = run;
  script.src = 'https://github.com/niklasvh/html2canvas/releases/download/v1.0.0-alpha.1/html2canvas.min.js';
  document.querySelector('head').appendChild(script);
  function run() {
    this && this.parentNode && this.parentNode.removeChild(this);
    html2canvas(document.getElementById('card'), {
        backgroundColor: null,
        allowTaint: true,
        useCORS: true,
        logging: true
    }).then(function(canvas) {
      return new Promise(function(fufill) { canvas.toBlob(fufill); });
    }).then(function(blob) {
      var link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = "%s";
      link.click();
      return new Promise(function(fufill) { setTimeout(10, fufill, link); });
    }).then(function(link) {
      if(link.href.indexOf('blob:') === 0) {
        URL.revokeObjectURL(link.href);
        link.href = '###';
      }
    }).catch(function(error) {
      console.error(error);
      error.message && alert('Failed to capture:' + error.message);
    });
  }
})();'''  # noqa: W605


def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args())

    main(args['name'], args['cost'])


def main(name, mana_cost):
    card = _generate_card(name, mana_cost)
    card_art_url = _generate_card_art_url(card)
    card_name = card['name']

    card['url'] = f'https://corsproxy.io/?{quote(card_art_url)}'
    card['filename'] = f'{slugify(card_name)}_{int(time.time())}.png'

    print("Finished card:")
    print(json.dumps(card, indent=4))
    _download_card(card)


def _download_card(card):
    driver = _get_driver()

    url = f'{CARD_DISPLAY_URL}?encoded=1&card={quote(json.dumps(card))}'
    print("Printing card...")
    print(url)

    driver.get(url)
    time.sleep(5)
    driver.execute_script(DOWNLOAD_BOOKMARKLET % card['filename'])
    time.sleep(10)

    driver.close()


def _generate_card(name, mana_cost):
    card = {
        "deck_name": "",
        "name": name or "",
        "manaCost": mana_cost or "",
        "types": "",
        "subtypes": "",
        "text": "",
        "power": "",
        "toughness": "",
        "flavorText": "",
        "rarity": "",
        "loyalty": "",
        "url": "",
        "basic_land": "",
        "cardId": ""
    }

    print("Inventing card")
    response = requests.request("GET",
                                CARD_INFO_GENERATION_URL,
                                params={"presets": json.dumps(card),
                                        "deckBuilder": "false",
                                        "temperature": "1"})
    return response.json()


def _generate_card_art_url(card):
    print("Fetching artwork")
    response = requests.request("GET",
                                CARD_ART_GENERATION_URL,
                                params={"card": json.dumps(card)})

    wombo_task_id = response.json()['wombo_task_id']
    time.sleep(10)

    state = "incomplete"
    while state != "completed":
        response = requests.request("GET",
                                    f'{CARD_ART_GENERATION_URL}/latest',
                                    params={"wombo_task_id": wombo_task_id})
        state = response.json()['state']
        if state != "completed":
            print("Still waiting...")
            time.sleep(5)

    return response.json()['art_url']


def _get_driver():
    options = Options()
    options.headless = True

    driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
    return driver


def get_parser():
    parser = argparse.ArgumentParser(description='MTG Card Generator')
    parser.add_argument('-c',
                        '--cost',
                        nargs='?',
                        default=None,
                        type=str,
                        help='The cost of your card')
    parser.add_argument('-n',
                        '--name',
                        nargs='?',
                        default=None,
                        type=str,
                        help='The name of your card')
    return parser


if __name__ == '__main__':
    command_line_runner()
