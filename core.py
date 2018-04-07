﻿# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import settings
import model
import misc
import shlib
import time
import datetime
import urllib2
import logging
import json

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
BASE_URL = u"http://%s.lianjia.com/" % (settings.CITY)
CITY = settings.CITY

def GetHouseByCommunitylist(communitylist):
    logging.info("Get House Infomation")
    starttime = datetime.datetime.now()
    for community in communitylist:
        try:
            if CITY == 'sh':
                shlib.get_house_percommunity(community)
            get_house_percommunity(community)
        except Exception as e:
            logging.error(e)
            logging.error(community + "Fail")
            pass
    endtime = datetime.datetime.now()
    logging.info("Run time: " + str(endtime - starttime))

def GetSellByCommunitylist(communitylist):
    logging.info("Get Sell Infomation")
    starttime = datetime.datetime.now()
    for community in communitylist:
        try:
            if CITY == 'sh':
                shlib.get_sell_percommunity(community)
            get_sell_percommunity(community)
        except Exception as e:
            logging.error(e)
            logging.error(community + "Fail")
            pass
    endtime = datetime.datetime.now()
    logging.info("Run time: " + str(endtime - starttime))

def GetRentByCommunitylist(communitylist):
    logging.info("Get Rent Infomation")
    starttime = datetime.datetime.now()
    for community in communitylist:
        try:
            if CITY == 'sh':
                shlib.get_rent_percommunity(community)
            get_rent_percommunity(community)
        except Exception as e:
            logging.error(e)
            logging.error(community + "Fail")
            pass
    endtime = datetime.datetime.now()
    logging.info("Run time: " + str(endtime - starttime))

def GetCommunityByRegionlist(regionlist=[u'xicheng']):
    logging.info("Get Community Infomation")
    starttime = datetime.datetime.now()
    for regionname in regionlist:
        try:
            if CITY == 'sh':
                shlib.get_community_perregion(regionname)
            get_community_perregion(regionname)
            logging.info(regionname + "Done")
        except Exception as e:
            logging.error(e)
            logging.error(regionname + "Fail")
            pass
    endtime = datetime.datetime.now()
    logging.info("Run time: " + str(endtime - starttime))

def GetHouseByRegionlist(regionlist=[u'xicheng']):
    starttime = datetime.datetime.now()
    for regionname in regionlist:
        logging.info("Get Onsale House Infomation in %s" % regionname)
        try:
            if CITY == 'sh':
                shlib.get_house_perregion(regionname)
            get_house_perregion(regionname)
        except Exception as e:
            logging.error(e)
            pass
    endtime = datetime.datetime.now()
    logging.info("Run time: " + str(endtime - starttime))

def GetRentByRegionlist(regionlist=[u'xicheng']):
    starttime = datetime.datetime.now()
    for regionname in regionlist:
        logging.info("Get Rent House Infomation in %s" % regionname)
        try:
            if CITY == 'sh':
                shlib.get_rent_perregion(regionname)
            get_rent_perregion(regionname)
        except Exception as e:
            logging.error(e)
            pass
    endtime = datetime.datetime.now()
    logging.info("Run time: " + str(endtime - starttime))

