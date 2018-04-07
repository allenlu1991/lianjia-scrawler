﻿import core
import model
import settings

def get_communitylist():
	res = []
	for community in model.Community.select():
		res.append(community.title)
	return res

if __name__=="__main__":
    # regionlist = settings.REGIONLIST # only pinyin support
    regionlist = core.getRegionByArea(settings.AREA)
    model.database_init()

    # core.GetHouseByRegionlist(regionlist)
    core.GetRentByRegionlist(regionlist)
    # core.GetCommunityByRegionlist(regionlist) # Init,scrapy celllist and insert database; could run only 1st time
    # # communitylist = get_communitylist() # Read celllist from database
    # core.GetSellByCommunitylist(communitylist)
