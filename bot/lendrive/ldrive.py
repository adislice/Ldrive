from bs4 import BeautifulSoup
import requests

from log import LOGGER

class Lendrive:
    _website = "https://lendrive.web.id/"

    def search(self, query) -> dict:
        LOGGER.info("Search : " + query)
        search_url = self._website + "/?s=" + query
        res = requests.get(search_url)
        if res.status_code != 200:
            LOGGER.error("Error")
        soup = BeautifulSoup(res.text, 'html.parser')
        bixbox = soup.find('div', class_='bixbox')
        listupd = bixbox.find('div', class_='listupd')
        article_list = listupd.find_all('article', class_='bs')
        search_result = {}
        for index,article in enumerate(article_list):
            post = article.find('a')
            post_url = post['href'] or '-'
            post_title = post.find('div', class_='tt').find(text=True, recursive=False).strip()
            post_title = post_title[:60] + '' * (len(post_title) > 60)
            search_result[index] = {
                'title' : post_title,
                'url' : post_url
            }
            if index > 10:
                break
        # this will be returned
        search_return = {
            'status' : True,
            'result' : search_result
        }
        return search_return

    def parse_anime_info(self, anime_url) -> dict:
        LOGGER.info("Anime : " + anime_url)
        res = requests.get(anime_url)
        if res.status_code != 200:
            LOGGER.error("Error")
        soup = BeautifulSoup(res.text, 'html.parser')
        #content > div.postbody
        postbody = soup.find('div', class_='postbody')
        # anime info
        #post-* > div.bixbox.animefull > div.bigcontent
        bigcontent = postbody.find('div', class_='bigcontent')
        # find thumbnail
        thumb_div = bigcontent.find('div', class_='thumb')
        thumb_img_url = thumb_div.find('img')['src']
        # find rating
        rat_div = bigcontent.find('div', class_='rating')
        rating = rat_div.find('strong').text
        # find anime details
        infox_div = bigcontent.find('div', class_='infox')
        anime_title = infox_div.find('h1', class_='entry-title').text
        #post-* > div.bixbox.animefull > div.bigcontent > div.infox > div.ninfo > div.info-content > div.spe
        details_soup = infox_div.find('div', class_='spe')
        details_div = details_soup.find_all('span')
        post = ""
        post += anime_title + '\n'
        anime_details = ""
        for detail in details_div:
            span = detail.find_all(text=True)
            # Make first item having bold text
            temp = span[0]
            span[0] = f"<b>{temp}</b>"
            info = ''.join(span)
            anime_details += info + '\n'
        # find synopsis
        #post-* > div.bixbox.synp
        syn_div = postbody.find('div', class_='bixbox synp')
        syn_container = syn_div.find('div', class_='entry-content', itemprop='description') if syn_div is not None else False
        if syn_container:
            syn_paragraphs = syn_container.find_all('p')
            par = [i.text for i in syn_paragraphs]
        else:
            par = ["Tidak ada sinopsisnya! Cari sendiri di gugel."]
        anime_sinopsis = "\n".join(par)
        # find genres
        #post-* > div.bixbox.animefull > div.bigcontent > div.infox > div.ninfo > div.info-content > div.genxed
        genre_div = infox_div.find('div', class_='genxed')
        genres_tags = genre_div.find_all('a')
        genres_list = [i.text for i in genres_tags] # list ['Action', 'Drama', ...]
        genres_str = ', '.join(genres_list)
        # find episode list
        ep_div = postbody.find('div', class_='eplister').find('ul').find_all('li')
        episodes_list = {}
        for index,ep_tag in enumerate(ep_div):
            ep_link = ep_tag.find('a')['href']
            ep_num = ep_tag.find('div', class_='epl-num').text
            episodes_list[index] = {
                'ep_num':ep_num,
                'ep_link':ep_link
            }
    
        anime_info = {
            'status': True,
            'result': {
                'anime_title' : anime_title,
                'anime_url': anime_url,
                'anime_thumbnail_url' : thumb_img_url,
                'anime_details' : anime_details,
                'anime_rating': rating,
                'anime_genres': genres_str,
                'anime_sinopsis' : anime_sinopsis,
                'anime_episodes' : episodes_list
            }
        }
        return anime_info


    def parse_episode(self, url):
        LOGGER.info("Episode : " + url)
        page_res = requests.get(url)
        if page_res.status_code != 200:
            LOGGER.error("Error when requesting")
        soup = BeautifulSoup(page_res.text, 'html.parser')
        post_container = soup.find('div', class_='epwrapper')
        title = post_container.find(class_='entry-title').text or '?'
        thumb_div = post_container.find('div', class_='thumbnail')
        thumb_img_url = thumb_div.find('img')['src'] if thumb_div is not None else None
        dl_box = post_container.find('div', class_='soraddlx soradlg')
        episode = {}
        dl_name = dl_box.find('div', class_='sorattlx').findChildren()[0].text
        episode['url'] = url
        episode['title'] = dl_name
        dl_links = dl_box.find_all('div', class_='soraurlx')
        dl_mirrors = {}
        for index,link in enumerate(dl_links):
            quality = link.findChildren()[0].text
            url_list = link.find_all('a')
            quality_list = {}
            for i,url in enumerate(url_list):
                mirror_name = url.text or '-'
                mirror_link = url['href'] or '-'
                quality_list[i] = {
                    'name' : mirror_name, 
                    'url' : mirror_link
                    }
            dl_mirrors[index] = {
                'quality' : quality,
                'mirror_list' :quality_list
            }
        episode['dl_mirrors'] = dl_mirrors
        episode['thumbnail'] = thumb_img_url
        return episode