def get_house_percommunity(communityname):
    url = BASE_URL + u"ershoufang/rs" + urllib2.quote(communityname.encode('utf8')) + "/"
    source_code = misc.get_source_code(url)
    soup = BeautifulSoup(source_code, 'lxml')

    if check_block(soup):
        return
    total_pages = misc.get_total_pages(url)

    if total_pages == None:
        row = model.Houseinfo.select().count()
        raise RuntimeError("Finish at %s because total_pages is None" % row)

    for page in range(total_pages):
        if page > 0:
            url_page = BASE_URL + u"ershoufang/pg%drs%s/" % (page, urllib2.quote(communityname.encode('utf8')))
            source_code = misc.get_source_code(url_page)
            soup = BeautifulSoup(source_code, 'lxml')

        nameList = soup.findAll("li", {"class":"clear"})
        i = 0
        log_progress("GetHouseByCommunitylist", communityname, page+1, total_pages)
        data_source = []
        hisprice_data_source = []
        for name in nameList: # per house loop
            i = i + 1
            info_dict = {}
            try:
                housetitle = name.find("div", {"class":"title"})
                info_dict.update({u'title':housetitle.get_text().strip()})
                info_dict.update({u'link':housetitle.a.get('href')})

                houseaddr = name.find("div", {"class":"address"})
                info = houseaddr.div.get_text().split('|')
                info_dict.update({u'community':info[0].strip()})
                info_dict.update({u'housetype':info[1].strip()})
                info_dict.update({u'square':info[2].strip()})
                info_dict.update({u'direction':info[3].strip()})
                info_dict.update({u'decoration':info[4].strip()})

                housefloor = name.find("div", {"class":"flood"})
                floor_all = housefloor.div.get_text().split('-')[0].strip().split(' ')
                info_dict.update({u'floor':floor_all[0].strip()})
                info_dict.update({u'years':floor_all[-1].strip()})

                followInfo = name.find("div", {"class":"followInfo"})
                info_dict.update({u'followInfo':followInfo.get_text()})

                tax = name.find("div", {"class":"tag"})
                info_dict.update({u'taxtype':tax.get_text().strip()})

                totalPrice = name.find("div", {"class":"totalPrice"})
                info_dict.update({u'totalPrice':totalPrice.span.get_text()})

                unitPrice = name.find("div", {"class":"unitPrice"})
                info_dict.update({u'unitPrice':unitPrice.get('data-price')})
                info_dict.update({u'houseID':unitPrice.get('data-hid')})
            except:
                continue
            # houseinfo insert into mysql
            data_source.append(info_dict)
            hisprice_data_source.append({"houseID":info_dict["houseID"], "totalPrice":info_dict["totalPrice"]})
            #model.Houseinfo.insert(**info_dict).upsert().execute()
            #model.Hisprice.insert(houseID=info_dict['houseID'], totalPrice=info_dict['totalPrice']).upsert().execute()

        with model.database.atomic():
            model.Houseinfo.insert_many(data_source).upsert().execute()
            model.Hisprice.insert_many(hisprice_data_source).upsert().execute()
        time.sleep(1)

def get_sell_percommunity(communityname):
    url = BASE_URL + u"chengjiao/rs" + urllib2.quote(communityname.encode('utf8')) + "/"
    source_code = misc.get_source_code(url)
    soup = BeautifulSoup(source_code, 'lxml')

    if check_block(soup):
        return
    total_pages = misc.get_total_pages(url)

    if total_pages == None:
        row = model.Sellinfo.select().count()
        raise RuntimeError("Finish at %s because total_pages is None" % row)

    for page in range(total_pages):
        if page > 0:
            url_page = BASE_URL + u"chengjiao/pg%drs%s/" % (page, urllib2.quote(communityname.encode('utf8')))
            source_code = misc.get_source_code(url_page)
            soup = BeautifulSoup(source_code, 'lxml')
        i = 0
        log_progress("GetSellByCommunitylist", communityname, page+1, total_pages)
        data_source = []
        for ultag in soup.findAll("ul", {"class":"listContent"}):
            for name in ultag.find_all('li'):
                i = i + 1
                info_dict = {}
                try:
                    housetitle = name.find("div", {"class":"title"})
                    info_dict.update({u'title':housetitle.get_text().strip()})
                    info_dict.update({u'link':housetitle.a.get('href')})
                    houseID = housetitle.a.get('href').split("/")[-1].split(".")[0]
                    info_dict.update({u'houseID':houseID.strip()})

                    house = housetitle.get_text().strip().split(' ')
                    info_dict.update({u'community':house[0].strip()})
                    info_dict.update({u'housetype':house[1].strip()})
                    info_dict.update({u'square':house[2].strip()})

                    houseinfo = name.find("div", {"class":"houseInfo"})
                    info = houseinfo.get_text().split('|')
                    info_dict.update({u'direction':info[0].strip()})
                    info_dict.update({u'status':info[1].strip()})

                    housefloor = name.find("div", {"class":"positionInfo"})
                    floor_all = housefloor.get_text().strip().split(' ')
                    info_dict.update({u'floor':floor_all[0].strip()})
                    info_dict.update({u'years':floor_all[-1].strip()})

                    followInfo = name.find("div", {"class":"source"})
                    info_dict.update({u'source':followInfo.get_text().strip()})

                    totalPrice = name.find("div", {"class":"totalPrice"})
                    if totalPrice.span is None:
                        info_dict.update({u'totalPrice':totalPrice.get_text().strip()})
                    else:
                        info_dict.update({u'totalPrice':totalPrice.span.get_text().strip()})

                    unitPrice = name.find("div", {"class":"unitPrice"})
                    if unitPrice.span is None:
                        info_dict.update({u'unitPrice':unitPrice.get_text().strip()})
                    else:
                        info_dict.update({u'unitPrice':unitPrice.span.get_text().strip()})

                    dealDate= name.find("div", {"class":"dealDate"})
                    info_dict.update({u'dealdate':dealDate.get_text().strip().replace('.','-')})

                except:
                    continue
                # Sellinfo insert into mysql
                data_source.append(info_dict)
                #model.Sellinfo.insert(**info_dict).upsert().execute()

        with model.database.atomic():
            model.Sellinfo.insert_many(data_source).upsert().execute()
        time.sleep(1)

