import traceback
from asyncio.exceptions import TimeoutError

import orjson
from httpx import ConnectTimeout, PoolTimeout
from loguru import logger

from ..config import hikari_config
from ..HttpClient_Pool import get_client_yuyuko, recreate_client_yuyuko
from ..model import Hikari_Model
from .publicAPI import get_ClanIdByName


async def get_cw_recent(hikari: Hikari_Model) -> Hikari_Model:
    """查询公会cw赛季战斗记录"""
    try:
        if hikari.Status == 'init':
            if hikari.Input.Search_Type == 3:
                clanList = await get_ClanIdByName(hikari.Input.Server, hikari.Input.ClanName)
                if clanList:
                    if len(clanList) < 2:
                        hikari.Input.ClanId = clanList[0]['clanId']
                    else:
                        hikari.Input.Select_Data = clanList
                        hikari.set_template_info('select-clan.html', 360, 100)
                        return hikari.wait(clanList)
                else:
                    return hikari.failed('找不到军团，请确认军团名是否正确')
        elif hikari.Status == 'wait':
            if hikari.Input.Select_Data and hikari.Input.Select_Index and hikari.Input.Select_Index <= len(hikari.Input.Select_Data):
                hikari.Input.ClanId = hikari.Input.Select_Data[hikari.Input.Select_Index - 1]['clanId']
            else:
                return hikari.error('请选择有效的序号')
        else:
            return hikari.error('当前请求状态错误')

        # if hikari.Input.Search_Type == 3:
        #    is_cache = await check_yuyuko_cache(hikari.Input.Server, hikari.Input.AccountId)
        # else:
        #    is_cache = await check_yuyuko_cache(hikari.Input.Platform, hikari.Input.PlatformId)
        # if is_cache:
        #    logger.success('上报数据成功')
        # else:
        #    logger.success('跳过上报数据，直接请求')

        url = f'{hikari_config.yuyuko_url}/public/wows/clan/battle/info'
        params = {
            'season': hikari.Input.CwSeasonId,
            'server': hikari.Input.Server,
            'clanId': hikari.Input.ClanId,
            'team': hikari.Input.Recent_Day,
        }

        client_yuyuko = await get_client_yuyuko()
        resp = await client_yuyuko.get(url, params=params, timeout=10)
        result = orjson.loads(resp.content)
        hikari.Output.Yuyuko_Code = result['code']
        if result['code'] == 200:
            if result['data']:
                hikari.set_template_info('wws-clan-cw.html', 1200, 100)
            else:
                return hikari.failed("没有战斗数据")
            return hikari.success(result['data'])
        elif result['code'] == 403:
            return hikari.failed(f"{result['message']}\n请先绑定账号")
        elif result['code'] == 500:
            return hikari.failed(f"{result['message']}\n这是服务器问题，请联系雨季麻麻")
        else:
            return hikari.failed(f"{result['message']}")
    except (TimeoutError, ConnectTimeout):
        logger.warning(traceback.format_exc())
        return hikari.error('请求超时了，请过会儿再尝试哦~')
    except PoolTimeout:
        await recreate_client_yuyuko()
        return hikari.error('连接池异常，请尝试重新查询~')
    except Exception:
        logger.error(traceback.format_exc())
        return hikari.error('wuwuwu出了点问题，请联系麻麻解决')
