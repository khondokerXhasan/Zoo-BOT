import json
import random
import hashlib
import asyncio
import aiohttp
import traceback
from time import time
from better_proxy import Proxy
from typing import Any, Callable, Optional, Union
from datetime import datetime, timedelta
from aiocfscrape import CloudflareScraper
from urllib.parse import unquote, quote, parse_qs
from random import randint, choices, uniform, choice
from aiohttp import ClientSession, ClientTimeout, ClientConnectorError
from aiohttp_proxy import ProxyConnector as http_connector
from aiohttp_socks import ProxyConnector as socks_connector

from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.raw.functions import account
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import (
    InputBotAppShortName,
    InputNotifyPeer,
    InputPeerNotifySettings,
)
from pyrogram.errors import (
    RPCError,
    FloodWait,
    Unauthorized,
    UserDeactivated,
    UserRestricted,
    PeerIdInvalid,
    UsernameInvalid,
    UsernameNotOccupied,
    ChannelPrivate,
    AuthKeyUnregistered,
    UserAlreadyParticipant,
    UserNotParticipant,
    UserDeactivatedBan,
)

from bot.utils import logger
from bot.config import settings
from bot.utils.proxy import get_proxy
from bot.exceptions import InvalidSession
from bot.core.agents import extract_chrome_version
from bot.core.registrator import get_tg_client
from bot.utils.safe_guard import safety_checker
from .headers import get_headers, options_headers
from bot.utils.helper import (
    time_until,
    format_number,
    best_animals,
    convert_utc_to_local,
    extract_json_from_response,
    get_param,
)


BASE_API = "https://api.zoo.team"  # √
auth_api = f"{BASE_API}/telegram/auth"  # √
getProfile_api = f"{BASE_API}/profile/info"
allUserData_api = f"{BASE_API}/user/data/all"  # √
allUserDataAfter_api = f"{BASE_API}/user/data/after"  # √
onboardingComplete_api = f"{BASE_API}/hero/onboarding/finish"  # √
resetOnboarding_api = f"{BASE_API}/hero/onboarding/reset"
getHero_api = f"{BASE_API}/hero/info"
getSettings_api = f"{BASE_API}/settings"
setSettings_api = f"{BASE_API}/settings/save"
loadDb_api = f"{BASE_API}/dbs"
assets_api = f"{BASE_API}/assets"
adminReset_api = f"{BASE_API}/admin/reset"
getRatings_api = f"{BASE_API}/ratings"
communityLeaderboard_api = f"{BASE_API}/community/leaderboard"
communityCreate_api = f"{BASE_API}/community/create"
getFriends_api = f"{BASE_API}/friends"
getQuests_api = f"{BASE_API}/quests/progress"  # √
claimQuest_api = f"{BASE_API}/quests/claim"  # √
checkQuest_api = f"{BASE_API}/quests/check"  # √
getDailyRewards_api = f"{BASE_API}/quests/daily"
claimDailyReward_api = f"{BASE_API}/quests/daily/claim"  # √
buyAnimal_api = f"{BASE_API}/animal/buy"  # √
animalChangePosition_api = f"{BASE_API}/animal/position"
boostBuy_api = f"{BASE_API}/boost/buy"
purchaseBuy_api = f"{BASE_API}/purchase/buy"
allianceCreate_api = f"{BASE_API}/alliance/create"
allianceRating_api = f"{BASE_API}/alliance/rating"
allianceJoin_api = f"{BASE_API}/alliance/join"
allianceSave_api = f"{BASE_API}/alliance/save"
allianceDonate_api = f"{BASE_API}/alliance/donate"
allianceLeave_api = f"{BASE_API}/alliance/leave"
allianceInfoByUser_api = f"{BASE_API}/alliance/user/info"  # √
friendsReferralBalance_api = f"{BASE_API}/friends/balance/referral"
referralBuyFeed_api = f"{BASE_API}/friends/balance/referral/feed/buy"
saveTonWallet_api = f"{BASE_API}/ton/wallet/save"  # √
infoTonWallet_api = f"{BASE_API}/ton/wallet/info"  # √
validateTonWallet_api = f"{BASE_API}/ton/wallet/validate"  # √
checkTransaction_api = f"{BASE_API}/ton/wallet/transaction/check"
tonTransactions_api = f"{BASE_API}/coins/ton/transactions"
quizResultSet_api = f"{BASE_API}/quiz/result/set"  # √
quizClaim_api = f"{BASE_API}/quiz/claim"  # √
autoFeedBuy_api = f"{BASE_API}/autofeed/buy"  # √

background_task: Optional[asyncio.Task[None]] = None