def get_community_perregion(regionname=u'xicheng'):
    url = BASE_URL + u"xiaoqu/" + regionname +"/"
    source_code = misc.get_source_code(url)
    soup = BeautifulSoup(source_code, 'lxml')

    if check_block(soup):
        return
    total_pages = misc.get_total_pages(url)

    if total_pages == None:
        row = model.Community.select().count()
        raise RuntimeError("Finish at %s because total_pages is None" % row)

    for page in range(total_pages):
        url_page = BASE_URL + u"xiaoqu/" + regionname +"/pg%d/" % (page+1)
        source_code = misc.get_source_code(url_page)
        soup = BeautifulSoup(source_code, 'lxml')

        nameList = soup.findAll("li", {"class":"clear"})
        i = 0
        log_progress("GetCommunityByRegionlist", regionname, page+1, total_pages)
        data_source = []
        for name in nameList: # Per house loop
            i = i + 1
            info_dict = {}
            try:
                communitytitle = name.find("div", {"class":"title"})
                title = communitytitle.get_text().strip('\n')
                link = communitytitle.a.get('href')
                info_dict.update({u'title':title})
                info_dict.update({u'link':link})

                district = name.find("a", {"class":"district"})
                info_dict.update({u'district':district.get_text()})

                bizcircle = name.find("a", {"class":"bizcircle"})
                info_dict.update({u'bizcircle':bizcircle.get_text()})

                tagList = name.find("div", {"class":"tagList"})
                info_dict.update({u'tagList':tagList.get_text().strip('\n')})

                onsale = name.find("a", {"class":"totalSellCount"})
                info_dict.update({u'onsale':onsale.span.get_text().strip('\n')})

                onrent = name.find("a", {"title":title+u"租房"})
                info_dict.update({u'onrent':onrent.get_text().strip('\n').split(u'套')[0]})

                info_dict.update({u'id':name.get('data-housecode')})

                price = name.find("div", {"class":"totalPrice"})
                info_dict.update({u'price':price.span.get_text().strip('\n')})


                communityinfo = get_communityinfo_by_url(link)
                for key, value in communityinfo.iteritems():
                    info_dict.update({key:value})

            except:
                continue
            # communityinfo insert into mysql
            data_source.append(info_dict)
            #model.Community.insert(**info_dict).upsert().execute()

        with model.database.atomic():
            model.Community.insert_many(data_source).upsert().execute()
        time.sleep(1)

