__author__ = 'yingbozhan'

from sw4.cordyceps.skyscanner.transport.query import TransportQuery
from werkzeug.datastructures import ImmutableMultiDict, Headers
from sw4.cordyceps.skyscanner.support import import_scraper_module
from pprint import pprint
import urllib2
import os
import json
import argparse


def get_airport_id(location):
    url = 'http://www.opstest.skyscanner.local/dataservices/geo/v1.1/concordance/iata/routenodeid/'+location
    response = urllib2.urlopen(url)
    json_response = json.loads(response.read())
    for answer in json_response:
        if answer['Type'] == 'Airport':
            return answer['OutputCode']

def form_legs(legs):
    segs = legs.replace(' ','').split(',')
    known_aiport_dict = {}
    leg_num = len(segs)
    error = False
    leg_str = ''
    for seg in segs:
        [from_place, to_place, selected_time] = seg.split('.')
        try:
            if from_place not in known_aiport_dict:
                known_aiport_dict[from_place] = get_airport_id(from_place)
            if to_place not in known_aiport_dict:
                known_aiport_dict[to_place] = get_airport_id(to_place)
            leg_str += known_aiport_dict[from_place]+'.'+known_aiport_dict[to_place]+'.'+selected_time+','
        except:
            pprint('Not Able to Obtain Airport ID for ' + from_place+','+to_place)
            error = True
            break
    return leg_num, leg_str[:-1:], error



def main(**kwargs):
    website_id = kwargs.get('website_id', None)
    legs = kwargs.get('legs', None)
    ccy = kwargs.get('ccy', 'SGD')
    ucy = kwargs.get('ucy', 'SG')
    locale = kwargs.get('locale', 'en-GB')
    adult = kwargs.get('adults', '1')
    child = kwargs.get('child', '0')
    infant = kwargs.get('infant', '0')
    cabin = kwargs.get('cabin', 'economy')
    model = kwargs.get('mode', 'return')

    if legs is None or website_id is None:
        pprint("No Website/Leg information Found")
        return

    leg_num, legs_str, error = form_legs(legs)
    if error:return

    os.environ["SCRAPERSERVICE"] = "jacquard"
    query_dict = {'user_currency': ccy, 'task': 'transport', 'website_id': website_id,
                  'user_locale': locale, 'version': '4.0', 'user_market': ucy,
                  'leg_count': str(leg_num), 'legs': legs_str}
    query_options = ImmutableMultiDict([('debug', 'true'),
                                        ('passengers', str(adult)+','+str(child)+','+str(infant)),
                                        ('cabin_class', cabin), ('proxy', 'http://localhost:8888'),
                                        ('pricing_model', model)])
    query_headers = Headers([('Content-Length', ''),
                             ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.99 Safari/537.36'),
                             ('Connection', 'keep-alive'),
                             ('Host', 'localhost:1731'),
                             ('Upgrade-Insecure-Requests', '1'),
                             ('Cache-Control', 'max-age=0'),
                             ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'),
                             ('Accept-Language', 'en-US,en;q=0.8'),
                             ('Content-Type', ''),
                             ('Accept-Encoding', 'gzip, deflate, sdch')])

    query_builders = {
        ('transport', '4.0'): TransportQuery,
    }

    query_builder = query_builders[(query_dict['task'], query_dict['version'])]
    query = query_builder(query_dict, query_options, query_headers)
    module = import_scraper_module(query.task, query.website_id, False)
    answer = module.register.run_scraper(query)
    pprint(json.loads(answer.serialise('json')))


if __name__ == "__main__":
    pprint('sample message (website_id and legs are mandatory')
    pprint('python cmd_jacquard.py -w=silk -l=SIN.RGN.2015-10-02,RGN.SIN.2015-10-08 --ccy=SGD --ucy=SG --locale=en-GB '
           '--adult=1 --child=0 --infant=0 --cabin=economy --model=return')
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-w','--website_id', help='website id', required=True)
    parser.add_argument('-l','--legs', help='searching legs(support md), i.e. SIN.RGN.2015-10-02,RGN.SIN.2015-10-08 ', required=True)
    parser.add_argument('-ucy','--ucy', help='market, default to be SG', required=False)
    parser.add_argument('-ccy','--ccy', help='currency, default to be SGD', required=False)
    parser.add_argument('-locale','--locale', help='locale, default to be en-GB', required=False)
    parser.add_argument('-model','--model', help='pricing model, default to be return', required=False)
    parser.add_argument('-cabin','--cabin', help='cabin, default to be economy', required=False)
    parser.add_argument('-adult','--adult', help='adult, default to be 1', required=False)
    parser.add_argument('-child','--child', help='child, default to be 0', required=False)
    parser.add_argument('-infant','--infant', help='infant, default to 0', required=False)


    args = vars(parser.parse_args())
    main(**args)