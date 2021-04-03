#################################
##### Name: Hang Song
##### Uniqname: hangsong
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

BASE_URL = "https://www.nps.gov"
CACHE_FILENAME = "national_parks_cache.json"
CACHE_DICT = {}
MAP_URL = "http://www.mapquestapi.com/search/v2/radius"

consumer_key = secrets.CONSUMER_KEY
consumer_secret = secrets.CONSUMER_SECRET


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
    
    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

def make_request_with_cache(url):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    Parameters
    ----------
    url: string

    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    CACHE_DICT = open_cache()

    if (url in CACHE_DICT.keys()):
        print("Using Cache")
        return CACHE_DICT[url]
    else:
        print("Fetching")
        response = requests.get(url)
        CACHE_DICT[url] = response.text
        save_cache(CACHE_DICT)
        return CACHE_DICT[url]

def map_make_request_with_cache(url):
    CACHE_DICT = open_cache()

    if (url in CACHE_DICT.keys()):
        print("Using Cache")
        return CACHE_DICT[url]
    else:
        print("Fetching")
        response = requests.get(url)
        CACHE_DICT[url] = response.json()
        save_cache(CACHE_DICT)
        return CACHE_DICT[url]


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    main_url = "https://www.nps.gov/index.htm"
    url_text = make_request_with_cache(main_url)
    soup = BeautifulSoup(url_text, 'html.parser')
 
    state_list_parent = soup.find('div',class_ = 'SearchBar-keywordSearch input-group input-group-lg')
    state_list = state_list_parent.find_all('li')
    state_url_dict = {}

    for state_info in state_list:
        state_tag = state_info.find('a')
        state_detail_path = state_tag['href']
        state_detail_url = BASE_URL+state_detail_path
        state_url_dict[state_tag.string.lower()] = state_detail_url
    
    return state_url_dict
  


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    url_text = make_request_with_cache(site_url)
    soup = BeautifulSoup(url_text, 'html.parser')
 
    site_head_parent = soup.find('div',class_ = "Hero-titleContainer clearfix")
    site_name = site_head_parent.find('a').text
    site_category = site_head_parent.find('div',class_="Hero-designationContainer").find('span',class_="Hero-designation").text

    #check if address exists - Yosemite for example
    site_address_parent = soup.find('p',class_='adr')
    site_locality = None
    site_region = None
    site_zipcode = None
    site_address = None

    if site_address_parent is not None:
        site_locality = soup.find("span",itemprop = "addressLocality").text
        site_region = soup.find("span",itemprop = "addressRegion").text
        site_zipcode = soup.find("span",itemprop = "postalCode").text.strip()
        site_address = site_locality + ", " + site_region
    else:
        site_zipcode = 'No zipcode'
        site_address = 'No address'

    site_phone = soup.find("span",itemprop ="telephone").text.strip()

    national_site = NationalSite(category = site_category, name = site_name, address = site_address, zipcode= site_zipcode, phone = site_phone)

    return national_site


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    Returns
    -------
    list
        a list of national site instances
    '''
    url_text = make_request_with_cache(state_url)
    soup = BeautifulSoup(url_text, 'html.parser')

    park_instance_list = []

    park_info_parent = soup.find(id="list_parks")
    park_info = park_info_parent.find_all('h3')

    for park in park_info:
        park_ref = park.find('a')['href']
        park_url = BASE_URL+park_ref+'index.htm'
        parkinstance = get_site_instance(park_url)
        park_instance_list.append(parkinstance)

    return park_instance_list

def construct_unique_key(baseurl,params):
    param_strings = []
    connector = '&'
    for k in params.keys():
        param_strings.append(f'{k}={params[k]}')
    param_strings.sort()
    unique_key = baseurl + '?' +  connector.join(param_strings)
    return unique_key


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    origin = site_object.zipcode
    params = {'origin':origin,'radius':10,'maxMatches':10,'ambiguities':'ignore','outFormat':'json','key':consumer_key}
    map_api_key = construct_unique_key(MAP_URL,params)
    response_dict = map_make_request_with_cache(map_api_key)

    return response_dict

def print_nearby_places(map_api_dict):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    None
    '''
    results_list = map_api_dict['searchResults']
    for result in results_list:
        place_name = result['name']
        place_category = result['fields']['group_sic_code_name']
        place_address = result['fields']['address']
        place_city = result['fields']['city']
        if len(place_category) == 0:
            place_category = 'no category'
        if len(place_address) == 0:
            place_address = 'no address'
        if len(place_city) == 0:
            place_city = 'no city'
        print(f"- {place_name} ({place_category}): {place_address}, {place_city}")



if __name__ == "__main__":
    np_url_dict = build_state_url_dict()
    # print(np_url_dict)

    # np = get_site_instance("https://www.nps.gov/frst/index.htm")

    
    while True:
        state = input("Enter a state name (e.g. Michigan, michigan) or 'exit': ")
        
        if state.lower() == "exit":
            exit()
        elif state.lower() not in np_url_dict:
            print('[Error] Enter a state name.\n')
            continue
        else:
            print("-"*40)
            print(f"List of national sites in {state.title()}")
            state_url = np_url_dict[state.lower()]
            state_nps_list = get_sites_for_state(state_url)
            num = 1
            for park in state_nps_list :
                print(f"[{num}] {park.info()}")
                num = num+1
        
        print('-'*40)
        while True:
            num = input("Choose the number for detail search or 'exit' or 'back': ")
            if num == 'exit':
                exit()
            elif num == 'back':
                break
            elif num.isnumeric() and int(num) >= 1 and int(num) <= len(state_nps_list):
                site_chose = state_nps_list[int(num)-1]
                site_api_dict = get_nearby_places(site_chose)
                print_nearby_places(site_api_dict)
            else:
                print('[Error] Invalid Input')
                print('-'*40)
                continue