def get_rent_percommunity(communityname):
    url = BASE_URL + u"zufang/rs" + urllib2.quote(communityname.encode('utf8')) + "/"
    source_code = misc.get_source_code(url)
    soup = BeautifulSoup(source_code, 'lxml')

    if check_block(soup):
        return
    total_pages = misc.get_total_pages(url)

    if total_pages == None:
        row = model.Rentinfo.select().count()
        raise RuntimeError("Finish at %s because total_pages is None" % row)

    for page in range(total_pages):
        if page > 0:
            url_page = BASE_URL + u"rent/pg%drs%s/" % (page, urllib2.quote(communityname.encode('utf8')))
            source_code = misc.get_source_code(url_page)
            soup = BeautifulSoup(source_code, 'lxml')
        i = 0
        log_progress("GetRentByCommunitylist", communityname, page+1, total_pages)
        data_source = []
        for ultag in soup.findAll("ul", {"class":"house-lst"}):
            for name in ultag.find_all('li'):
                i = i + 1
                info_dict = {}
                try:
                    housetitle = name.find("div", {"class":"info-panel"})
                    info_dict.update({u'title':housetitle.get_text().strip()})
                    info_dict.update({u'link':housetitle.a.get('href')})
                    houseID = housetitle.a.get('href').split("/")[-1].split(".")[0]
                    info_dict.update({u'houseID':houseID})

                    region = name.find("span", {"class":"region"})
                    info_dict.update({u'region':region.get_text().strip()})

                    zone = name.find("span", {"class":"zone"})
                    info_dict.update({u'zone':zone.get_text().strip()})

                    meters = name.find("span", {"class":"meters"})
                    info_dict.update({u'meters':meters.get_text().strip()})

                    other = name.find("div", {"class":"con"})
                    info_dict.update({u'other':other.get_text().strip()})

                    subway = name.find("span", {"class":"fang-subway-ex"})
                    if subway is None:
                        info_dict.update({u'subway':""})
                    else:
                        info_dict.update({u'subway':subway.span.get_text().strip()})

                    decoration = name.find("span", {"class":"decoration-ex"})
                    if decoration is None:
                        info_dict.update({u'decoration':""})
                    else:
                        info_dict.update({u'decoration':decoration.span.get_text().strip()})

                    heating = name.find("span", {"class":"heating-ex"})
                    info_dict.update({u'heating':heating.span.get_text().strip()})

                    price = name.find("div", {"class":"price"})
                    info_dict.update({u'price':int(price.span.get_text().strip())})

                    pricepre = name.find("div", {"class":"price-pre"})
                    info_dict.update({u'pricepre':pricepre.get_text().strip()})

                except:
                    continue
                # Rentinfo insert into mysql
                data_source.append(info_dict)
                #model.Rentinfo.insert(**info_dict).upsert().execute()

        with model.database.atomic():
            model.Rentinfo.insert_many(data_source).upsert().execute()
        time.sleep(1)

def getRegionByArea(areaList):
    regionList = []

    for area in areaList:
        try:
            url = BASE_URL + u"ershoufang/%s/" % area
            source_code = misc.get_source_code(url)
            soup = BeautifulSoup(source_code, 'lxml')
            if check_block(soup):
                return
            for regionInfo in soup.find('div',{"class":"sub_sub_nav"}).find_all('a'):
                region = regionInfo.get('href').strip().split('/ershoufang/')[1].rstrip('/')
                regionList.append(region)
        except Exception as e:
            logging.error(e)
            pass
    return regionList

