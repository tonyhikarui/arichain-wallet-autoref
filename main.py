import requests
import random
import time
import string
import gc
from colorama import Fore, Style, init
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

init()

ANDROID_USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36', 
    'Mozilla/5.0 (Linux; Android 13; SM-A346B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-A236B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; M2101K6G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; moto g(30)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; CPH2211) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; V2169) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; OnePlus 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Redmi Note 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; POCO X3 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Nothing Phone 1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Nord 2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Xperia 1 IV) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Edge 30 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Zenfone 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
]

def retry_with_backoff(func, retries=5, backoff=2):
    """Retry decorator with exponential backoff"""
    def wrapper(*args, **kwargs):
        retry_count = 0
        while retry_count < retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retry_count += 1
                if retry_count == retries:
                    raise
                sleep_time = (backoff * 2 ** retry_count) + random.uniform(0, 1)
                log(f"Attempt {retry_count} failed, retrying in {sleep_time:.1f}s: {str(e)}", Fore.YELLOW)
                time.sleep(sleep_time)
    return wrapper

class TempMailClient:
    def __init__(self, proxy_dict=None):
        self.base_url = "https://smailpro.com/app"
        self.inbox_url = "https://app.sonjj.com/v1/temp_gmail"
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': random.choice(ANDROID_USER_AGENTS),
            'origin': 'https://smailpro.com',
            'referer': 'https://smailpro.com/'
        }
        self.proxy_dict = proxy_dict
        self.email_address = None
        self.key = None
        self.payload = None
        # Add session for connection pooling
        self.session = requests.Session()
        self.timeout = (30, 60)  # Increase timeout (connect, read)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'session'):
            self.session.close()
        
    def __del__(self):
        # Cleanup resources
        if hasattr(self, 'session'):
            self.session.close()
            
    def create_email(self) -> dict:
        url = f"{self.base_url}/create"
        params = {
            'username': 'random',
            'type': 'alias',
            'domain': 'gmail.com',
            'server': '1'
        }
        
        try:
            response = self.session.get(url, params=params, headers=self.headers, proxies=self.proxy_dict)
            data = response.json()
            self.email_address = data['address']
            self.key = data['key']
            return data
        finally:
            # Ensure response body is read and closed
            if 'response' in locals():
                response.close()

    def create_inbox(self) -> dict:
        url = f"{self.base_url}/inbox"
        payload = [{
            "address": self.email_address,
            "timestamp": int(time.time()),
            "key": self.key
        }]
        
        try:
            response = self.session.post(url, json=payload, headers=self.headers, proxies=self.proxy_dict)
            data = response.json()
            if data:
                self.payload = data[0]['payload']
            return data[0]
        finally:
            if 'response' in locals():
                response.close()

    @retry_with_backoff
    def get_inbox(self) -> dict:
        url = f"{self.inbox_url}/inbox"
        params = {'payload': self.payload}
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                headers=self.headers, 
                proxies=self.proxy_dict, 
                timeout=self.timeout
            )
            response.raise_for_status()
            if not response.text:
                return {"messages": []}
            try:
                return response.json()
            except ValueError:
                log(f"Invalid JSON response: {response.text[:100]}", Fore.RED)
                return {"messages": []}
        except requests.RequestException as e:
            log(f"Inbox error: {e}", Fore.RED)
            return {"messages": []}
        finally:
            if 'response' in locals():
                response.close()

    def process_inbox(self, max_retries=3, wait_time=5):
        """Process inbox with retries and waiting"""
        for attempt in range(max_retries):
            try:
                inbox = self.get_inbox()
                if inbox.get('messages'):
                    message = inbox['messages'][0]
                    token = self.get_message_token(message['mid'])
                    if not token:
                        continue
                    content = self.get_message_content(token)
                    if not content:
                        continue
                    otp = self.extract_otp(content['body'])
                    if otp:
                        return otp
            except Exception as e:
                log(f"Inbox processing error: {e}", Fore.RED)
            
            if attempt < max_retries - 1:
                time.sleep(wait_time)
        return None

    @retry_with_backoff
    def get_message_token(self, mid: str) -> str:
        url = f"{self.base_url}/message"
        params = {
            'email': self.email_address,
            'mid': mid
        }
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                headers=self.headers, 
                proxies=self.proxy_dict,
                timeout=(10, 30)
            )
            response.raise_for_status()
            return response.text
        finally:
            if 'response' in locals():
                response.close()

    @retry_with_backoff
    def get_message_content(self, token: str) -> dict:
        url = f"{self.inbox_url}/message"
        params = {'payload': token}
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                headers=self.headers, 
                proxies=self.proxy_dict,
                timeout=(10, 30)
            )
            response.raise_for_status()
            if not response.text:
                return {"body": ""}
            return response.json()
        finally:
            if 'response' in locals():
                response.close()

    def extract_otp(self, html_content: str) -> str:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            otp_element = soup.find('b', style=lambda value: value and 'letter-spacing:16px' in value)
            if otp_element:
                return otp_element.text.strip()
            return None
        except Exception as e:
            log(f"Error extracting OTP: {e}", Fore.RED)
            return None

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Add thread-safe printing
print_lock = Lock()

