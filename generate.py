#!/usr/bin/env python

#################################################################
#
# summoning-51ckn355 - AI generated cards and sets for Cockatrice
# written by Benjamin Gleitzman (gleitz@mit.edu)
#
#################################################################

import argparse
import json
import random
import time
from urllib.parse import quote

from dotenv import dotenv_values
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from slugify import slugify

env_vars = dotenv_values('.env')

CARD_INFO_GENERATION_URL = 'https://backend-dot-valued-sight-253418.ew.r.appspot.com/api/v1/card'
CARD_ART_GENERATION_URL = 'https://backend-dot-valued-sight-253418.ew.r.appspot.com/api/v1/art'
CARD_ART_GENERATION_URL_WOMBO = "https://api.luan.tools/api/tasks/"
CARD_DISPLAY_URL = 'https://magic.glei.tz/urza'
WOMBO_API_KEY = env_vars['WOMBO_API_KEY']
WOMBO_HEADERS = {
    'Authorization': f'bearer {WOMBO_API_KEY}',
    'Content-Type': 'application/json'
}

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
    card_art_url = _generate_card_art_url_wombo(card)
    card_name = card['name']

    # card['url'] = f'https://corsproxy.io/?{quote(card_art_url)}'
    card['url'] = card_art_url
    card['filename'] = f'{slugify(card_name)}_{int(time.time())}.png'

    print("Finished card:")
    print(json.dumps(card, indent=4))
    _download_card(card)


def _download_card(card):
    url = f'{CARD_DISPLAY_URL}?encoded=1&card={quote(json.dumps(card))}'
    print("Printing card...")
    print(url)

    driver = _get_driver()
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
    print(response.url)
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


# https://wombo.gitbook.io/dream-docs/quick-start
def _generate_card_art_url_wombo(card):
    print("Fetching artwork")
    post_payload = json.dumps({
        "use_target_image": False
    })
    post_response = requests.request(
        "POST", CARD_ART_GENERATION_URL_WOMBO,
        headers=WOMBO_HEADERS, data=post_payload)

    task_id = post_response.json()['id']
    prompt = f'Generate an image for a Magic: the Gathering card with the following specification: {json.dumps(card)}'
    print(prompt)
    task_id_url = f"https://api.luan.tools/api/tasks/{task_id}"
    put_payload = json.dumps({
        "input_spec": {
            "style": random.randint(1, 21),
            "prompt": prompt,
            "target_image_weight": 0.1,
            "width": 1024,
            "height": 748
        }})
    requests.request("PUT", task_id_url, headers=WOMBO_HEADERS, data=put_payload)

    while True:
        response_json = requests.request(
            "GET", task_id_url, headers=WOMBO_HEADERS).json()

        state = response_json["state"]

        if state == "completed":
            r = requests.request("GET", response_json["result"])
            with open("image.jpg", "wb") as image_file:
                image_file.write(r.content)
            print("image saved successfully :)")
            break

        if state == "failed":
            print("generation failed :(")
            break
        time.sleep(3)

    return "image.jpg"


def _get_driver():
    options = Options()
    options.headless = True

    service = Service(executable_path='./chromedriver')
    driver = webdriver.Chrome(options=options, service=service)
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