def get_house_perregion(district):
    url = BASE_URL + u"ershoufang/%s/" % district
    source_code = misc.get_source_code(url)
    soup = BeautifulSoup(source_code, 'html5lib')
    if check_block(soup):
        return
    total_pages = misc.get_total_pages(url)
    if total_pages == None:
        row = model.Houseinfo.select().count()
        raise RuntimeError("Finish at %s because total_pages is None" % row)

    for page in range(total_pages):
        url_page = BASE_URL + u"ershoufang/%s/pg%d/" % (district, page+1)
        source_code = misc.get_source_code(url_page)
        soup = BeautifulSoup(source_code, 'html5lib')

        i = 0
        log_progress("GetHouseByRegionlist", district, page+1, total_pages)
        data_source = []
        hisprice_data_source = []
        for ultag in soup.findAll("ul", {"class":"sellListContent"}):
            namearr = ultag.find_all('li',{"class":"clear"})

            for name in namearr:

                i = i + 1
                info_dict = {}
                try:
                    housetitle = name.find("div", {"class":"title"})
                    info_dict.update({u'title':housetitle.get_text().strip()})
                    info_dict.update({u'link':housetitle.a.get('href')})
                    houseID = housetitle.a.get('data-housecode')
                    info_dict.update({u'houseID':houseID})


                    houseinfo = name.find("div", {"class":"houseInfo"})
                    info = houseinfo.get_text().split('/')
                    info_communityid = houseinfo.a.get('href').split('xiaoqu/')
                    communityid = info_communityid[1].strip().rstrip('/')
                    square_info = info[2].encode("utf-8").split('平米')

                    info_dict.update({u'community':info[0]})
                    info_dict.update({u'communityid':communityid})
                    info_dict.update({u'housetype':info[1]})
                    info_dict.update({u'square':square_info[0]})
                    info_dict.update({u'direction':info[3]})
                    info_dict.update({u'decoration':info[4]})

                    housefloor = name.find("div", {"class":"positionInfo"})
                    info_housefloor = housefloor.get_text().split('/')
                    
                    info_years = info_housefloor[1].strip().encode("utf-8").split('年建') #unicode作为python中间编码，先转化成utf8(decode:...->unicode,encode:unicode->...)
                    info_floor = info_housefloor[0].split('(')
                    info_buildheight = info_floor[1].encode("utf-8").rstrip('层)').lstrip('共')


                    info_dict.update({u'years':info_years[0].strip()})
                    info_dict.update({u'buildingtype':info_years[1].strip()})
                    info_dict.update({u'floor':info_floor[0].strip()})
                    info_dict.update({u'buildheight':info_buildheight.strip()})

                    followInfo = name.find("div", {"class":"followInfo"})
                    info_dict.update({u'followInfo':followInfo.get_text().strip()})

                    taxfree = name.find("span", {"class":"taxfree"})
                    if taxfree == None:
                        five = name.find("span", {"class":"five"})
                        if five == None:
                            info_dict.update({u"taxtype":""})
                        else:
                            info_dict.update({u"taxtype":five.get_text().strip()})
                    else:
                        info_dict.update({u"taxtype":taxfree.get_text().strip()})

                    totalPrice = name.find("div", {"class":"totalPrice"})
                    info_dict.update({u'totalPrice':totalPrice.span.get_text()})

                    unitPrice = name.find("div", {"class":"unitPrice"})
                    info_dict.update({u'unitPrice':unitPrice.get("data-price")})

                except:
                    continue

                # Houseinfo insert into mysql
                data_source.append(info_dict)
                hisprice_data_source.append({"houseID":info_dict["houseID"], "totalPrice":info_dict["totalPrice"]})
                #model.Houseinfo.insert(**info_dict).upsert().execute()
                #model.Hisprice.insert(houseID=info_dict['houseID'], totalPrice=info_dict['totalPrice']).upsert().execute()

        with model.database.atomic():
            model.Houseinfo.insert_many(data_source).upsert().execute()
            model.Hisprice.insert_many(hisprice_data_source).upsert().execute()
        time.sleep(1)

def getRentInfoFromCommunity(search_community, rid, hid):
    if rid in search_community:
        return search_community

    url = 'https://bj.lianjia.com/zufang/housestat?hid=%s&rid=%s' % (hid, rid)

    try:
        source_code = misc.get_source_code(url)
        json_obj = json.loads(source_code)

        rentData = json_obj['data']['resblockSold']
        data_source = []

        logging.info("Progress: %s: %s" % ('getRentInfoFromCommunity', url))

        for rentInfo in rentData:
            info_dict = {}

            info_dict.update({u'title':rentInfo['resblockName'] +u' '+ rentInfo['title']})
            info_dict.update({u'link':rentInfo['house_url']})
            info_dict.update({u'houseID':rentInfo['houseId']})
            info_dict.update({u'regionid':rid})
            info_dict.update({u'region':rentInfo['resblockName']})
            info_dict.update({u'zone':rentInfo['title']})
            info_dict.update({u'meters':rentInfo['area']})
            info_dict.update({u'other':rentInfo['floor']+'/'+rentInfo['totalFloor']+u'层 '+rentInfo['orientation']+' '+rentInfo['decoration']})
            info_dict.update({u'subway':''})
            info_dict.update({u'decoration':u'同小区成交记录'})
            info_dict.update({u'heating':''})
            info_dict.update({u'price':rentInfo['price']})
            info_dict.update({u'pricepre':rentInfo['transDate']+u' 成交'})

            data_source.append(info_dict)

        with model.database.atomic():
            model.Rentinfo.insert_many(data_source).upsert().execute()
        time.sleep(1)

    except Exception as e:
        logging.error(e)


    search_community.append(rid)
    return search_community

