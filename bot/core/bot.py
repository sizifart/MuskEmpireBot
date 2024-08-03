import asyncio, aiohttp, random, math, json, hashlib
from time import time
from zoneinfo import ZoneInfo
from datetime import datetime
from urllib.parse import unquote
from typing import Any, Dict
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestWebView

from bot.utils.logger import log
from bot.utils.settings import config
from .headers import headers

class CryptoBot:
	def __init__(self, tg_client: Client):
		self.session_name = tg_client.name
		self.tg_client = tg_client
		self.user_id = None
		self.api_url = 'https://api.muskempire.io'
		self.need_quiz = False
		self.need_rebus = False
		self.rebus_key = ''
		self.errors = 0

	async def get_tg_web_data(self, proxy: str | None) -> Dict[str, Any]:
		if proxy:
			proxy = Proxy.from_str(proxy)
			proxy_dict = dict(
				scheme=proxy.protocol,
				hostname=proxy.host,
				port=proxy.port,
				username=proxy.login,
				password=proxy.password
			)
		else:
			proxy_dict = None

		self.tg_client.proxy = proxy_dict

		try:
			if not self.tg_client.is_connected:
				try:
					await self.tg_client.connect()
				except (Unauthorized, UserDeactivated, AuthKeyUnregistered) as error:
					raise RuntimeError(str(error)) from error
			web_view = await self.tg_client.invoke(RequestWebView(
				peer=await self.tg_client.resolve_peer('muskempire_bot'),
				bot=await self.tg_client.resolve_peer('muskempire_bot'),
				platform='android',
				from_bot_menu=False,
				url='https://game.muskempire.io/'
			))
			auth_url = web_view.url
			tg_web_data = unquote(
				string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])
			
			user_hash = tg_web_data[tg_web_data.find('hash=') + 5:]
			self.api_key = user_hash
			if self.tg_client.is_connected:
				await self.tg_client.disconnect()
			
			login_data = {'data': {
					'initData' : tg_web_data,
					'platform' : 'android',
					'chatId' : ''
				}
			}
			return login_data

		except RuntimeError as error:
			raise error

		except Exception as error:
			log.error(f"{self.session_name} | Authorization error: {error}")
			await asyncio.sleep(delay=3)

	async def login(self, json_data: Dict[str, Any]) -> bool:
		url = self.api_url + '/telegram/auth'
		try:
			log.info(f"{self.session_name} | Trying to login...")
			self.http_client.headers['Api-Key'] = 'empty'
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success: return True
			else: return False
		except Exception as error:
			log.error(f"{self.session_name} | Login error: {error}")
			self.errors += 1
			await asyncio.sleep(delay=3)
			return False
	
	async def set_sign_headers(self, data: Dict[str, Any]) -> None:
		time_string = str(int(time()))
		json_string = json.dumps(data)
		hash_object = hashlib.md5()
		hash_object.update(f"{time_string}_{json_string}".encode('utf-8'))
		hash_string = hash_object.hexdigest()
		self.http_client.headers['Api-Time'] = time_string
		self.http_client.headers['Api-Hash'] = hash_string
	
	async def get_dbs(self) -> Dict[str, Any]:
		url = self.api_url + '/dbs'
		try:
			json_data = {'data': {'dbs': ['all']}}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success: return response_json['data']
			else: return {}
		except Exception as error:
			self.errors += 1
			log.error(f"{self.session_name} | Database error: {error}")
			await asyncio.sleep(delay=3)
			return {}

	async def get_profile(self, full: bool) -> Dict[str, Any]:
		url = self.api_url + '/user/data/all' if full else self.api_url + '/hero/balance/sync'
		try:
			json_data = {'data': {}} if full else {}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			return response_json
		except Exception as error:
			self.errors += 1
			log.error(f"{self.session_name} | Profile data error: {error}")
			await asyncio.sleep(delay=3)
			return {}

	async def get_offline_bonus(self) -> bool:
		url = self.api_url + '/hero/bonus/offline/claim'
		try:
			json_data = {}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success:
				self.errors = 0
				self.balance = int(response_json['data']['hero']['money'])
				self.level = int(response_json['data']['hero']['level'])
				self.mph = int(response_json['data']['hero']['moneyPerHour'])
				return True
			else: return False
		except Exception as error:
			self.errors += 1
			log.error(f"{self.session_name} | Offline bonus error: {error}")
			await asyncio.sleep(delay=3)
			return False

	async def daily_reward(self, index: int) -> bool:
		url = self.api_url + '/quests/daily/claim'
		try:
			json_data = {'data': f"{index}"}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success:
				self.errors = 0
				self.balance = int(response_json['data']['hero']['money'])
				self.level = int(response_json['data']['hero']['level'])
				self.mph = int(response_json['data']['hero']['moneyPerHour'])
				return True
			else: return False
		except Exception as error:
			log.error(f"{self.session_name} | Daily reward error: {str(error)}")
			return False
			
	async def quest_reward(self, quest: str, code:str = None) -> bool:
		url = self.api_url + '/quests/claim'
		try:
			json_data = {'data': [quest, code]}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success:
				self.errors = 0
				self.balance = int(response_json['data']['hero']['money'])
				self.level = int(response_json['data']['hero']['level'])
				self.mph = int(response_json['data']['hero']['moneyPerHour'])
				return True
			else: return False
		except Exception as error:
			log.error(f"{self.session_name} | Quest reward error: {str(error)}")
			return False
	
	async def daily_quest_reward(self, quest: str, code:str = None) -> bool:
		url = self.api_url + '/quests/daily/progress/claim'
		try:
			json_data = {'data': {'quest': quest, 'code': code}}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success:
				self.errors = 0
				self.balance = int(response_json['data']['hero']['money'])
				self.level = int(response_json['data']['hero']['level'])
				self.mph = int(response_json['data']['hero']['moneyPerHour'])
				return True
			else: return False
		except Exception as error:
			log.error(f"{self.session_name} | Daily quest reward error: {str(error)}")
			return False
	
	async def daily_quests(self) -> None:
		url = self.api_url + '/quests/daily/progress/all'
		try:
			json_data = {}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success:
				for name, quest in response_json['data'].items():
					if 'youtube' in name: continue
					if 'quiz' in name:
						if quest['isRewarded'] == False:
							self.need_quiz = True
						continue
					if quest['isComplete'] == True and quest['isRewarded'] == False:
						if await self.daily_quest_reward(quest=name):
							log.success(f"{self.session_name} | Reward for daily quest {name} claimed")
		except Exception as error:
			log.error(f"{self.session_name} | Daily quests error: {str(error)}")
			return False
	
	async def solve_rebus(self, quest: str, code:str) -> bool:
		url = self.api_url + '/quests/check'
		try:
			json_data = {'data': [quest, code]}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			if response_json.get('success', False) and response_json['data'].get('result', False):
				await asyncio.sleep(delay=2)
				if await self.quest_reward(quest=quest, code=code):
					return True
			return False
		except Exception as error:
			log.error(f"{self.session_name} | Rebus error: {str(error)}")
			return False
	
	async def friend_reward(self, friend: int) -> bool:
		url = self.api_url + '/friends/claim'
		try:
			json_data = {'data': friend}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success:
				self.errors = 0
				self.balance = int(response_json['data']['hero']['money'])
				self.level = int(response_json['data']['hero']['level'])
				self.mph = int(response_json['data']['hero']['moneyPerHour'])
				return True
			else: return False
		except Exception as error:
			log.error(f"{self.session_name} | Friend reward error: {str(error)}")
			return False
	
	async def perform_taps(self, per_tap: int, energy: int) -> None:
		url = self.api_url + '/hero/action/tap'
		log.info(f"{self.session_name} | Taps started")
		while True:
			taps_per_second = random.randint(*config.TAPS_PER_SECOND)
			seconds = random.randint(4, 6)
			earned_money = per_tap * taps_per_second * seconds
			energy_spent = math.ceil(earned_money / 2)
			energy -= energy_spent
			if energy < 0:
				log.info(f"{self.session_name} | Taps stopped (not enough energy)")
				break
			await asyncio.sleep(delay=seconds)
			try:
				json_data = {'data': {'data':{'task': {'amount': earned_money, 'currentEnergy': energy}}, 'seconds': seconds}}
				await self.set_sign_headers(data=json_data)
				response = await self.http_client.post(url, json=json_data)
				response.raise_for_status()
				response_json = await response.json()
				success = response_json.get('success', False)
				if success:
					self.errors = 0
					self.balance = int(response_json['data']['hero']['money'])
					self.level = int(response_json['data']['hero']['level'])
					self.mph = int(response_json['data']['hero']['moneyPerHour'])
					energy = int(response_json['data']['hero']['earns']['task']['energy'])
					log.success(f"{self.session_name} | Earned money: +{earned_money} | Energy left: {energy}")
			except Exception as error:
				log.error(f"{self.session_name} | Taps error: {str(error)}")
				self.errors += 1
				break

	async def perform_pvp(self, league: Dict[str, Any], strategy: str, count: int) -> None:
		url_info = self.api_url + '/pvp/info'
		url_fight = self.api_url + '/pvp/fight'
		url_claim = self.api_url + '/pvp/claim'
		log.info(f"{self.session_name} | PvP negotiations started | League: {league['key']} | Strategy: {strategy}")
		json_data = {}
		await self.set_sign_headers(data=json_data)
		await self.http_client.post(url_info, json=json_data)
		await asyncio.sleep(3)
		curent_strategy = strategy
		money = 0
		while count > 0:
			if self.balance < int(league['maxContract']):
				money_str = f"Profit: +{money}" if money > 0 else (f"Loss: {money}" if money < 0 else "Profit: 0")
				log.info(f"{self.session_name} | PvP negotiations stopped (not enough money). {money_str}")
				break
			
			if strategy == 'random': curent_strategy = random.choice(self.strategies)
			log.info(f"{self.session_name} | Searching opponent...")
			try:
				json_data = {'data': {'league': league['key'], 'strategy': curent_strategy}}
				await self.set_sign_headers(data=json_data)
				response = await self.http_client.post(url_fight, json=json_data)
				response.raise_for_status()
				response_json = await response.json()
				success = response_json.get('success', False)
				if success:
					self.errors = 0
					if response_json['data']['opponent'] is None:
						await asyncio.sleep(random.randint(5, 10))
						continue
					
					await asyncio.sleep(random.randint(6, 7))
					count -= 1
					if int(response_json['data']['fight']['player1']) == self.user_id:
						opponent_strategy = response_json['data']['fight']['player2Strategy']
					else:
						opponent_strategy = response_json['data']['fight']['player1Strategy']
					money_contract = response_json['data']['fight']['moneyContract']
					money_profit = response_json['data']['fight']['moneyContract']
					winner = int(response_json['data']['fight']['winner'])
					if winner == self.user_id:
						money += money_profit
						log.success(f"{self.session_name} | Contract sum: {money_contract} | "
									f"Your strategy: {curent_strategy} | "
									f"Opponent strategy: {opponent_strategy} | "
									f"You WIN (+{money_profit})")
					else:
						money -= money_contract
						log.success(f"{self.session_name} | Contract sum: {money_contract} | "
									f"Your strategy: {curent_strategy} | "
									f"Opponent strategy: {opponent_strategy} | "
									f"You LOSE (-{money_contract})")
					
					json_data = {}
					await self.set_sign_headers(data=json_data)
					response = await self.http_client.post(url_claim, json=json_data)
					response.raise_for_status()
					response_json = await response.json()
					success = response_json.get('success', False)
					if success:
						self.errors = 0
						self.balance = int(response_json['data']['hero']['money'])
						self.level = int(response_json['data']['hero']['level'])
						self.mph = int(response_json['data']['hero']['moneyPerHour'])
					
					await asyncio.sleep(random.randint(1, 2))
			
			except Exception as error:
				log.error(f"{self.session_name} | PvP error: {str(error)}")
				self.errors += 1
				await asyncio.sleep(random.randint(10, 30))
		money_str = f"Profit: +{money}" if money > 0 else (f"Loss: {money}" if money < 0 else "Profit: 0")
		log.info(f"{self.session_name} | PvP negotiations finished. {money_str}")

	async def get_helper(self) -> Dict[str, Any]:
		url = 'https://alexell.ru/crypto/musk-empire/data.json'
		response = await self.http_client.get(url)
		if response.status == 200:
			response_json = await response.json()
			return response_json
		else: return {}

	async def get_funds_info(self) -> Dict[str, Any]:
		url = self.api_url + '/fund/info'
		try:
			json_data = {}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			return response_json['data']
		except Exception as error:
			self.errors += 1
			log.error(f"{self.session_name} | Funds error: {error}")
			await asyncio.sleep(delay=3)
			return {}

	def calculate_bet(self) -> int:
		bet_steps_count = 7 # from game js, may be changed in the future
		def smart_zero_round(amount):
			def round_to_nearest(value, base=100):
				return round(value / base) * base

			if amount < 100:
				return round_to_nearest(amount, 50)
			elif amount < 1000:
				return round_to_nearest(amount, 100)
			elif amount < 10000:
				return round_to_nearest(amount, 1000)
			elif amount < 100000:
				return round_to_nearest(amount, 10000)
			elif amount < 1000000:
				return round_to_nearest(amount, 100000)
			elif amount < 10000000:
				return round_to_nearest(amount, 1000000)
			elif amount < 100000000:
				return round_to_nearest(amount, 10000000)
			else:
				return round_to_nearest(amount, 1000)

		def min_bet():
			multiplier = 2
			if self.level < 3:
				multiplier = 5
			elif self.level < 6:
				multiplier = 4
			elif self.level < 10:
				multiplier = 3

			calculated_bet = smart_zero_round(self.mph * multiplier / (bet_steps_count * 3))
			return calculated_bet or 100

		def max_bet():
			return min_bet() * bet_steps_count
		
		avail_bet = 0
		max_bet = max_bet()
		if max_bet < self.balance:
			avail_bet = max_bet
		else: # reduce the bet if there is not enough money
			min_bet = min_bet()
			while max_bet > self.balance and max_bet - min_bet >= min_bet:
				max_bet -= min_bet
			avail_bet = max(max_bet, min_bet)
		
		return avail_bet
	
	async def invest(self, fund: str, amount: int) -> None:
		url = self.api_url + '/fund/invest'
		if self.balance < amount:
			log.info(f"{self.session_name} | Not enough money for invest")
			return
		try:
			json_data = {'data': {'fund': fund, 'money': amount}}
			await self.set_sign_headers(data=json_data)
			response = await self.http_client.post(url, json=json_data)
			response.raise_for_status()
			response_json = await response.json()
			success = response_json.get('success', False)
			if success:
				self.errors = 0
				self.balance = int(response_json['data']['hero']['money'])
				self.level = int(response_json['data']['hero']['level'])
				self.mph = int(response_json['data']['hero']['moneyPerHour'])
				for fnd in response_json['data']['funds']:
					if fnd['fundKey'] == fund:
						money = fnd['moneyProfit']
						money_str = f"Profit: +{money}" if money > 0 else (f"Loss: {money}" if money < 0 else "Profit: 0")
						log.success(f"{self.session_name} | Invest completed. {money_str}")
						break
		except Exception as error:
			self.errors += 1
			log.error(f"{self.session_name} | Invest error: {str(error)}")

	async def check_proxy(self, proxy: Proxy) -> None:
		try:
			response = await self.http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
			ip = (await response.json()).get('origin')
			log.info(f"{self.session_name} | Proxy IP: {ip}")
		except Exception as error:
			log.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

	async def run(self, proxy: str | None) -> None:
		proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

		async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
			self.http_client = http_client
			if proxy:
				await self.check_proxy(proxy=proxy)

			self.authorized = False
			gmt_timezone = ZoneInfo('GMT')
			while True:
				if self.errors >= config.ERRORS_BEFORE_STOP:
					log.error(f"{self.session_name} | Bot stopped (too many errors)")
					break
				try:
					if not self.authorized:
						login_data = await self.get_tg_web_data(proxy=proxy)
						if await self.login(json_data=login_data):
							log.success(f"{self.session_name} | Login successful")
							self.authorized = True
							self.http_client.headers['Api-Key'] = self.api_key
							self.dbs = await self.get_dbs()
							full_profile = await self.get_profile(full=True)
							if self.user_id is None: self.user_id = int(full_profile['data']['profile']['id'])
							self.balance = int(full_profile['data']['hero']['money'])
							self.level = int(full_profile['data']['hero']['level'])
							self.mph = int(full_profile['data']['hero']['moneyPerHour'])
							offline_bonus = int(full_profile['data']['hero']['offlineBonus'])
							if offline_bonus > 0:
								if await self.get_offline_bonus():
									log.success(f"{self.session_name} | Offline bonus claimed: +{offline_bonus}")
							else:
								log.info(f"{self.session_name} | Offline bonus not available")
						else: continue
						
					profile = await self.get_profile(full=False)
					self.balance = int(profile['data']['hero']['money'])
					self.level = int(profile['data']['hero']['level'])
					self.mph = int(profile['data']['hero']['moneyPerHour'])
					log.info(f"{self.session_name} | Level: {self.level} | "
								f"Balance: {self.balance} | "
								f"Money per hour: {self.mph}")
					
					daily_rewards = full_profile['data']['dailyRewards']
					daily_index = None
					for day, status in daily_rewards.items():
						if status == 'canTake':
							daily_index = day
							break
					if daily_index is not None:
						log.info(f"{self.session_name} | Daily reward available")
						daily_claimed = await self.daily_reward(index=daily_index)
						if daily_claimed:
							log.success(f"{self.session_name} | Daily reward claimed")
							self.errors = 0
					else:
						log.info(f"{self.session_name} | Daily reward not available")
					
					unrewarded_quests = [quest['key'] for quest in full_profile['data']['quests'] if not quest['isRewarded']]
					if unrewarded_quests:
						log.info(f"{self.session_name} | Quest rewards available")
						for quest in unrewarded_quests:
							if await self.quest_reward(quest=quest):
								log.success(f"{self.session_name} | Reward for quest {quest} claimed")
					
					await self.daily_quests()
					
					unrewarded_friends = [int(friend['id']) for friend in full_profile['data']['friends'] if friend['bonusToTake'] > 0]
					if unrewarded_friends:
						log.info(f"{self.session_name} | Reward for friends available")
						for friend in unrewarded_friends:
							if await self.friend_reward(friend=friend):
								log.success(f"{self.session_name} | Reward for friend {friend} claimed")
					
					if config.TAPS_ENABLED:
						per_tap = profile['data']['hero']['earns']['task']['moneyPerTap']
						max_energy = profile['data']['hero']['earns']['task']['limit']
						energy = profile['data']['hero']['earns']['task']['energy']
						if energy == max_energy:
							await self.perform_taps(per_tap=per_tap, energy=energy)
					
					if config.PVP_ENABLED:
						if self.dbs:
							league_data = None
							for league in self.dbs['dbNegotiationsLeague']:
								if league['key'] == config.PVP_LEAGUE:
									league_data = league
									break;

							if league_data is not None:
								if self.level >= int(league_data['requiredLevel']):
									self.strategies = [strategy['key'] for strategy in self.dbs['dbNegotiationsStrategy']]
									if config.PVP_STRATEGY == 'random' or config.PVP_STRATEGY in self.strategies:
										await self.perform_pvp(league=league_data, strategy=config.PVP_STRATEGY, count=config.PVP_COUNT)
									else:
										config.PVP_ENABLED = False
										log.warning(f"{self.session_name} | PVP_STRATEGY param is invalid. PvP negotiations disabled.")
								else:
									config.PVP_ENABLED = False
									log.warning(f"{self.session_name} | Your level is too low for the {config.PVP_LEAGUE} league. PvP negotiations disabled.")
							else:
								config.PVP_ENABLED = False
								log.warning(f"{self.session_name} | PVP_LEAGUE param is invalid. PvP negotiations disabled.")
						else:
							log.warning(f"{self.session_name} | Database is missing. PvP negotiations will be skipped this time.")
					
					# Daily quiz, rebus and combo invest with external data
					for quest in self.dbs['dbQuests']:
						if 'rebus' in quest['key']:
							self.rebus_key = quest['key']
							self.rebus_answer = quest['checkData']
							break
					self.need_rebus = True
					for quest in full_profile['data']['quests']:
						if self.rebus_key in quest['key']:
							self.need_rebus = False
							break
					
					helper = await self.get_helper()
					cur_time_gmt = datetime.now(gmt_timezone)
					cur_time_gmt_s = cur_time_gmt.strftime('%Y-%m-%d')
					new_day_gmt = cur_time_gmt.replace(hour=7, minute=0, second=0, microsecond=0)
					if cur_time_gmt >= new_day_gmt and cur_time_gmt_s in helper:
						helper = helper[cur_time_gmt_s]
						if 'quiz' in helper and self.need_quiz:
							if await self.daily_quest_reward(quest='quiz', code=helper['quiz']):
								self.need_quiz = False
								log.success(f"{self.session_name} | Reward for daily quiz claimed")
						if self.need_rebus:
							if await self.solve_rebus(quest=self.rebus_key, code=self.rebus_answer):
								self.need_rebus = False
								log.success(f"{self.session_name} | Reward for daily rebus claimed")
						if 'funds' in helper:
							current_invest = await self.get_funds_info()
							if 'funds' in current_invest and not current_invest['funds']:
								for fund in helper['funds']:
									await self.invest(fund=fund, amount=self.calculate_bet())
					
					profile = await self.get_profile(full=False)
					self.balance = int(profile['data']['hero']['money'])
					self.level = int(profile['data']['hero']['level'])
					self.mph = int(profile['data']['hero']['moneyPerHour'])
					log.info(f"{self.session_name} | Level: {self.level} | "
								f"Balance: {self.balance} | "
								f"Money per hour: {self.mph}")
					
					log.info(f"{self.session_name} | Sleep 1 hour")
					await asyncio.sleep(3600)
					self.authorized = False
					
				except RuntimeError as error:
					raise error
				except Exception as error:
					log.error(f"{self.session_name} | Unknown error: {error}")
					await asyncio.sleep(delay=3)

async def run_bot(tg_client: Client, proxy: str | None):
	try:
		await CryptoBot(tg_client=tg_client).run(proxy=proxy)
	except RuntimeError as error:
		log.error(f"{tg_client.name} | Session error: {str(error)}")