class Tapper:
    def __init__(
        self, tg_client: Client,
        multi_thread: bool
    ) -> None:
        self.multi_thread = multi_thread
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.bot_username = "zoo_story_bot"
        self.short_name = "game"
        self.my_ref = get_param()
        self.peer = None
        self.lock = asyncio.Lock()
        self.link = get_param()
        self.api_key = "empty"
        self.isWalletConnected = False
        self.TonWalletAddress = None

    async def get_tg_web_data(
        self,
        proxy: str | None
    ) -> str:
        proxy_dict = await self._parse_proxy(proxy)
        self.tg_client.proxy = proxy_dict
        try:
            async with self.lock:
                async with self.tg_client:
                    self.peer = await self.resolve_peer_with_retry(chat_id=self.bot_username, username=self.bot_username)
                    ref_id = str(settings.REF_LINK)
                    refer_id = choices([ref_id, self.link], weights=[70, 30], k=1)[
                        0]  # this is sensitive data don’t change it (if ydk)
                    self.refer_id = refer_id.split('=')[1]
                    web_view = await self.tg_client.invoke(
                        RequestAppWebView(
                            peer=self.peer,
                            platform='android',
                            app=InputBotAppShortName(
                                bot_id=self.peer,
                                short_name=self.short_name
                            ),
                            write_allowed=True,
                            start_param=self.refer_id
                        )
                    )
                    auth_url = web_view.url
                    return await self._extract_tg_web_data(auth_url)

        except InvalidSession as error:
            raise error
        except UserDeactivated:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Your Telegram account has been deactivated. You may need to reactivate it.")
            await asyncio.sleep(delay=3)
        except UserDeactivatedBan:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Your Telegram account has been banned. Contact Telegram support for assistance.")
            await asyncio.sleep(delay=3)
        except UserRestricted as e:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Your account is restricted. Details: {e}", exc_info=True)
            await asyncio.sleep(delay=3)
        except Unauthorized:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Session is Unauthorized. Check your API_ID and API_HASH")
            await asyncio.sleep(delay=3)
        except Exception as error:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def _extract_tg_web_data(self, auth_url: str) -> str:
        tg_web_data = unquote(
            string=unquote(
                string=auth_url.split('tgWebAppData=')[
                    1].split('&tgWebAppVersion')[0]
            )
        )
        self.tg_account_info = await self.tg_client.get_me()
        tg_web_data_parts = tg_web_data.split('&')

        data_dict = {part.split('=')[0]: unquote(
            part.split('=')[1]) for part in tg_web_data_parts}
        self.api_key = data_dict['hash']
        return f"user={quote(data_dict['user'])}&chat_instance={data_dict['chat_instance']}&chat_type={data_dict['chat_type']}&start_param={data_dict['start_param']}&auth_date={data_dict['auth_date']}&signature={data_dict['signature']}&hash={data_dict['hash']}"

    async def check_proxy(
        self,
        http_client: CloudflareScraper,
        proxy: str
    ) -> None:
        try:
            response = await http_client.get(url='https://ipinfo.io/json', timeout=ClientTimeout(total=20), ssl=settings.ENABLE_SSL)
            response.raise_for_status()
            response_json = await extract_json_from_response(response=response)
            ip = response_json.get('ip', 'NO')
            country = response_json.get('country', 'NO')
            logger.info(
                f"{self.session_name} | Proxy IP: <g>{ip}</g> | Country : <g>{country}</g>")
        except (asyncio.TimeoutError, ClientConnectorError) as e:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Network Connection error or Proxy is not online")
        except Exception as error:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Proxy: {proxy} | Error: {error}")

    async def _parse_proxy(
        self,
        proxy: str | None
    ) -> dict | None:

        if proxy:
            parsed = Proxy.from_str(proxy)
            return {
                'scheme': parsed.protocol,
                'hostname': parsed.host,
                'port': parsed.port,
                'username': parsed.login,
                'password': parsed.password
            }
        return None

    async def resolve_peer_with_retry(
        self,
        chat_id: int | str,
        username: str,
        max_retries: int = 5
    ):
        retries = 0
        peer = None
        while retries < max_retries:
            try:
                await self.get_dialog(username=username)
                peer = await self.tg_client.resolve_peer(chat_id)
                break

            except (KeyError, ValueError, PeerIdInvalid) as e:
                logger.warning(
                    f"{self.session_name} | Error resolving peer: <y>{str(e)}</y>. Retrying in <e>3</e> seconds.")
                await asyncio.sleep(3)
                retries += 1

            except FloodWait as error:
                wait_time = error.value + \
                    (15 * (retries + 1))  # Exponential backoff
                logger.warning(
                    f"{self.session_name} | FloodWait error | Retrying in <e>{wait_time}</e> seconds.")
                await asyncio.sleep(wait_time)
                retries += 1

                peer_found = await self.get_dialog(username=username)
                if peer_found:
                    peer = await self.tg_client.resolve_peer(chat_id)
                    break

        if not peer:
            logger.error(
                f"{self.session_name} | Could not resolve peer for <y>{username}</y> after <e>{retries}</e> retries.")

        return peer

    async def get_dialog(
        self,
        username: str
    ) -> bool:
        peer_found = False
        try:
            async for dialog in self.tg_client.get_dialogs():
                if dialog.chat and dialog.chat.username and dialog.chat.username.lower() == username.lower():
                    peer_found = True
                    break
        except Exception as e:
            logger.error(f"{self.session_name} | Error in get_dialog: {e}")
        return peer_found

    async def mute_and_archive_chat(
        self,
        chat,
        peer,
        username: str
    ) -> None:
        try:
            # Mute notifications
            await self.tg_client.invoke(
                account.UpdateNotifySettings(
                    peer=InputNotifyPeer(peer=peer),
                    settings=InputPeerNotifySettings(mute_until=2147483647)
                )
            )
            logger.info(
                f"{self.session_name} | Successfully muted chat <g>{chat.title}</g> for channel <y>{username}</y>")

            # Archive the chat
            await asyncio.sleep(delay=5)
            if settings.ARCHIVE_CHANNELS:
                await self.tg_client.archive_chats(chat_ids=[chat.id])
                logger.info(
                    f"{self.session_name} | Channel <g>{chat.title}</g> successfully archived for channel <y>{username}</y>")
        except RPCError as e:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Error muting or archiving chat <g>{chat.title}</g>: {e}", exc_info=True)

    async def join_tg_channel(
        self,
        link: str,
        max_retries: int = 10
    ) -> None:
        retries = 0
        peer = None
        while retries < max_retries:
            async with self.lock:
                async with self.tg_client:
                    try:
                        parsed_link = link if 'https://t.me/+' in link else link[13:]
                        username = parsed_link if "/" not in parsed_link else parsed_link.split("/")[
                            0]

                        # Refresh Chat list
                        await self.get_dialog(username=username)

                        chat_info = await self.tg_client.get_chat(username)

                        participants = await self.tg_client.get_chat_members_count(chat_info.id)
                        logger.info(
                            f"{self.session_name} | Channel <g>{username}</g> has <g>{format_number(participants)}</g> members")

                        chat_type = str(getattr(chat_info, 'type', '')).upper()

                        if 'CHANNEL' in chat_type or 'SUPERGROUP' in chat_type:
                            try:
                                await self.tg_client.get_chat_member(chat_info.id, "me")
                                logger.info(
                                    f"{self.session_name} | Already a member of <y>{chat_info.title}</y>")
                                return

                            except UserNotParticipant:
                                try:
                                    chat = await self.tg_client.join_chat(username)
                                    chat_id = chat.id
                                    logger.success(
                                        f"{self.session_name} | Successfully joined to <g>{chat.title}</g>")

                                    await asyncio.sleep(delay=5)
                                    peer = await self.resolve_peer_with_retry(chat_id, username)
                                    if peer:
                                        await self.mute_and_archive_chat(chat, peer, username)
                                    return

                                except FloodWait as error:
                                    wait_time = error.value + \
                                        15 + (retries + 2)
                                    logger.info(
                                        f"{self.session_name} | FloodWait required | Wait <e>{wait_time}</e> seconds.")

                                    await asyncio.sleep(wait_time)
                                    retries += 1
                                    continue

                        else:
                            logger.error(
                                f"{self.session_name} | Chat type not supported: {chat_type} for {username}")
                            return

                    except (UsernameInvalid, UsernameNotOccupied) as e:
                        logger.error(
                            f"{self.session_name} | Invalid username or chat doesn't exist: {username}")
                        return

                    except RPCError as e:
                        logger.error(
                            f"{self.session_name} | Chat <y>{username}</y> error: {str(e)}")
                        if "CHANNEL_PRIVATE" in str(e):
                            logger.error(
                                f"{self.session_name} | This is a private channel and requires an invite link")
                        raise

                    except (UserDeactivated, UserDeactivatedBan, UserRestricted,
                            AuthKeyUnregistered, Unauthorized) as e:
                        logger.error(
                            f"<light-yellow>{self.session_name}</light-yellow> | Account error: {str(e)}")
                        return

                    except Exception as error:
                        logger.error(
                            f"<light-yellow>{self.session_name}</light-yellow> | Error while joining channel: {error} {link}")
                        await asyncio.sleep(delay=3)
                        retries += 1
                        continue

                    return

    async def change_name(
        self,
        symbol: str
    ) -> bool:
        async with self.lock:
            async with self.tg_client:
                try:
                    me = await self.tg_client.get_me()
                    first_name = me.first_name
                    last_name = me.last_name if me.last_name else ''
                    tg_name = f"{me.first_name or ''} {me.last_name or ''}".strip()

                    if symbol not in tg_name:
                        changed_name = f'{first_name}{symbol}'
                        await self.tg_client.update_profile(first_name=changed_name)
                        logger.info(
                            f"{self.session_name} | First name changed <g>{first_name}</g> to <g>{changed_name}</g>")
                        await asyncio.sleep(delay=randint(20, 30))
                    return True
                except Exception as error:
                    logger.error(
                        f"<light-yellow>{self.session_name}</light-yellow> | Error while changing tg name : {error}")
                    return False

    async def remove_symbol(
        self,
        symbol: str
    ) -> bool:
        async with self.lock:
            async with self.tg_client:
                try:
                    me = await self.tg_client.get_me()
                    first_name = me.first_name
                    last_name = me.last_name if me.last_name else ''
                    tg_name = f"{me.first_name or ''} {me.last_name or ''}".strip()

                    if symbol in tg_name:
                        changed_name = str(first_name).replace(symbol, "")
                        await self.tg_client.update_profile(first_name=changed_name)
                        logger.info(
                            f"{self.session_name} | First name changed <g>{first_name}</g> to <g>{changed_name}</g>")
                        await asyncio.sleep(delay=randint(20, 30))
                    return True
                except Exception as error:
                    logger.error(
                        f"<light-yellow>{self.session_name}</light-yellow> | Error while changing tg name : {error}")
                    return False

    async def make_request(
        self,
        http_client: CloudflareScraper,
        method: str,
        url: str,
        params: Optional[dict] = None,
        payload: Optional[dict] = None,
        max_retries: int = 10,
        delay: int = 10,
        timeout: int = 50,
        ssl: bool = settings.ENABLE_SSL,
        api_key: str = "empty",
        is_beta_server: str = "null",
        sleep: int = 1
    ) -> Optional[Union[dict | list | int | str | bool]]:
        retries = 0
        while retries < max_retries:
            try:
                async with self.lock:
                    await asyncio.sleep(sleep)
                    await http_client.options(
                        url=url,
                        headers=options_headers(
                            method=method.upper(), kwarg=http_client.headers),
                        timeout=ClientTimeout(total=timeout),
                        ssl=ssl
                    )
                    current_time = int(time())
                    api_hash = hashlib.md5(
                        f"{current_time}_{json.dumps(payload)}".encode('utf-8')).hexdigest()

                    http_client.headers['Api-Key'] = api_key
                    http_client.headers['Api-Time'] = str(current_time)
                    http_client.headers['Api-Hash'] = api_hash
                    http_client.headers['is-beta-server'] = is_beta_server
                    response = await http_client.request(
                        method=method.upper(),
                        url=url,
                        params=params,
                        json=payload,
                        timeout=ClientTimeout(total=timeout),
                        ssl=ssl
                    )
                    if response.status == 200:
                        return await extract_json_from_response(response=response)
                    else:
                        retries += 1
                        logger.warning(
                            f"{self.session_name} | Request to <c>{url}</c> failed: <r>{response.status}</r>, retrying... (<g>{retries}</g>/<r>{max_retries}</r>)")
                        await asyncio.sleep(delay)
                        delay *= 2
            except (asyncio.TimeoutError) as e:
                retries += 1
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)
            except (ClientConnectorError) as e:
                retries += 1
                logger.warning(
                    f"{self.session_name} | Network Connection Error: {e}, retrying... (<g>{retries}</g>/<r>{max_retries}</r>)", exc_info=True)
                await asyncio.sleep(delay)
                delay *= 2
            except Exception as e:
                # traceback.print_exc()
                logger.warning(
                    f"{self.session_name} | Unknown error while making request to <y>{url}</y>: {e}", exc_info=True)
                return None
        return None

    async def create_payload_from_initdata(
        self,
        init_data: str
    ):
        parsed = parse_qs(init_data)
        user_data = json.loads(unquote(parsed['user'][0]))
        payload = {
            "data": {
                "initData": init_data,
                "startParam": parsed['start_param'][0],
                "photoUrl": user_data['photo_url'],
                "platform": "android",
                "chatId": "",
                "chatType": parsed['chat_type'][0],
                "chatInstance": parsed['chat_instance'][0]
            }
        }
        return payload

    async def login(
        self,
        http_client: CloudflareScraper
    ) -> Optional[dict]:
        payload = await self.create_payload_from_initdata(init_data=self.tg_web_data)
        response = await self.make_request(http_client=http_client, method="POST", url=auth_api, payload=payload)
        return response

    async def data_all(
        self,
        http_client: CloudflareScraper
    ) -> Optional[dict]:
        payload = {"data": {}}
        response = await self.make_request(http_client=http_client, method="POST", url=allUserData_api, payload=payload, api_key=self.api_key)
        return response

    async def data_after(
        self,
        http_client: CloudflareScraper
    ) -> Optional[dict]:
        payload = {"data": {"lang": "en"}}
        response = await self.make_request(http_client=http_client, method="POST", url=allUserDataAfter_api, payload=payload, api_key=self.api_key)
        return response

    async def claim_daily(
        self,
        http_client: CloudflareScraper,
        day: int
    ) -> Optional[dict]:
        payload = {"data": day}
        response = await self.make_request(http_client=http_client, method="POST", url=claimDailyReward_api, payload=payload, api_key=self.api_key)
        return response

    async def quests_progress(
        self,
        http_client: CloudflareScraper
    ) -> Optional[dict]:
        payload = {"data": ""}
        response = await self.make_request(http_client=http_client, method="POST", url=getQuests_api, payload=payload, api_key=self.api_key)
        return response

    async def claim_quest(
        self,
        http_client: CloudflareScraper,
        payload: dict,
        sleep: int
    ) -> Optional[dict]:
        response = await self.make_request(http_client=http_client, method="POST", url=claimQuest_api, payload=payload, api_key=self.api_key, sleep=sleep)
        return response

    async def check_quest(
        self,
        http_client: CloudflareScraper,
        key: str,
        code: str | bool = None
    ) -> Optional[dict]:
        payload = {"data": [str(key), str(code)]}
        response = await self.make_request(http_client=http_client, method="POST", url=checkQuest_api, payload=payload, api_key=self.api_key)
        return response

    async def quest_claimer(
        self,
        http_client: CloudflareScraper,
        key: str,
        code: bool | str = True,
        sleep: int = 1
    ) -> None:
        if isinstance(code, str):
            payload = {"data": [str(key), str(code)]}
        else:
            payload = {"data": [str(key), None]} if code == True else {
                "data": [str(key)]}
        claim = await self.claim_quest(http_client=http_client, payload=payload, sleep=sleep)
        if claim and claim.get('success', False):
            self.coins = claim['data']['hero']["coins"]
            quests = claim["data"]["quests"]
            return any(quest["key"] == key and quest.get("isRewarded", False) for quest in quests)
        return False

    async def wallet_info(
        self,
        http_client: CloudflareScraper
    ) -> Optional[dict]:
        payload = {}
        response = await self.make_request(http_client=http_client, method="POST", url=infoTonWallet_api, payload=payload, api_key=self.api_key)
        return response

    async def validate_wallet(
        self,
        http_client: CloudflareScraper,
        wallet_proof: dict
    ) -> Optional[dict]:
        payload = {"data": {"wallet": wallet_proof}}
        response = await self.make_request(http_client=http_client, method="POST", url=validateTonWallet_api, payload=payload, api_key=self.api_key)
        return response

    async def save_wallet(
        self,
        http_client: CloudflareScraper,
        wallet_proof: dict
    ) -> Optional[dict]:
        payload = {"data": {"wallet": wallet_proof}}
        response = await self.make_request(http_client=http_client, method="POST", url=saveTonWallet_api, payload=payload, api_key=self.api_key)
        return response

    async def complete_onboarding(
        self,
        http_client: CloudflareScraper,
        onboarding_id: int
    ) -> Optional[dict]:
        payload = {"data": onboarding_id}
        response = await self.make_request(http_client=http_client, method="POST", url=onboardingComplete_api, payload=payload, api_key=self.api_key, sleep=10)
        return response

    async def alliance_info(
        self,
        http_client: CloudflareScraper,
        alliance_admin_uid: int
    ) -> Optional[dict]:
        payload = {"data": str(alliance_admin_uid)}
        response = await self.make_request(http_client=http_client, method="POST", url=allianceInfoByUser_api, payload=payload, api_key=self.api_key)
        return response

    async def set_quiz(
        self,
        http_client: CloudflareScraper,
        key: str,
        result: str
    ) -> Optional[dict]:
        payload = {"data": {"key": str(key), "result": str(result)}}
        response = await self.make_request(http_client=http_client, method="POST", url=quizResultSet_api, payload=payload, api_key=self.api_key, sleep=5)
        return response

    async def claim_quiz(
        self,
        http_client: CloudflareScraper,
        key: str
    ) -> Optional[dict]:
        payload = {"data": {"key": str(key)}}
        response = await self.make_request(http_client=http_client, method="POST", url=quizClaim_api, payload=payload, api_key=self.api_key, sleep=5)
        return response

    async def onboarding(
        self,
        http_client: CloudflareScraper,
        onboarding_id: int = 1
    ) -> None:
        if str(onboarding_id) not in self.dbOnboarding:
            res = await self.complete_onboarding(http_client=http_client, onboarding_id=onboarding_id)
            if res.get("success", False) and str(onboarding_id) in res.get("data", {}).get("onboarding", []):
                self.dbOnboarding = res.get("data", {}).get("onboarding", [])
                logger.info(
                    f"{self.session_name} | Onboarding <g>{onboarding_id}</g> Completed")

    async def buy_animal(
        self,
        http_client: CloudflareScraper,
        key: str,
        position: int
    ) -> Optional[dict]:
        payload = {"data": {"position": int(position), "animalKey": key}}
        response = await self.make_request(http_client=http_client, method="POST", url=buyAnimal_api, payload=payload, api_key=self.api_key, sleep=10)
        return response

    async def buy_autofeed(
        self,
        http_client: CloudflareScraper
    ) -> Optional[dict]:
        payload = {"data": "instant"}
        response = await self.make_request(http_client=http_client, method="POST", url=autoFeedBuy_api, payload=payload, api_key=self.api_key, sleep=10)
        return response

    async def join_alliance(
        self,
        http_client: CloudflareScraper,
        alliance_id: int
    ) -> Optional[dict]:
        payload = {"data": alliance_id}
        response = await self.make_request(http_client=http_client, method="POST", url=allianceJoin_api, payload=payload, api_key=self.api_key, sleep=10)
        return response

    async def donate_alliance(
        self,
        http_client: CloudflareScraper,
        amount: int
    ) -> Optional[dict]:
        payload = {"data": amount}
        response = await self.make_request(http_client=http_client, method="POST", url=allianceDonate_api, payload=payload, api_key=self.api_key, sleep=10)
        return response

    async def chest_claimer(
        self,
        http_client: CloudflareScraper,
        data: dict
    ) -> None:
        key = data.get('key', None)
        current_time = int(time())
        actionTo = data.get('actionTo', None)
        reward = data.get('reward', 0)
        title = key.replace('_', '-')
        actionTo_timestamp = convert_utc_to_local(actionTo)
        if self.multi_thread:
            if actionTo_timestamp > current_time:
                wait = int(actionTo_timestamp - current_time) + randint(10, 50)
                logger.info(
                    f"{self.session_name} | Chest task is in background, it will available in: <e>{wait / 60 :.2f}</e> minutes")
                await asyncio.sleep(wait)
        else:
            if actionTo_timestamp > current_time:
                return
        claim = await self.quest_claimer(http_client=http_client, key=key, code=False)
        if claim:
            logger.success(
                f"{self.session_name} | Quest <g>{title}</g> claimed | rewarded: <g>+{format_number(reward)}</g>")

    async def buy_manager(
        self,
        http_client: CloudflareScraper,
        dbAnimals: dict
    ) -> None:

        available_animals = [Animal for Animal in dbAnimals if Animal['key'] not in [animal["key"] for animal in self.animals]]

        level = 1
        best_animal = best_animals(
            coins=self.coins, level=level, dbAnimals=available_animals)

        for x in best_animal:

            if len(self.animals) >= int(settings.MAX_ANIMALS):
                return

            price = x["price"]
            key = x["key"]
            title = x["title"]
            profit = x['profit']
            used_positions = [animal["position"] for animal in self.animals]

            if int(settings.COIN_TO_SAVE) < self.coins and int(self.coins - price) >= int(settings.COIN_TO_SAVE):
                random_position = choice(
                    [n for n in range(1, 38) if n not in used_positions])
                buy_res = await self.buy_animal(http_client=http_client, key=key, position=random_position)
                if buy_res.get("success", False):
                    self.coins = int(buy_res.get("data", {}).get('hero', {}).get('coins', 0))
                    self.animals = buy_res.get("data", {}).get('animals', {})
                    self.tph = int(buy_res.get("data", {}).get('hero', {}).get('tph', 0))
                    logger.success(
                        f"{self.session_name} | Purchased animal <g>{title}</g> | Cost: <r>-{format_number(price)}</r> coin | TPH: <g>+{format_number(profit)}</g> | Available Coin: <g>{format_number(self.coins)}</g>")

    async def upgrade_manager(
        self,
        http_client: CloudflareScraper,
        dbAnimals: dict
    ) -> None:

        upgradeable_animal = []
        for animal in self.animals:
            id = animal.get('id')
            key = animal.get('key')
            level = animal.get('level')
            position = animal.get('position')
            animal_data = next(
                (animal for animal in dbAnimals if animal["key"] == key), None)
            nextLevel = int(level + 1)
            nextLevelData = next(
                (level for level in animal_data["levels"] if level["level"] == nextLevel), None)
            if animal_data and nextLevelData and int(settings.COIN_TO_SAVE) < self.coins and int(self.coins - int(nextLevelData["price"])) >= int(settings.COIN_TO_SAVE):
                upgrade_animal = await self.buy_animal(http_client=http_client, key=key, position=position)
                if upgrade_animal.get("success", False):
                    title = animal_data.get('title', 'Not Found')
                    price = nextLevelData.get('price', 0)
                    profit = nextLevelData.get('profit', 0)
                    self.coins = int(upgrade_animal.get("data", {}).get('hero', {}).get('coins', self.coins))
                    self.animals = upgrade_animal.get("data", {}).get('animals', {})
                    self.tph = int(upgrade_animal.get("data", {}).get('hero', {}).get('tph', 0))
                    logger.success(
                        f"{self.session_name} | Upgraded animal <g>{title}</g> Level <g>{level}</g> to <g>{nextLevel}</g> | Cost: <r>-{format_number(price)}</r> coin | TPH: <g>+{format_number(profit)}</g> | Available Coin: <g>{format_number(self.coins)}</g>")

    async def run(
        self,
        user_agent: str,
        proxy: str | None
    ) -> None:
        global background_task
        if settings.USE_RANDOM_DELAY_IN_RUN:
            random_delay = randint(
                settings.START_DELAY[0], settings.START_DELAY[1])
            logger.info(
                f"{self.session_name} | 🕚 wait <c>{random_delay}</c> second before starting...")
            await asyncio.sleep(random_delay)

        proxy_conn = (
            socks_connector.from_url(proxy) if proxy and 'socks' in proxy else
            http_connector.from_url(proxy) if proxy and 'http' in proxy else
            (logger.warning(f"{self.session_name} | Proxy protocol not recognized. Proceeding without proxy.") or None) if proxy else
            None
        )
        headers = get_headers()
        headers["User-Agent"] = user_agent
        chrome_ver = extract_chrome_version(
            user_agent=headers['User-Agent']).split('.')[0]
        headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not?A_Brand";v="24"'

        timeout = ClientTimeout(total=60)
        async with CloudflareScraper(headers=headers, connector=proxy_conn, trust_env=True, auto_decompress=False, timeout=timeout) as http_client:

            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)

            while True:
                can_run = True
                try:
                    end_at = 3600 * 3
                    isDailyClaimed = False
                    if await safety_checker(self.session_name) is False:

                        can_run = False
                        logger.warning(
                            "<y>Detected change index in js file. Contact me to check if it's safe to continue</y>: <g>https://t.me/scripts_hub</g>")
                        return round(end_at / 60)

                    if can_run:
                        self.tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        if self.tg_web_data is None:
                            logger.warning(
                                f"{self.session_name} | retrieving telegram web data failed")
                            return

                        ### Login ###
                        login = await self.login(http_client=http_client)
                        if login.get('success', None):
                            logger.success(
                                f"{self.session_name} | Login Successful")

                        ### Alliance Info ###
                        alliance_info = await self.alliance_info(http_client=http_client, alliance_admin_uid=str(self.tg_account_info.id))

                        ### All Data ###
                        all_data = await self.data_all(http_client=http_client)
                        if all_data.get('success', None):
                            all_data_ = all_data.get('data', {})
                            profile = all_data_.get('profile', {})
                            self.animals = all_data_.get('animals', [])
                            hero = all_data_.get('hero', {})
                            self.dbOnboarding = hero.get("onboarding", [])
                            dbData = all_data_.get('dbData', {})
                            dbAnimals = dbData.get('dbAnimals', [])
                            dbPurchase = dbData.get('dbPurchase', [])
                            dbAlliance = dbData.get('dbAlliance', [])
                            dbBoost = dbData.get('dbBoost', [])
                            dbQuests = dbData.get('dbQuests', [])
                            gameConfig = dbData.get('gameConfig', {})
                            dbDailyRewards = dbData.get('dbDailyRewards', [])
                            dbQuizzes = dbData.get('dbQuizzes', [])
                            dbAutoFeed = dbData.get('dbAutoFeed', [])
                            self.feedData = all_data_.get('feed', {})
                            self.alliance = all_data_.get('alliance', {})

                        ### Define User id ###
                        self.user_id = profile["id"]

                        ### Initial Onboarding ###
                        await self.onboarding(http_client=http_client, onboarding_id=1)

                        ### User Data ###
                        self.tokens = hero.get('tokens', 0)
                        self.coins = hero.get('coins', 0)
                        self.tph = hero.get('tph', 0)
                        logger.info(
                            f"{self.session_name} | Animals: <g>{len(self.animals)}</g> | TPH: <g>{format_number(self.tph)}</g> - Token: <g>{format_number(self.tokens)}</g> - Coin: <g>{format_number(self.coins)}</g>")

                        ### Data After (Activity) ###
                        after_data = await self.data_after(http_client=http_client)
                        if after_data.get('success', None):
                            after_data_ = after_data.get('data', {})
                            dailyRewards = after_data_.get('dailyRewards', {})
                            CompleatedQuests = after_data_.get('quests', [])
                            CompletedQuizzes = after_data_.get('quizzes', [])

                        ### Daily Reward ###
                        if dailyRewards:
                            day = next(
                                (int(num) for num, status in dailyRewards.items() if status == "canTake"), None)
                            if isinstance(day, int):
                                reward = next(
                                    (money['rewardMoney'] for money in dbDailyRewards if money["key"] == day), 0)
                                claim_data = await self.claim_daily(http_client=http_client, day=day)
                                if claim_data.get('success', None):
                                    if claim_data['data']["dailyRewards"][str(day)] == "taken":
                                        self.coins = claim_data['data']['hero']["coins"]
                                        logger.success(
                                            f"{self.session_name} | <g>Daily Claimed</g> - day: <g>{day}</g> - rewarded: <g>+{format_number(reward)}</g>")
                                        isDailyClaimed = True

                        ### Alliance info ###
                        if self.alliance:
                            allianceName = self.alliance.get(
                                "name", "Not Found")
                            allianceLevel = self.alliance.get("level", 0)
                            logger.info(
                                f"{self.session_name} | Alliance Name: <g>{allianceName}</g> - Level: <g>{allianceLevel}</g>")
                        else:
                            if settings.AUTO_JOIN_ALLIANCE and int(settings.ALLIANCE_JOIN_FEE) >= 1000 and self.coins > int(settings.ALLIANCE_JOIN_FEE):
                                alliance_id = int(settings.ALLIANCE_ID)
                                join_res = await self.join_alliance(http_client=http_client, alliance_id=alliance_id)
                                if join_res.get('success', None):
                                    hero = join_res.get(
                                        'data', {}).get('hero', {})
                                    self.alliance = join_res.get(
                                        'data', {}).get('alliance', {})
                                    tphAlliance = hero.get('tphAlliance', 0)
                                    self.coins = hero.get('coins', self.coins)
                                    enterFee = self.alliance.get('enterFee', 0)
                                    name = self.alliance.get('name', 0)
                                    logger.success(
                                        f"{self.session_name} | <g>Successfully Joined Alliance</g> | Name: <g>{name}</g> | Cost: <r>-{format_number(enterFee)}</r> | TPH: <g>+{format_number(tphAlliance)}</g>")

                            elif int(settings.ALLIANCE_JOIN_FEE) >= 1000:
                                logger.warning(
                                    f"{self.session_name} | Alliance join fee should be 1000 or max")

                        ### Donate to the alliance to gain extra TPH ###
                        if settings.DONATE_TO_ALLIANCE and isDailyClaimed:
                            amount = choice(
                                range(
                                    settings.DONATE_AMOUNT[0],
                                    settings.DONATE_AMOUNT[1],
                                    5
                               )
                            )
                            if (settings.COIN_TO_SAVE < self.coins) and (self.coins > amount):
                                donate = await self.donate_alliance(http_client=http_client, amount=amount)
                                if donate.get('success', None):
                                    self.coins = donate["data"]["hero"]["coins"]
                                    logger.success(
                                        f"{self.session_name} | Donated <g>{format_number(amount)}</g> Coin to level up Alliance | Available Coins: <g>{format_number(self.coins)}</g>")

                        ### Quests Progress ###
                        QuestsProgress = await self.quests_progress(http_client=http_client)
                        CompleatedQuestsList = []
                        if QuestsProgress.get('success', None):
                            CompleatedQuests = QuestsProgress.get('data', [])
                            for quest in CompleatedQuests:
                                key = quest.get('key')
                                CompleatedQuestsList.append(key)
                                if not quest.get('isRewarded', True):
                                    claim = await self.quest_claimer(http_client=http_client, key=key)
                                    Quest = next(
                                        (x for x in dbQuests if x["key"] == key), {})
                                    title = Quest.get("title", "Not Found")
                                    reward = Quest.get("reward", 0)
                                    type_ = Quest.get("checkType")
                                    symbol = Quest.get("checkData")
                                    if claim:
                                        logger.success(
                                            f"{self.session_name} | Quest <g>{title}</g> claimed | rewarded: <g>+{format_number(reward)}</g>")
                                        if type_ == "username":
                                            await self.remove_symbol(symbol=symbol)

                        ### Completeed Quizzes ###
                        CompletedQuizzesList = []
                        for quiz in CompletedQuizzes:
                            key = quiz.get('key')
                            CompletedQuizzesList.append(key)
                            if not quiz.get('isRewarded', True):
                                claim = await self.claim_quiz(http_client=http_client, key=key)
                                Quiz = next(
                                    (x for x in dbQuizzes if x["key"] == key), {})
                                title = Quiz.get("title", "Not Found")
                                reward = Quiz.get("reward", 0)
                                if claim.get('success', None):
                                    logger.success(
                                        f"{self.session_name} | Quiz <g>{title}</g> claimed | rewarded: <g>+{format_number(reward)}</g>")
                                    self.coins = claim['data']['hero']["coins"]

                        ### Quests ###
                        if dbQuests and settings.AUTO_DO_TASKS:
                            for Quest in dbQuests:
                                dateStart = Quest["dateStart"]
                                dateEnd = Quest["dateEnd"]
                                start_time_str = dateStart if dateStart and dateStart != "" else "2024-12-31 23:59:59"
                                end_time_str = dateEnd if dateEnd and dateEnd != "" else "2099-12-31 23:59:59"
                                start_time = convert_utc_to_local(
                                    start_time_str)
                                end_time = convert_utc_to_local(end_time_str)
                                current_time = int(time())

                                QuestType = Quest.get("checkType", None)
                                reward = Quest.get("reward", 0)
                                key = Quest.get("key", None)
                                title = Quest.get("title", "Not Found")

                                if (
                                    key not in CompleatedQuestsList
                                    and QuestType in settings.TO_DO_QUEST
                                    and QuestType not in settings.NOT_TO_DO_QUEST
                                    # and "boost" not in str(key)
                                    and start_time <= current_time and end_time >= current_time
                                ):

                                    if QuestType == "telegramChannel":
                                        actionUrl = Quest["actionUrl"]
                                        await self.join_tg_channel(actionUrl)
                                        check_tg = await self.check_quest(http_client=http_client, key=key)
                                        if check_tg.get("success", None) and check_tg.get("data", {}).get("result", False):
                                            logger.info(
                                                f"{self.session_name} | Quest <g>{title}</g> checked")
                                            claim_tg = await self.quest_claimer(http_client=http_client, key=key)
                                            if claim_tg:
                                                logger.success(
                                                    f"{self.session_name} | Quest <g>{title}</g> claimed | rewarded: <g>+{format_number(reward)}</g>")

                                    if QuestType == "ton_wallet_connect":
                                        pass  # -_-

                                    if QuestType == "fakeCheck":

                                        if key.startswith("chest_"):
                                            if self.multi_thread:
                                                background_task = asyncio.create_task(
                                                    self.chest_claimer(http_client=http_client, data=Quest))
                                            else:
                                                await self.chest_claimer(http_client=http_client, data=Quest)
                                        else:
                                            claim_fake = await self.quest_claimer(http_client=http_client, key=key)
                                            if claim_fake:
                                                logger.success(
                                                    f"{self.session_name} | Quest <g>{title}</g> claimed | rewarded: <g>+{format_number(reward)}</g>")

                                    if QuestType == "checkCode":
                                        code = Quest["checkData"]
                                        check_code = await self.check_quest(http_client=http_client, key=key, code=code)
                                        if check_code.get("success", None) and check_code.get("data", {}).get("result", False):
                                            logger.info(
                                                f"{self.session_name} | Quest <g>{title}</g> checked")
                                            claim_code = await self.quest_claimer(http_client=http_client, key=key, code=code)
                                            if claim_code:
                                                logger.success(
                                                    f"{self.session_name} | Quest <g>{title}</g> claimed | Code: <g>{code}</g> | rewarded: <g>+{format_number(reward)}</g>")

                                    if QuestType == "username":
                                        symbol = Quest["checkData"]
                                        await self.change_name(symbol=symbol)

                        ### Quizzes ###
                        if dbQuizzes and settings.AUTO_DO_QUIZZES:
                            for Quiz in dbQuizzes:
                                if Quiz not in CompletedQuizzesList:
                                    key = Quiz.get('key')
                                    title = Quiz.get(
                                        'title', 'Title not found')
                                    reward = Quiz.get('reward')
                                    answers = Quiz.get('answers', {})
                                    results = [answer["key"]
                                               for answer in Quiz.get('answers', {})]
                                    result = choice(results)
                                    set_quiz = await self.set_quiz(http_client=http_client, key=key, result=result)
                                    if set_quiz.get('success', False):
                                        claim = await self.claim_quiz(http_client=http_client, key=key)
                                        if claim.get('success', False):
                                            logger.success(
                                                f"{self.session_name} | Quiz <g>{title}</g> claimed | rewarded: <g>+{format_number(reward)}</g>")
                                            self.coins = claim['data']['hero']["coins"]

                        ### Onboarding 50 After Sharing Invite Link To Friend ###
                        await self.onboarding(http_client=http_client, onboarding_id=50)

                        if settings.AUTO_BUY_ANIMALS:
                            await self.buy_manager(http_client=http_client, dbAnimals=dbAnimals)
                        else:
                            if self.coins < int(settings.COIN_TO_SAVE):
                                logger.info(
                                    f"{self.session_name} | Not enough coin to buy animals | Coin: <g>{self.coins}<g>")

                        ### A Funny Mechanism To Handle Onboarding event ###
                        TOSS = choice(
                            ["H", "A", "S", "A", "N", "X", "K", "H", "O", "N", "D", "O", "K", "E", "R"])
                        if TOSS == "H":
                            # appear while changing animal position
                            await self.onboarding(http_client=http_client, onboarding_id=40)
                        elif TOSS == "X":
                            # Appear While Enter In Buy Section
                            await self.onboarding(http_client=http_client, onboarding_id=31)
                        elif TOSS == "K":
                            # I Don't Know
                            await self.onboarding(http_client=http_client, onboarding_id=30)

                        if settings.AUTO_UPGRADE_ANIMALS:
                            await self.upgrade_manager(http_client=http_client, dbAnimals=dbAnimals)

                        if settings.AUTO_FEED_ANIMALS:

                            isNeedFeed = self.feedData.get('isNeedFeed', False)
                            autoFeedEndDate = self.feedData.get(
                                'autoFeedEndDate', False)

                            if autoFeedEndDate:
                                await self.onboarding(http_client=http_client, onboarding_id=21)
                            else:
                                await self.onboarding(http_client=http_client, onboarding_id=20)

                            if isNeedFeed:
                                feedRes = await self.buy_autofeed(http_client=http_client)
                                if feedRes.get('success', False):

                                    coin = feedRes.get('data', {}).get(
                                        'hero', {}).get('coins', self.coins)
                                    self.feedData = feedRes.get(
                                        'data', {}).get('feed', {})
                                    cost = self.coins - int(coin)
                                    logger.success(
                                        f"{self.session_name} | <g>Purchased AutoFeed</g> | Cost: <r>-{format_number(cost)}</r> coin")

                                else:
                                    logger.success(
                                        f"{self.session_name} | <y>Insufficient balance to buy AutoFeed</y>")
                            else:
                                logger.info(
                                    f"{self.session_name} | Auto Feeding in progress... ")
                            nextFeedTime = self.feedData.get('nextFeedTime')
                            nextFeedTimestamp = convert_utc_to_local(
                                nextFeedTime)
                            current_time = int(time())
                            end_at = int(nextFeedTimestamp - current_time)

                    if self.multi_thread is True:
                        sleep = round(end_at / 60) + randint(9, 15)
                        logger.info(
                            f"{self.session_name} | 🕦 Sleep <y>{sleep}</y> min")
                        await asyncio.sleep(sleep * 60)
                        if background_task is not None and not background_task.done():
                            background_task.cancel()
                            logger.info(
                                f"{self.session_name} | Background task stopped.")

                    else:
                        logger.info(
                            f"{self.session_name} | <m>==== Completed ====</m>")
                        await asyncio.sleep(3)
                        return round(end_at / 60)

                except InvalidSession as error:
                    raise error
                except (KeyboardInterrupt, RuntimeError):
                    pass
                except Exception as error:
                    traceback.print_exc()
                    logger.error(
                        f"<light-yellow>{self.session_name}</light-yellow> | Unknown error: {error}")
                    await asyncio.sleep(delay=randint(60, 120))


async def run_tapper(tg_client: Client, user_agent: str, proxy: str | None):
    try:
        await Tapper(
            tg_client=tg_client,
            multi_thread=True
        ).run(
            user_agent=user_agent,
            proxy=proxy,
        )
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")


async def run_tapper_synchronous(accounts: list[dict]):
    while True:
        for account in accounts:
            try:
                session_name, user_agent, raw_proxy = account.values()
                tg_client = await get_tg_client(session_name=session_name, proxy=raw_proxy)
                proxy = get_proxy(raw_proxy=raw_proxy)

                _ = await Tapper(
                    tg_client=tg_client,
                    multi_thread=False
                ).run(
                    proxy=proxy,
                    user_agent=user_agent,
                )

                sleep = min(_ or 0, (_ or 0) + randint(9, 15))

            except InvalidSession:
                logger.error(f"{tg_client.name} | Invalid Session")

        logger.info(f"Sleep <red>{round(sleep, 1)}</red> minutes")
        await asyncio.sleep(sleep * 60)