def get_rent_perregion(district):
    url = BASE_URL + u"zufang/%s/" % district
    source_code = misc.get_source_code(url)
    soup = BeautifulSoup(source_code, 'lxml')

    search_community = []

    if check_block(soup):
        return
    total_pages = misc.get_total_pages(url)
    if total_pages == None:
        row = model.Rentinfo.select().count()
        raise RuntimeError("Finish at %s because total_pages is None" % row)

    for page in range(total_pages):
        url_page = BASE_URL + u"zufang/%s/pg%d/" % (district, page+1)
        source_code = misc.get_source_code(url_page)
        soup = BeautifulSoup(source_code, 'lxml')

        i = 0
        log_progress("GetRentByRegionlist", district, page+1, total_pages)
        data_source = []
        for ultag in soup.findAll("ul", {"class":"house-lst"}):
            for name in ultag.find_all('li'):
                i = i + 1
                info_dict = {}
                try:
                    housetitle = name.find("div", {"class":"info-panel"})
                    info_dict.update({u'title':housetitle.h2.a.get_text().strip()})
                    info_dict.update({u'link':housetitle.a.get("href")})
                    houseID = name.get("data-housecode")
                    info_dict.update({u'houseID':houseID})

                    region = name.find("span", {"class":"region"})
                    info_regionid = region.parent.get("href").split("xiaoqu/")
                    regionid = info_regionid[1].strip().rstrip("/")

                    info_dict.update({u'regionid':regionid})
                    info_dict.update({u'region':region.get_text().strip()})

                    zone = name.find("span", {"class":"zone"})
                    info_dict.update({u'zone':zone.get_text().strip()})

                    meters = name.find("span", {"class":"meters"})
                    info_meters = meters.get_text().strip().encode("utf-8").rstrip("平米")
                    info_dict.update({u'meters':info_meters})

                    other = name.find("div", {"class":"con"})
                    info_dict.update({u'other':other.get_text().strip()})

                    subway = name.find("span", {"class":"fang-subway-ex"})
                    if subway == None:
                        info_dict.update({u'subway':""})
                    else:
                        info_dict.update({u'subway':subway.span.get_text().strip()})

                    decoration = name.find("span", {"class":"decoration-ex"})
                    if decoration == None:
                        info_dict.update({u'decoration': ""})
                    else:
                        info_dict.update({u'decoration':decoration.span.get_text().strip()})

                    heating = name.find("span", {"class":"heating-ex"})
                    if decoration == None:
                        info_dict.update({u'heating': ""})
                    else:
                        info_dict.update({u'heating':heating.span.get_text().strip()})

                    price = name.find("div", {"class":"price"})
                    info_dict.update({u'price':int(price.span.get_text().strip())})

                    pricepre = name.find("div", {"class":"price-pre"})
                    info_dict.update({u'pricepre':pricepre.get_text().strip()})

                    search_community = getRentInfoFromCommunity(search_community, regionid, houseID)

                except:
                    continue

                # Rentinfo insert into mysql
                data_source.append(info_dict)
                #model.Rentinfo.insert(**info_dict).upsert().execute()

        with model.database.atomic():
            model.Rentinfo.insert_many(data_source).upsert().execute()
        time.sleep(1)

def get_communityinfo_by_url(url):
    source_code = misc.get_source_code(url)
    soup = BeautifulSoup(source_code, 'lxml')

    if check_block(soup):
        return

    communityinfos = soup.findAll("div", {"class":"xiaoquInfoItem"})
    res = {}
    for info in communityinfos:
        key_type = {
        u"建筑年代": "year",
        u"建筑类型": "housetype",
        u"物业费用": "cost",
        u"物业公司": "service",
        u"开发商": "company",
        u"楼栋总数": "building_num",
        u"房屋总数": "house_num",
        }
        try:
            key = info.find("span",{"xiaoquInfoLabel"})
            value = info.find("span",{"xiaoquInfoContent"})
            key_info = key_type[key.get_text().strip()]

            if key_info == 'building_num':
                value_info = value.get_text().strip().encode("utf-8").rstrip("栋")
            elif key_info == 'house_num':
                value_info = value.get_text().strip().encode("utf-8").rstrip("户")
            else:
                value_info = value.get_text().strip()
            res.update({key_info:value_info})

        except:
            continue
    return res

def check_block(soup):
    if soup.title.string == "414 Request-URI Too Large":
        logging.error("Lianjia block your ip, please verify captcha manually at lianjia.com")
        return True
    return False

def log_progress(function, address, page, total):
    logging.info("Progress: %s %s: current page %d total pages %d" %(function, address, page, total))