def log(message, color=Fore.WHITE, current=None, total=None):
    with print_lock:
        timestamp = f"[{Fore.LIGHTBLACK_EX}{get_timestamp()}{Style.RESET_ALL}]"
        progress = f"[{Fore.LIGHTBLACK_EX}{current}/{total}{Style.RESET_ALL}]" if current is not None and total is not None else ""
        print(f"{timestamp} {progress} {color}{message}{Style.RESET_ALL}")

def ask(message):
    return input(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def format_proxy(proxy):
    if not proxy.startswith('http://') and not proxy.startswith('https://'):
        return f"http://{proxy}"
    return proxy

def load_proxies():
    try:
        with open("proxies.txt", "r") as file:
            proxies = [format_proxy(line.strip()) for line in file if line.strip()]
        print(f"{Fore.GREEN}\nLoaded {len(proxies)} proxies{Style.RESET_ALL}")
        return proxies
    except FileNotFoundError:
        print(f"{Fore.RED}\nFile proxies.txt not found{Style.RESET_ALL}")
        return []

def get_random_proxy(proxies):
    return random.choice(proxies) if proxies else None

def generate_password():
    word = ''.join(random.choices(string.ascii_letters, k=5))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{word.capitalize()}@{numbers}#"

def send_otp(email, proxy_dict, headers, current=None, total=None):
    url = "https://arichain.io/api/email/send_valid_email"
    payload = {
        'blockchain': "testnet",
        'email': email,
        'lang': "en",
        'device': "app",
        'is_mobile': "Y"
    }
    
    with requests.Session() as session:
        try:
            response = session.post(
                url, 
                data=payload, 
                headers=headers, 
                proxies=proxy_dict,
                timeout=(10, 30)  # (connect timeout, read timeout)
            )
            response.raise_for_status()
            log(f"OTP code sent to {email}", Fore.YELLOW, current, total)
            return True
        except requests.Timeout:
            log(f"Timeout sending OTP to {email}", Fore.RED, current, total)
            return False
        except requests.RequestException as e:
            log(f"Failed to send OTP: {e}", Fore.RED, current, total)
            return False
        finally:
            if 'response' in locals():
                response.close()

def verify_otp(email, valid_code, password, proxy_dict, invite_code, headers, current=None, total=None):
    url = "https://arichain.io/api/account/signup_mobile"
    payload = {
        'blockchain': "testnet",
        'email': email,
        'valid_code': valid_code,
        'pw': password,
        'pw_re': password,
        'invite_code': invite_code,
        'lang': "en",
        'device': "app",
        'is_mobile': "Y"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxy_dict, timeout=120)
        response.raise_for_status()
        result = response.json()
        log(f"Success Register with referral code {invite_code}", Fore.GREEN, current, total)

        with open("accounts.txt", "a") as file:
            file.write(f"ID: {result['result']['session_code']}\nEmail: {email}\nPassword: {password}\nAddress: {result['result']['address']}\nPrivate Key: {result['result']['master_key']}\n")

        return result['result']['address']

    except requests.RequestException as e:
        log(f"Failed to verify OTP: {e}", Fore.RED, current, total)
        return None

def daily_claim(address, proxy_dict, headers, current=None, total=None):
    url = "https://arichain.io/api/event/checkin"
    payload = {
        'blockchain': "testnet",
        'address': address,
        'lang': "en",
        'device': "app",
        'is_mobile': "Y"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxy_dict, timeout=120)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'success':
            log("Success claim Daily", Fore.GREEN, current, total)
            return True
        log("Daily claim failed", Fore.RED, current, total)
        return False
    except requests.exceptions.RequestException as e:
        log(f"Daily claim error: {str(e)}", Fore.RED, current, total)
        return False

def auto_send(email, to_address, password, proxy_dict, headers, current=None, total=None):
    url = "https://arichain.io/api/wallet/transfer_mobile"
    
    payload = {
        'blockchain': "testnet",
        'symbol': "ARI",
        'email': email,
        'to_address': to_address,
        'pw': password,
        'amount': "60",
        'memo': "",
        'valid_code': "",
        'lang': "en",
        'device': "app",
        'is_mobile': "Y"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxy_dict, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") == "success" and result.get("result") == "success":
            log(f"Success sent 60 ARI to {to_address}", Fore.GREEN, current, total)
            return True
        else:
            log(f"Failed to send: {result}", Fore.RED, current, total)
            return False
            
    except requests.RequestException as e:
        log(f"Auto-send failed: {e}", Fore.RED, current, total)
        return False

def print_banner():
    print(Fore.CYAN + """
╔═══════════════════════════════════════════╗
║         Ari Wallet Autoreferral           ║
║       https://github.com/im-hanzou        ║
╚═══════════════════════════════════════════╝
    """ + Style.RESET_ALL)

def get_referral_count():
    while True:
        try:
            count = int(ask('Enter desired number of referrals: '))
            if count > 0:
                return count
            log('Please enter a positive number.', Fore.YELLOW)
        except ValueError:
            log('Please enter a valid number.', Fore.RED)

def get_target_address():
    while True:
        address = "ARW7GNYDyrBRRDavrue4Ld4GMw5zuMv8H1brm57sxTm4ByFtAENwb" #ask('Enter target address for auto-send: ').strip()
        if address:
            return address
        log('Please enter a valid address.', Fore.YELLOW)

def get_referral_code():
    while True:
        code = "678d1bfc5f6df" #ask('Enter your referral code: ').strip()
        if code:
            return code
        log('Please enter a valid referral code.', Fore.YELLOW)

def process_single_referral(index, total_referrals, proxy_dict, target_address, ref_code, headers):
    try:
        print(f"{Fore.CYAN}\nStarting new referral process\n{Style.RESET_ALL}")

        with TempMailClient(proxy_dict) as mail_client:  # Use context manager
            email_data = mail_client.create_email()
            if not email_data:
                log("Failed to create email", Fore.RED, index, total_referrals)
                return False
                
            email = email_data['address']
            password = generate_password()
            log(f"Generated account: {email}:{password}", Fore.CYAN, index, total_referrals)

            if not send_otp(email, proxy_dict, headers, index, total_referrals):
                log("Failed to send OTP.", Fore.RED, index, total_referrals)
                return False

            mail_client.create_inbox()
            valid_code = None
            
            # Replace OTP check loop with new process_inbox method
            for _ in range(12):  # 12 attempts * 5 seconds = 60 seconds total
                valid_code = mail_client.process_inbox()
                if valid_code:
                    log(f"Found OTP: {valid_code}", Fore.GREEN, index, total_referrals)
                    break
                time.sleep(5)

            if not valid_code:
                log("Failed to get OTP code.", Fore.RED, index, total_referrals)
                return False

            address = verify_otp(email, valid_code, password, proxy_dict, ref_code, headers, index, total_referrals)
            if not address:
                log("Failed to verify OTP.", Fore.RED, index, total_referrals)
                return False

            daily_claim(address, proxy_dict, headers, index, total_referrals)
            auto_send(email, target_address, password, proxy_dict, headers, index, total_referrals)
            
            log(f"Referral #{index} completed!", Fore.MAGENTA, index, total_referrals)
            return True
            
    except Exception as e:
        log(f"Error occurred: {str(e)}.", Fore.RED, index, total_referrals)
        return False
    finally:
        # Ensure garbage collection
        gc.collect()

def get_proxy_by_task(proxies, task_index):
    """Get proxy by task index (1-based indexing)"""
    if not proxies:
        return None
    proxy_index = ((task_index - 1) % len(proxies))  # Convert 1-based to 0-based index
    proxy = proxies[proxy_index]
    return {"http": proxy, "https": proxy}

def main():
    print_banner()
    
    ref_code = get_referral_code()
    if not ref_code:
        return

    total_referrals = get_referral_count()
    if not total_referrals:
        return
        
    target_address = get_target_address()
    if not target_address:
        return

    proxies = load_proxies()
    headers = {
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'User-Agent': random.choice(ANDROID_USER_AGENTS)
    }
    
    # Get number of threads
    max_workers = min(32, total_referrals)  # Limit max threads
    thread_count = int(ask(f'Enter number of threads (1-{max_workers}): '))
    thread_count = max(1, min(thread_count, max_workers))
    
    successful_referrals = 0
    futures = []
    
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        for index in range(1, total_referrals + 1):
            proxy_dict = get_proxy_by_task(proxies, index)
            if proxy_dict:
                log(f"Queued task #{index} with proxy: {list(proxy_dict.values())[0]}", 
                    Fore.CYAN, index, total_referrals)
            
            # Submit task to thread pool
            future = executor.submit(
                process_single_referral,
                index, total_referrals, proxy_dict,
                target_address, ref_code, headers
            )
            futures.append(future)
            
        # Process completed tasks
        for future in as_completed(futures):
            try:
                if future.result():
                    successful_referrals += 1
            except Exception as e:
                log(f"Task failed with error: {str(e)}", Fore.RED)
    
    print(f"{Fore.MAGENTA}\nCompleted {successful_referrals}/{total_referrals} successful referrals{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}\nScript terminated by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}\nAn unexpected error occurred: {str(e)}{Style.RESET_ALL}")
    finally:
        print(f"{Fore.CYAN}\nAll Process completed{Style.RESET_ALL}")
