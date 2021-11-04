

def create_pages(li):
    nais = {}
    page = []
    temp = []
    dict_idx = 0
    for i, val in enumerate(li):
        temp.append(val)
        if len(temp) > 3:
            page.append(temp)
            temp = []
        if len(page) > 3:
            dict_idx += 1
            nais[dict_idx] = page
            page = []
        if i == len(li)-1:
            dict_idx += 1
            page.append(temp)
            nais[dict_idx] = page
            break
    return nais

def dl_links_to_post(p: dict) -> str:
    post = ""
    post += f"<code>{p['title']}</code>\n\n"
    for k,v in p['dl_mirrors'].items():
        quality = v['quality']
        mirror_list = v['mirror_list']
        link_post_list = []
        link_post = ""
        for ky,vv in mirror_list.items():
            hosting = vv['name']
            dl_link = vv['url']
            a_href = f"<a href='{dl_link}'>{hosting}</a>"
            link_post_list.append(a_href)
        link_post = ' | '.join(link_post_list)
        post += f"⁍ <b>{quality}</b>\n   {link_post}\n\n"
    return post

def get_rating(rat:str) -> str:
    star = '⭐'
    try:
        rating = rat.split(' ')
        rat_str = rating[0]
        rat_num = rating[1]
        rat_float = float(rat_num) / 2
        rat_round = round(rat_float)
        rat_star = star*rat_round
        return "<b>"+rat_str+":</b> "+rat_star+' '+rat_num
    except:
        return ' <b>'+ rating + '</b> '+star
